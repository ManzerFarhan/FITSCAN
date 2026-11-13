"use client";
import { useEffect } from "react";
import { API_BASE } from "@/lib/api";

/** Free hosting puts the API to sleep when idle. One quiet ping when the site opens starts it waking up,
 *  so it's usually ready by the time someone has picked their report. */
export function WakeServer() {
  useEffect(() => {
    fetch(`${API_BASE}/ping`, { cache: "no-store" }).catch(() => undefined);
  }, []);
  return null;
}
