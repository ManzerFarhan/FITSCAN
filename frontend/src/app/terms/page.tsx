import type { Metadata } from "next";
import Link from "next/link";
import { LegalDocument, V, type LegalSection } from "@/components/legal/LegalDocument";
import { DISCLAIMER_TEXT } from "@/lib/constants";
import { SITE } from "@/lib/site";

export const metadata: Metadata = { title: "Terms & Conditions" };

const SUMMARY = [
  "FITSCAN explains your lab reports in plain language. It is not a doctor and does not diagnose, treat or prescribe.",
  "Always check the values FITSCAN reads against your original report, and talk to a qualified doctor about your results.",
  "In an emergency, call 112 (or 108 for an ambulance) - do not rely on an app.",
  "Only upload your own reports, or reports you have permission to upload.",
  "Diagnostic-centre listings come from public map data and are not verified or endorsed by us.",
  "The Service is currently free and provided \"as is\"; these terms limit our liability as far as the law allows.",
];

const SECTIONS: LegalSection[] = [
  {
    id: "acceptance", title: "Acceptance of these terms",
    body: (
      <p>
        These Terms &amp; Conditions (&quot;Terms&quot;) are an agreement between you and <V>{SITE.companyName}</V> (&quot;FITSCAN&quot;,
        &quot;we&quot;, &quot;us&quot;) for your use of the FITSCAN website and services (the &quot;Service&quot;). By using the Service as a guest or
        by creating an account, you agree to these Terms and to our <Link href="/privacy">Privacy Policy</Link>. If you do not agree, please do
        not use the Service.
      </p>
    ),
  },
  {
    id: "medical", title: "Not medical advice",
    body: (
      <>
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-900">{DISCLAIMER_TEXT}</p>
        <ul>
          <li>FITSCAN gives <strong>general information</strong> to help you understand your own lab reports. It is not a medical device and is not a substitute for professional medical advice, diagnosis or treatment.</li>
          <li>Results are compared only with the reference range printed on your report by your lab. A value inside or outside that range does not, by itself, mean you are healthy or unwell.</li>
          <li>Never ignore professional advice, or delay seeking it, because of something you read on FITSCAN. Do not start, stop or change any medicine based on the Service.</li>
          <li><strong>Emergencies:</strong> if you feel very unwell, call your local emergency number (112 in India, 108 for an ambulance) or go to the nearest emergency department.</li>
        </ul>
      </>
    ),
  },
  {
    id: "service", title: "What the Service does",
    body: (
      <>
        <p>FITSCAN lets you upload printed lab reports; reads the test names, values, units and reference ranges; lets you check and correct them; explains the values you confirm; compares reports over time; shows charts; and helps you find diagnostic centres.</p>
        <p>Handwritten documents are not supported. Features may change, and some (such as AI explanations or enhanced map search) may be unavailable at times.</p>
      </>
    ),
  },
  {
    id: "eligibility", title: "Eligibility and accounts",
    body: (
      <ul>
        <li>You must be at least 18 years old and able to enter into a binding contract under Indian law. A parent or legal guardian may use the Service for their child&apos;s reports as the account holder.</li>
        <li>You can use FITSCAN as a guest - guest data is deleted after {SITE.guestRetentionHours} hours - or create an account to keep your history.</li>
        <li>Keep your password confidential and tell us promptly at <a href={`mailto:${SITE.supportEmail}`}><V>{SITE.supportEmail}</V></a> if you think your account has been misused. You are responsible for activity under your account.</li>
        <li>The information you give us must be accurate.</li>
      </ul>
    ),
  },
  {
    id: "content", title: "Your reports and content",
    body: (
      <>
        <p>
          You keep ownership of the reports and information you upload (&quot;Your Content&quot;). You give us a limited, non-exclusive,
          royalty-free permission to store, process and display Your Content <strong>only to provide the Service to you</strong>, as described
          in our <Link href="/privacy">Privacy Policy</Link>. This permission ends when you delete Your Content, except for copies we must keep by law.
        </p>
        <p>
          You confirm that you have the right to upload each report - it is your own, or you have the permission of the person it belongs to
          (or are their parent or legal guardian).
        </p>
      </>
    ),
  },
  {
    id: "accuracy", title: "Accuracy and your checks",
    body: (
      <>
        <p>
          Reading documents automatically is not perfect. Values, units, ranges or names may be misread, especially on photos and scans.
          FITSCAN highlights values it is unsure about, and explanations are based only on values you have confirmed.
        </p>
        <p>
          If you use <strong>Auto-check &amp; confirm</strong>, FITSCAN accepts values that pass its automated checks and leaves the rest out of
          the analysis. Automated checks cannot catch every error, so you remain responsible for comparing the values with your original report.
        </p>
      </>
    ),
  },
  {
    id: "ai", title: "AI-generated content",
    body: (
      <p>
        Some explanations and assistant answers are produced with the help of artificial intelligence and are labelled &quot;AI-generated&quot;. They
        are checked against safety rules and, where possible, cite their sources, but may still be incomplete or wrong. They are general
        information only and must not be relied on as medical advice.
      </p>
    ),
  },
  {
    id: "third-party", title: "Diagnostic centres and third-party services",
    body: (
      <>
        <p>
          Centre listings, distances, phone numbers, ratings and opening hours come from third-party map data (such as OpenStreetMap or Google
          Maps). We do not verify, endorse or partner with any listed centre, and we do not guarantee that a centre offers a particular test, its
          prices, timings or quality. Please confirm directly with the centre before visiting.
        </p>
        <p>Links to other websites are for convenience; their own terms and policies apply, and we are not responsible for their content.</p>
      </>
    ),
  },
  {
    id: "use", title: "Acceptable use",
    body: (
      <>
        <p>You agree not to:</p>
        <ul>
          <li>upload reports belonging to someone else without their permission, or content that is unlawful, fake or misleading;</li>
          <li>try to access other users&apos; data, probe or break our security, or bypass rate limits;</li>
          <li>upload viruses or harmful code, or overload or disrupt the Service;</li>
          <li>scrape, copy or resell the Service or its content, or use it to build a competing product;</li>
          <li>use the Service to give medical advice to others or present its output as a doctor&apos;s opinion.</li>
        </ul>
        <p>We may suspend or remove access, and remove content, if these Terms are breached.</p>
      </>
    ),
  },
  {
    id: "ip", title: "Our intellectual property",
    body: (
      <p>
        The Service - including its software, design, text, test dictionary, glossary and logo - belongs to FITSCAN or its licensors and is
        protected by law. Health information summarised from public sources (such as MedlinePlus, NIH and NHS) is credited to those sources.
        You may use the Service for your personal, non-commercial purposes only.
      </p>
    ),
  },
  {
    id: "fees", title: "Fees",
    body: <p>The Service is currently free. If we introduce paid features, we will show the price clearly and ask for your agreement before you are charged.</p>,
  },
  {
    id: "termination", title: "Suspension and termination",
    body: (
      <p>
        You can stop using the Service and delete your account at any time from Profile. We may suspend or end your access if you breach these
        Terms, if required by law, or if we discontinue the Service, giving reasonable notice where possible so you can download your summaries.
        Sections that by their nature should continue (such as 13-16) survive termination.
      </p>
    ),
  },
  {
    id: "disclaimer", title: "Disclaimer of warranties",
    body: (
      <p>
        To the fullest extent permitted by law, the Service is provided &quot;as is&quot; and &quot;as available&quot;, without warranties of any kind,
        whether express or implied, including warranties of accuracy, fitness for a particular purpose, or uninterrupted availability.
      </p>
    ),
  },
  {
    id: "liability", title: "Limitation of liability",
    body: (
      <>
        <p>
          To the fullest extent permitted by law, FITSCAN is not liable for any indirect, incidental, special or consequential loss, or for any
          decision you make or action you take based on the Service. Our total liability for any claim relating to the Service is limited to
          the greater of the amount you paid us in the 12 months before the claim or <V>[INR 1,000]</V>.
        </p>
        <p>Nothing in these Terms limits liability that cannot be limited under applicable law.</p>
      </>
    ),
  },
  {
    id: "indemnity", title: "Indemnity",
    body: (
      <p>
        You agree to compensate FITSCAN for reasonable losses and costs arising from your breach of these Terms or your upload of content you did
        not have the right to upload.
      </p>
    ),
  },
  {
    id: "law", title: "Governing law and disputes",
    body: (
      <p>
        These Terms are governed by the laws of India. We encourage you to contact our Grievance Officer first so we can try to resolve any
        concern informally. Otherwise, the courts at <V>{SITE.jurisdictionCity}</V>, India, have exclusive jurisdiction, subject to any
        consumer-protection rights you have under the law.
      </p>
    ),
  },
  {
    id: "changes", title: "Changes to these terms",
    body: (
      <p>
        We may update these Terms from time to time. We will change the effective date at the top and, for significant changes, notify account
        holders before they take effect. Continuing to use the Service after that means you accept the updated Terms.
      </p>
    ),
  },
  {
    id: "general", title: "General",
    body: (
      <p>
        If any part of these Terms is found unenforceable, the rest remains in effect. Our failure to enforce a provision is not a waiver. These
        Terms and the Privacy Policy are the entire agreement between you and us about the Service.
      </p>
    ),
  },
  {
    id: "contact", title: "Contact and grievances",
    body: (
      <ul>
        <li>Support: <a href={`mailto:${SITE.supportEmail}`}><V>{SITE.supportEmail}</V></a></li>
        <li>Grievance Officer: <V>{SITE.grievanceOfficer}</V> - <a href={`mailto:${SITE.grievanceEmail}`}><V>{SITE.grievanceEmail}</V></a></li>
        <li>Postal address: <V>{SITE.companyName}</V>, <V>{SITE.companyAddress}</V></li>
      </ul>
    ),
  },
];

export default function TermsPage() {
  return (
    <LegalDocument title="Terms & Conditions" effective={SITE.termsEffectiveDate} summary={SUMMARY} sections={SECTIONS}
      other={{ href: "/privacy", label: "Privacy Policy" }}
      intro={<p>Please read these terms carefully. They explain what FITSCAN is - and is not - and the rules for using it.</p>} />
  );
}
