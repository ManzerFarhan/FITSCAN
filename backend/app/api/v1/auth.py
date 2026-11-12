"""Auth (API-16, FR-PROF-5). JWT in an httpOnly cookie; guest data migrates on login/register."""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AUTH_COOKIE, GUEST_COOKIE, Owner, _cookie_kwargs, get_owner, hash_token, rate_limit
from app.core.config import get_settings
from app.db.models import GuestSession
from app.db.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, ResetConfirmIn, ResetRequestIn, SessionOut, UserOut
from app.services import audit, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _guest(request: Request, db: Session) -> GuestSession | None:
    token = request.cookies.get(GUEST_COOKIE) or request.headers.get("x-guest-token")
    return db.scalar(select(GuestSession).where(GuestSession.token_hash == hash_token(token))) if token else None


def _sign_in(response: Response, request: Request, db: Session, user) -> SessionOut:
    migrated = user_service.migrate_guest(db, _guest(request, db), user)
    s = get_settings()
    response.set_cookie(AUTH_COOKIE, user_service.access_token(user), max_age=s.jwt_expire_minutes * 60, **_cookie_kwargs())
    response.delete_cookie(GUEST_COOKIE, path="/")
    return SessionOut(authenticated=True, user=UserOut.model_validate(user), migrated_documents=migrated)


@router.post("/register", response_model=SessionOut, status_code=201, dependencies=[Depends(rate_limit("auth", 10))])
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = user_service.register(db, body.email, body.password, body.full_name)
    out = _sign_in(response, request, db, user)
    audit.record(db, Owner(user=user), "REGISTER", "user", user.id, "Account created")
    return out


@router.post("/login", response_model=SessionOut, dependencies=[Depends(rate_limit("auth", 10))])
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = user_service.authenticate(db, body.email, body.password)
    return _sign_in(response, request, db, user)


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE, path="/")
    response.status_code = 204
    return response


@router.get("/me", response_model=SessionOut)
def me(owner: Owner = Depends(get_owner)):
    if owner.user is None:
        return SessionOut(authenticated=False)
    return SessionOut(authenticated=True, user=UserOut.model_validate(owner.user))


@router.post("/reset-password", dependencies=[Depends(rate_limit("reset", 5))])
def request_reset(body: ResetRequestIn, db: Session = Depends(get_db)) -> dict:
    token = user_service.request_reset(db, body.email)
    out = {"message": "If an account exists for this email, a reset link has been sent."}
    # No email service in the prototype: outside production the token is returned so the flow can be tested.
    if token and not get_settings().is_production:
        out["dev_reset_token"] = token
    return out


@router.post("/reset-password/confirm", dependencies=[Depends(rate_limit("reset", 5))])
def confirm_reset(body: ResetConfirmIn, db: Session = Depends(get_db)) -> dict:
    user_service.confirm_reset(db, body.token, body.new_password)
    return {"message": "Your password has been updated. Please log in."}
