/**
 * Legal / contact details used by the Privacy Policy and Terms & Conditions.
 * Values in [square brackets] are PLACEHOLDERS - replace them before a public launch (docs/launch_checklist.md).
 * Both policies must be reviewed by a lawyer familiar with India's DPDP Act 2023 and IT Act 2000 before launch.
 */
export const SITE = {
  name: "FITSCAN",
  companyName: "[Company legal name]",
  companyAddress: "[Registered office address, City, State, PIN]",
  privacyEmail: "privacy@[your-domain]",
  supportEmail: "support@[your-domain]",
  grievanceOfficer: "[Name of Grievance Officer]",
  grievanceEmail: "grievance@[your-domain]",
  jurisdictionCity: "[City]",
  policyEffectiveDate: "11 November 2026",
  termsEffectiveDate: "11 November 2026",
  guestRetentionHours: 24,
} as const;

export const isPlaceholder = (v: string) => /\[.*\]/.test(v);
