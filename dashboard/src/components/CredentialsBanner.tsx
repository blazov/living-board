/**
 * Server component: renders a warning banner when critical env vars are missing.
 * Reads process.env at render time — no client JS, no secrets exposed.
 * Returns null when everything is configured.
 */
export default function CredentialsBanner() {
  const checks: { name: string; set: boolean }[] = [
    { name: "AUTH_SECRET", set: !!process.env.AUTH_SECRET },
    { name: "NEXT_PUBLIC_SUPABASE_URL", set: !!process.env.NEXT_PUBLIC_SUPABASE_URL },
    { name: "NEXT_PUBLIC_SUPABASE_ANON_KEY", set: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY },
  ];

  const missing = checks.filter((c) => !c.set);

  if (missing.length === 0) return null;

  return (
    <div
      role="alert"
      style={{
        background: "#991b1b",
        color: "#fef2f2",
        padding: "12px 16px",
        fontFamily: "system-ui, sans-serif",
        fontSize: "14px",
        lineHeight: "1.5",
      }}
    >
      <strong>Missing credentials:</strong>{" "}
      {missing.map((m) => m.name).join(", ")}.{" "}
      The dashboard may not work correctly. See{" "}
      <span style={{ textDecoration: "underline" }}>
        artifacts/research/credential-bootstrap-guide.md
      </span>{" "}
      for setup instructions.
    </div>
  );
}
