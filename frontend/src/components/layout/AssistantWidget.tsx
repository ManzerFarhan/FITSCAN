"use client";
import { Bot, Lock, MessageCircle, RotateCcw, Send, User, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { LoginToUnlock } from "@/components/layout/LoginToUnlock";
import { SourceBadge } from "@/components/ui/badges";
import { Spinner } from "@/components/ui/misc";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import type { AssistantReply } from "@/lib/types";
import { cn } from "@/lib/utils";

type Msg = { id: string; role: "user" | "assistant"; content: string; reply?: AssistantReply };

const STORE = "fitscan-assistant";
const WELCOME = "Hi! I'm the FITSCAN assistant. Ask me how to use FITSCAN, what a lab test measures, or about your verified report. I give general information only - not a diagnosis or medicine advice.";
const PAGE_SUGGESTIONS: Record<string, string[]> = {
  "/dashboard": ["What do these charts show?", "How do I compare reports?", "What does out of range mean?"],
  "/analysis": ["How do I upload a report?", "Why must I confirm the values?", "When does the AI analysis unlock?"],
  "/tests": ["How do I find a centre near me?", "Do I need to fast before a blood test?", "What does a CBC test measure?"],
  "/history": ["How do I compare reports?", "Can I delete a report?", "How long are guest reports kept?"],
  "/profile": ["Who can see my data?", "How do I delete my account?", "What happens to guest uploads?"],
};
const DEFAULT_SUGGESTIONS = ["How do I upload a report?", "What does a reference range mean?", "Find a lab near me"];

function Widget() {
  const { user } = useAuth();  // log in to unlock: guests see a prompt instead of the chat
  const pathname = usePathname() || "/";
  const docId = useSearchParams().get("doc");
  const reportContext = pathname.startsWith("/analysis") && docId ? docId : null;
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try { const s = sessionStorage.getItem(STORE); if (s) setMsgs(JSON.parse(s) as Msg[]); } catch { /* ignore */ }
  }, []);
  useEffect(() => { try { sessionStorage.setItem(STORE, JSON.stringify(msgs.slice(-40))); } catch { /* ignore */ } }, [msgs]);
  useEffect(() => { if (open && user) { end.current?.scrollIntoView({ block: "end" }); inputRef.current?.focus(); } }, [open, msgs, busy, user]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const ask = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true); setError(null); setQ("");
    const history = msgs.slice(-6).map((m) => ({ role: m.role, content: m.content }));
    setMsgs((m) => [...m, { id: `u-${Date.now()}`, role: "user", content: text }]);
    const send = (document_id: string | null) => api<AssistantReply>("/assistant/chat", {
      method: "POST", json: { question: text, page: pathname, document_id, history },
    });
    try {
      let reply: AssistantReply;
      try { reply = await send(reportContext); } catch (e) {
        if (reportContext && e instanceof ApiError && e.status === 404) reply = await send(null); else throw e;
      }
      setMsgs((m) => [...m, { id: `a-${Date.now()}`, role: "assistant", content: reply.answer, reply }]);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The assistant is unavailable right now. Please try again.");
    } finally { setBusy(false); }
  };

  const suggestions = PAGE_SUGGESTIONS[pathname] ?? DEFAULT_SUGGESTIONS;
  const lastReply = [...msgs].reverse().find((m) => m.reply)?.reply;

  return (
    <>
      {open && (
        <section role="dialog" aria-modal="false" aria-label="FITSCAN assistant"
          className="fixed inset-x-0 bottom-0 z-50 flex h-[85vh] flex-col overflow-hidden rounded-t-2xl border border-slate-200 bg-white shadow-2xl
            sm:inset-x-auto sm:bottom-24 sm:right-6 sm:h-[600px] sm:max-h-[calc(100vh-8rem)] sm:w-[400px] sm:rounded-2xl">
          <header className="flex items-center gap-3 bg-brand-700 px-4 py-3 text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15"><Bot className="h-5 w-5" aria-hidden /></span>
            <div className="min-w-0 flex-1">
              <p className="font-semibold leading-tight">FITSCAN assistant</p>
              <p className="truncate text-xs text-brand-100">{reportContext ? "Can see your verified report on this page" : "Ask about FITSCAN or your lab tests"}</p>
            </div>
            {msgs.length > 0 && (
              <button onClick={() => { setMsgs([]); setError(null); }} aria-label="Start a new chat" title="New chat" className="rounded p-1.5 hover:bg-white/15">
                <RotateCcw className="h-4 w-4" />
              </button>
            )}
            <button onClick={() => setOpen(false)} aria-label="Close assistant" className="rounded p-1.5 hover:bg-white/15"><X className="h-5 w-5" /></button>
          </header>

          {!user ? (
            <div className="flex flex-1 items-center bg-slate-50 p-4">
              <LoginToUnlock feature="the assistant" compact
                description="Ask about FITSCAN, what a lab test measures, or your own verified report - free with an account." />
            </div>
          ) : (<>
          <div className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4" aria-live="polite">
            <Bubble role="assistant" content={WELCOME} />
            {msgs.map((m) => <Bubble key={m.id} role={m.role} content={m.content} reply={m.reply} onNavigate={() => setOpen(false)} />)}
            {busy && <p className="flex items-center gap-2 pl-9 text-sm text-slate-500"><Spinner />Thinking...</p>}
            {error && <p role="alert" className="rounded-lg bg-red-50 p-2 text-sm text-red-700">{error}</p>}
            <div className="flex flex-wrap gap-2 pl-9">
              {(lastReply?.suggestions?.length ? lastReply.suggestions : suggestions).map((s) => (
                <button key={s} onClick={() => ask(s)} disabled={busy}
                  className="rounded-full border border-brand-200 bg-white px-3 py-1 text-xs text-brand-800 hover:bg-brand-50 disabled:opacity-50">{s}</button>
              ))}
            </div>
            <div ref={end} />
          </div>

          <form className="flex gap-2 border-t border-slate-200 bg-white p-3" onSubmit={(e) => { e.preventDefault(); void ask(q); }}>
            <input ref={inputRef} aria-label="Message the assistant" placeholder="Type your question..." value={q} maxLength={1000}
              onChange={(e) => setQ(e.target.value)}
              className="h-10 flex-1 rounded-lg border border-slate-300 px-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100" />
            <button type="submit" disabled={busy || !q.trim()} aria-label="Send"
              className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50">
              <Send className="h-4 w-4" />
            </button>
          </form>
          <p className="bg-white px-3 pb-2 text-center text-[11px] text-slate-400">General information only. Always consult your doctor.</p>
          </>)}
        </section>
      )}

      <button onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label={open ? "Close assistant" : "Talk to the FITSCAN assistant"}
        className={cn("fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full bg-brand-700 px-4 py-3 font-medium text-white shadow-lg",
          "transition hover:bg-brand-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-200 sm:bottom-6 sm:right-6",
          open && "max-sm:hidden")}>
        {open ? <X className="h-5 w-5" aria-hidden /> : <MessageCircle className="h-5 w-5" aria-hidden />}
        <span className="hidden sm:inline">{open ? "Close" : "Talk to assistant"}</span>
        {!open && !user && <Lock className="h-3.5 w-3.5 opacity-80" aria-label="Log in to unlock" />}
      </button>
    </>
  );
}

function Bubble({ role, content, reply, onNavigate }: { role: Msg["role"]; content: string; reply?: AssistantReply; onNavigate?: () => void }) {
  const user = role === "user";
  return (
    <div className={cn("flex gap-2", user && "flex-row-reverse")}>
      <span className={cn("mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full", user ? "bg-slate-200 text-slate-700" : "bg-brand-100 text-brand-800")}>
        {user ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </span>
      <div className={cn("max-w-[85%] rounded-2xl px-3 py-2 text-sm", user ? "rounded-tr-sm bg-brand-700 text-white" : "rounded-tl-sm border border-slate-200 bg-white text-slate-800")}>
        {reply && <div className="mb-1"><SourceBadge tag="AI_GENERATED" /></div>}
        <p className="whitespace-pre-wrap">{content}</p>
        {reply && reply.sources.length > 0 && (
          <ul className="mt-2 space-y-0.5 border-t border-slate-100 pt-1 text-xs">
            {reply.sources.map((s) => (
              <li key={s.chunk_id}><a href={s.url} target="_blank" rel="noreferrer" className="text-brand-700 hover:underline">[S{s.n}] {s.title} - {s.source}</a></li>
            ))}
          </ul>
        )}
        {reply && reply.actions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {reply.actions.map((a) => (
              <Link key={a.href + a.label} href={a.href} onClick={onNavigate}
                className="rounded-md bg-brand-50 px-2 py-1 text-xs font-medium text-brand-800 ring-1 ring-brand-200 hover:bg-brand-100">{a.label} →</Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function AssistantWidget() {
  return <Suspense fallback={null}><Widget /></Suspense>;
}
