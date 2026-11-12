import type { Metadata } from "next";
import Link from "next/link";
import { LegalDocument, V, type LegalSection } from "@/components/legal/LegalDocument";
import { SITE } from "@/lib/site";

export const metadata: Metadata = { title: "Privacy Policy" };

const SUMMARY = [
  "You upload lab reports so FITSCAN can read and explain them. We use your data only to provide that service.",
  "We never sell your data, show you ads, or use the contents of your reports to train AI models.",
  "When AI explanations are on, the AI only receives your confirmed test values and your lab's ranges - never your name, address or the report file.",
  `Guest uploads are deleted automatically after ${SITE.guestRetentionHours} hours. Account holders can delete any report, or their whole account, at any time.`,
  "We use only essential cookies - no tracking or advertising cookies.",
  "You can ask us to access, correct or erase your data, or raise a complaint with our Grievance Officer.",
];

const SECTIONS: LegalSection[] = [
  {
    id: "about", title: "About this policy",
    body: (
      <>
        <p>
          This Privacy Policy explains how <V>{SITE.companyName}</V> (&quot;FITSCAN&quot;, &quot;we&quot;, &quot;us&quot;) collects, uses, shares and
          protects personal data when you use the FITSCAN website and services (the &quot;Service&quot;). For the purposes of the Digital Personal
          Data Protection Act, 2023 (&quot;DPDP Act&quot;), we are the Data Fiduciary for the personal data described here.
        </p>
        <p>
          Lab reports contain health information, which is treated as sensitive personal data under the Information Technology (Reasonable
          Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011. We handle it with particular care.
        </p>
        <p>By using the Service, or by uploading a report, you consent to the processing described in this policy.</p>
      </>
    ),
  },
  {
    id: "collect", title: "Information we collect",
    body: (
      <>
        <p><strong>Information you give us</strong></p>
        <ul>
          <li><strong>Account details</strong> (if you register): email address and password. Your password is stored only as a secure one-way hash. You may optionally add your name, phone number, date of birth, gender, city and address in your profile.</li>
          <li><strong>Lab reports you upload</strong> (PDF, JPG or PNG) and everything printed on them - which may include your name, age, sex, address, the lab&apos;s details, dates and your test results.</li>
          <li><strong>Your corrections and confirmations</strong> of the values we read, and any values you add by hand.</li>
          <li><strong>Questions you ask</strong> about a report, and the answers, which are saved with that report.</li>
          <li><strong>Centre searches</strong>: the city, area or PIN code you enter and, only if you allow it in your browser, your device location for that search.</li>
        </ul>
        <p><strong>Information collected automatically</strong></p>
        <ul>
          <li><strong>Essential cookies</strong> that keep your guest session or sign-in working (see section 11).</li>
          <li><strong>Technical logs</strong>: IP address, browser type, the pages or features requested and the time, used for security, abuse prevention and fixing problems.</li>
          <li><strong>Activity history</strong> in your account, such as when a report was uploaded, analysed or deleted.</li>
        </ul>
        <p>
          We do not collect payment details, your contacts, background location, or biometric data. Messages you send to the site assistant
          (the chat button at the bottom of each page) are kept in your browser tab only and are not stored on our servers.
        </p>
      </>
    ),
  },
  {
    id: "use", title: "How we use your information",
    body: (
      <>
        <p>We use personal data only for the following purposes:</p>
        <ul>
          <li>To read your report, show you what was read, let you correct it, and explain the values you confirm.</li>
          <li>To keep your history, comparisons, charts and PDF summaries if you have an account.</li>
          <li>To search for diagnostic centres near the location you choose.</li>
          <li>To keep the Service secure, prevent misuse (for example, rate limits) and investigate problems.</li>
          <li>To improve the Service using aggregated, non-identifying information (for example, how often values need correcting). Our accuracy testing uses synthetic reports, not yours.</li>
          <li>To meet legal obligations and respond to lawful requests.</li>
        </ul>
        <p>We do <strong>not</strong> sell or rent personal data, use it for advertising or profiling, or use the contents of your reports to train AI models.</p>
      </>
    ),
  },
  {
    id: "ai", title: "AI-generated explanations",
    body: (
      <>
        <p>
          When AI explanations are enabled, FITSCAN sends an AI service provider only what is needed to write the explanation: the test values
          you have confirmed, their units, your lab&apos;s printed reference ranges, and the report category and date. <strong>We never send your
          name, address, other identifying details, or the report file itself.</strong>
        </p>
        <p>
          Every AI answer is checked by safety rules before you see it and is labelled &quot;AI-generated&quot;. AI explanations are general
          information, not medical advice - see our <Link href="/terms">Terms &amp; Conditions</Link>.
        </p>
      </>
    ),
  },
  {
    id: "share", title: "How we share information",
    body: (
      <>
        <p>We share personal data only in these situations:</p>
        <ul>
          <li><strong>Service providers</strong> who process data on our behalf and under our instructions: cloud hosting and secure file storage; the AI provider (only the data described in section 4, when AI explanations are enabled); and mapping services - Google Maps Platform or OpenStreetMap - which receive the area or location you search, but not your reports.</li>
          <li><strong>Map images</strong> on the centre search page are loaded by your browser directly from OpenStreetMap&apos;s tile servers, which can see your IP address.</li>
          <li><strong>Legal reasons</strong>: where required by law, court order or a lawful request from a government authority, or to protect the rights, safety and security of users or the public.</li>
          <li><strong>Business transfer</strong>: if FITSCAN is merged or acquired, your data may transfer to the new owner, who must respect this policy.</li>
        </ul>
        <p>When you download a PDF summary and share it yourself (for example with your doctor), that sharing is under your control.</p>
      </>
    ),
  },
  {
    id: "transfer", title: "Where your data is processed",
    body: (
      <p>
        Your data is stored on servers located in <V>[country / cloud region]</V>. Some service providers, such as the AI or mapping provider,
        may process the limited data they receive outside India. We transfer data only as permitted by the DPDP Act, and not to any country
        the Government of India has restricted.
      </p>
    ),
  },
  {
    id: "retention", title: "How long we keep data",
    body: (
      <ul>
        <li><strong>Guest use</strong>: reports and results are deleted automatically {SITE.guestRetentionHours} hours after upload.</li>
        <li><strong>Accounts</strong>: kept until you delete them. In Profile you can choose to have reports deleted automatically after a set number of days.</li>
        <li><strong>Deleted data</strong> is removed from the live system straight away and from backups within <V>[30]</V> days.</li>
        <li><strong>Technical logs</strong> are kept for up to <V>[90]</V> days, unless needed longer to investigate a security incident or required by law.</li>
      </ul>
    ),
  },
  {
    id: "security", title: "How we protect your data",
    body: (
      <>
        <ul>
          <li>All connections use encryption (HTTPS).</li>
          <li>Passwords are stored only as one-way hashes; sign-in cookies cannot be read by page scripts.</li>
          <li>Each account&apos;s and guest session&apos;s data is isolated, so other users cannot open your documents. Report files are served only through short-lived links.</li>
          <li>Access by our staff is limited to what is needed to run and support the Service.</li>
        </ul>
        <p>
          No system is completely secure. If a personal data breach occurs, we will notify affected users and the Data Protection Board of India
          as required by law.
        </p>
      </>
    ),
  },
  {
    id: "rights", title: "Your rights and choices",
    body: (
      <>
        <p>Under the DPDP Act and other applicable law, you have the right to:</p>
        <ul>
          <li><strong>Access</strong> a summary of the personal data we hold about you and how it is processed.</li>
          <li><strong>Correct or complete</strong> your data - you can edit extracted values and your profile directly in the app.</li>
          <li><strong>Erase</strong> your data - delete any report from History, or your whole account from Profile.</li>
          <li><strong>Withdraw consent</strong> at any time, by deleting your data or account. This does not affect processing that took place before.</li>
          <li><strong>Nominate</strong> another person to exercise these rights if you die or become unable to do so.</li>
          <li><strong>Raise a grievance</strong> with our Grievance Officer (section 14) and, if unresolved, with the Data Protection Board of India.</li>
        </ul>
        <p>To make a request, email <a href={`mailto:${SITE.privacyEmail}`}><V>{SITE.privacyEmail}</V></a>. We may need to confirm your identity first, and will respond within <V>[30]</V> days.</p>
      </>
    ),
  },
  {
    id: "children", title: "Children",
    body: (
      <p>
        The Service is intended for users aged 18 or over. A parent or legal guardian may use the Service to understand a child&apos;s lab report
        as the account holder, and by doing so gives consent on the child&apos;s behalf. We do not knowingly allow children to create accounts,
        and we do not track or target advertising at children.
      </p>
    ),
  },
  {
    id: "cookies", title: "Cookies and local storage",
    body: (
      <>
        <p>We use only strictly necessary cookies:</p>
        <ul>
          <li><strong>fitscan_guest</strong> - keeps your guest session, so you can see your own uploads (expires after {SITE.guestRetentionHours} hours).</li>
          <li><strong>fitscan_auth</strong> - keeps you signed in to your account.</li>
        </ul>
        <p>The site assistant keeps your chat in your browser&apos;s session storage, which is cleared when you close the tab. We do not use analytics, advertising or cross-site tracking cookies.</p>
      </>
    ),
  },
  {
    id: "links", title: "Links to other websites",
    body: (
      <p>
        FITSCAN links to other sites, such as MedlinePlus, the NIH and the NHS for health information, and Google Maps or diagnostic-centre
        websites. Their own privacy policies apply when you visit them.
      </p>
    ),
  },
  {
    id: "changes", title: "Changes to this policy",
    body: (
      <p>
        We may update this policy as the Service or the law changes. We will change the effective date at the top and, for significant
        changes, tell account holders on the site or by email before the changes take effect.
      </p>
    ),
  },
  {
    id: "contact", title: "Grievance Officer and contact",
    body: (
      <>
        <p>In line with the Information Technology Act, 2000, its rules, and the DPDP Act, 2023, our Grievance Officer is:</p>
        <ul>
          <li>Name: <V>{SITE.grievanceOfficer}</V></li>
          <li>Email: <a href={`mailto:${SITE.grievanceEmail}`}><V>{SITE.grievanceEmail}</V></a></li>
          <li>Address: <V>{SITE.companyName}</V>, <V>{SITE.companyAddress}</V></li>
        </ul>
        <p>We acknowledge grievances within 48 hours and aim to resolve them within <V>[30]</V> days. For general privacy questions, write to <a href={`mailto:${SITE.privacyEmail}`}><V>{SITE.privacyEmail}</V></a>.</p>
      </>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <LegalDocument title="Privacy Policy" effective={SITE.policyEffectiveDate} summary={SUMMARY} sections={SECTIONS}
      other={{ href: "/terms", label: "Terms & Conditions" }}
      intro={<p>Your lab reports are personal. This policy explains, in plain language, what we collect, why, and the choices you have.</p>} />
  );
}
