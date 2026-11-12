"""Object storage (NFR-06). Local filesystem for dev, S3-compatible (MinIO/S3/R2) for prod."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def signed_url(self, key: str, filename: str | None = None) -> str | None:
        """Expiring URL, or None when the API must stream the bytes itself."""
        ...


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise ValueError("invalid storage key")
        return p

    def put(self, key: str, data: bytes, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def signed_url(self, key: str, filename: str | None = None) -> str | None:
        return None


class S3Storage:
    def __init__(self) -> None:
        import boto3

        s = get_settings()
        self.bucket = s.s3_bucket
        self.ttl = s.signed_url_ttl_seconds
        self.client = boto3.client(
            "s3",
            endpoint_url=s.s3_endpoint_url,
            aws_access_key_id=s.s3_access_key,
            aws_secret_access_key=s.s3_secret_key,
        )
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def signed_url(self, key: str, filename: str | None = None) -> str | None:
        params = {"Bucket": self.bucket, "Key": key}
        if filename:
            params["ResponseContentDisposition"] = f'inline; filename="{filename}"'
        return self.client.generate_presigned_url("get_object", Params=params, ExpiresIn=self.ttl)


class DatabaseStorage:
    """Files kept in the database (stored_files). For free hosts with no disk or object store."""

    def put(self, key: str, data: bytes, content_type: str) -> None:
        from app.db.models import StoredFile
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            db.merge(StoredFile(key=key, content_type=content_type, data=data))
            db.commit()

    def get(self, key: str) -> bytes:
        from app.db.models import StoredFile
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            row = db.get(StoredFile, key)
            if row is None:
                raise FileNotFoundError(key)
            return row.data

    def delete(self, key: str) -> None:
        from app.db.models import StoredFile
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            db.query(StoredFile).filter(StoredFile.key == key).delete()
            db.commit()

    def signed_url(self, key: str, filename: str | None = None) -> str | None:
        return None


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        s = get_settings()
        if s.storage_backend == "s3":
            _storage = S3Storage()
        elif s.storage_backend == "db":
            _storage = DatabaseStorage()
        else:
            _storage = LocalStorage(s.local_storage_dir)
    return _storage
