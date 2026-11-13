import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { AssistantWidget } from "@/components/layout/AssistantWidget";
import { DisclaimerBanner } from "@/components/layout/DisclaimerBanner";
import { Navbar } from "@/components/layout/Navbar";
import { WakeServer } from "@/components/layout/WakeServer";
import { WelcomeModal } from "@/components/layout/WelcomeModal";
import { AuthProvider } from "@/hooks/useAuth";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: { default: "FITSCAN", template: "%s | FITSCAN" },
  description: "Understand your lab reports in plain language.",
  icons: { icon: "/logo.svg" },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#0f766e" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:p-2">
          Skip to content
        </a>
        <WakeServer />
        <AuthProvider>
          <Navbar />
          <main id="main" className="mx-auto w-full max-w-7xl px-4 py-6">{children}</main>
          <footer className="mx-auto w-full max-w-7xl px-4 pb-24">
            <DisclaimerBanner compact />
            <div className="mt-4 flex flex-col items-center justify-between gap-3 border-t border-slate-200 pt-4 text-xs text-slate-500 sm:flex-row">
              <p>© {new Date().getFullYear()} FITSCAN · Informational only. Not a medical device.</p>
              <nav aria-label="Legal" className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
                <Link href="/privacy" className="font-medium text-slate-600 hover:text-brand-700 hover:underline">Privacy Policy</Link>
                <Link href="/terms" className="font-medium text-slate-600 hover:text-brand-700 hover:underline">Terms &amp; Conditions</Link>
                <Link href="/terms#medical" className="hover:text-brand-700 hover:underline">Medical disclaimer</Link>
              </nav>
            </div>
          </footer>
          <AssistantWidget />
          <WelcomeModal />
        </AuthProvider>
      </body>
    </html>
  );
}
