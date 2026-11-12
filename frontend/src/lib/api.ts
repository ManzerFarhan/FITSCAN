// Fetch wrapper: base URL, cookies (guest/auth session), uniform error format (BRD §5).
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: Record<string, unknown> = {}) {
    super(message);
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  const body = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const e = body?.error;
    throw new ApiError(res.status, e?.code ?? `HTTP_${res.status}`, e?.message ?? "Something went wrong. Please try again.", e?.details ?? {});
  }
  return body as T;
}

export async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, headers, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      ...rest,
      headers: { ...(json !== undefined ? { "Content-Type": "application/json" } : {}), ...headers },
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch {
    throw new ApiError(0, "NETWORK", "Can't reach the FITSCAN server. Is the backend running?");
  }
  return handle<T>(res);
}

/** Upload with progress (fetch has no upload progress events). */
export function uploadWithProgress<T>(path: string, form: FormData, onProgress: (pct: number) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}${path}`);
    xhr.withCredentials = true;
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100));
    xhr.onerror = () => reject(new ApiError(0, "NETWORK", "Upload failed - check your connection and try again."));
    xhr.onload = () => {
      let body: any = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* non-JSON */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as T);
      else reject(new ApiError(xhr.status, body?.error?.code ?? `HTTP_${xhr.status}`, body?.error?.message ?? "Upload failed.", body?.error?.details ?? {}));
    };
    xhr.send(form);
  });
}

export const fileUrl = (docId: string, download = false) => `${API_BASE}/documents/${docId}/file${download ? "?download=true" : ""}`;
export const pageImageUrl = (docId: string, page: number) => `${API_BASE}/documents/${docId}/pages/${page}.png`;
export const summaryPdfUrl = (docId: string) => `${API_BASE}/documents/${docId}/summary.pdf`;
