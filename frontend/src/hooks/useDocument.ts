"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { PROCESSING_TERMINAL } from "@/lib/constants";
import type { DocumentOut, ExtractionOut } from "@/lib/types";

/** Polls API-02 until processing reaches a terminal status, then loads the extraction (API-04). */
export function useDocument(docId: string | null) {
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [extraction, setExtraction] = useState<ExtractionOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadExtraction = useCallback(async (id: string) => {
    const ex = await api<ExtractionOut>(`/documents/${id}/extraction`);
    setExtraction(ex);
    setDoc(ex.document);
  }, []);

  const poll = useCallback(async (id: string, delay = 800) => {
    try {
      const d = await api<DocumentOut>(`/documents/${id}`);
      setDoc(d);
      if (PROCESSING_TERMINAL.includes(d.status)) {
        if (d.status !== "FAILED") await loadExtraction(id);
        return;
      }
      timer.current = setTimeout(() => void poll(id, Math.min(delay * 1.4, 4000)), delay);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the document.");
    }
  }, [loadExtraction]);

  useEffect(() => {
    setDoc(null); setExtraction(null); setError(null);
    if (docId) void poll(docId);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [docId, poll]);

  const restart = useCallback(() => { if (docId) { setExtraction(null); void poll(docId); } }, [docId, poll]);

  return { doc, extraction, setExtraction, error, restart, reload: () => docId && loadExtraction(docId) };
}
