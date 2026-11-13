// Fetch wrapper: base URL, cookies (guest/auth session), uniform error format (BRD §5).
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: Record<string, unknown> = {}) {
    super(message);
  }
}

/** 502/503/504 or no answer: on free hosting this almost always means the API server is asleep and starting up. */
export const SERVER_WAKING = "SERVER_WAKING";
const WAKING_MESSAGE = "The FITSCAN server is starting up (free hosting sleeps when idle). Please wait about a minute and try again.";
const isGatewayStatus = (s: number) => s === 502 || s === 503 || s === 504;

/** Ping the API until it answers (or `maxMs` passes). Returns true once the server is awake. */
export async function wakeServer(maxMs = 120_000): Promise<boolean> {
  const until = Date.now() + maxMs;
  while (Date.now() < until) {
    try {
      const r = await fetch(`${API_BASE}/ping`, { cache: "no-store" });
      if (r.ok) return true;
    } catch { /* still starting */ }
    await new Promise((r) => setTimeout(r, 3000));
  }
  return false;
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  const body = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    if (!body && isGatewayStatus(res.status)) throw new ApiError(res.status, SERVER_WAKING, WAKING_MESSAGE);
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
    xhr.onerror = () => reject(new ApiError(0, SERVER_WAKING, WAKING_MESSAGE));  // no answer: usually a sleeping server
    xhr.onload = () => {
      let body: any = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* non-JSON */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as T);
      else if (!body && isGatewayStatus(xhr.status)) reject(new ApiError(xhr.status, SERVER_WAKING, WAKING_MESSAGE));
      else reject(new ApiError(xhr.status, body?.error?.code ?? `HTTP_${xhr.status}`, body?.error?.message ?? "Upload failed.", body?.error?.details ?? {}));
    };
    xhr.send(form);
  });
}

export const fileUrl = (docId: string, download = false) => `${API_BASE}/documents/${docId}/file${download ? "?download=true" : ""}`;
export const pageImageUrl = (docId: string, page: number) => `${API_BASE}/documents/${docId}/pages/${page}.png`;
export const summaryPdfUrl = (docId: string) => `${API_BASE}/documents/${docId}/summary.pdf`;
