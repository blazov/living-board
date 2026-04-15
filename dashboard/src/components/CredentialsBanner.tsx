const REQUIRED_ENV_VARS = ["AUTH_SECRET", "CLAUDE_API_KEY", "TRIGGER_ID"] as const;

export function CredentialsBanner() {
  const missing = REQUIRED_ENV_VARS.filter((name) => !process.env[name]);

  if (missing.length === 0) {
    return null;
  }

  return (
    <div className="bg-red-950/80 border-b border-red-500/40 text-red-200 px-4 py-3">
      <p className="text-sm font-semibold">
        Missing required credentials:{" "}
        {missing.map((name, i) => (
          <span key={name}>
            <code className="font-mono bg-red-900/60 px-1 rounded">{name}</code>
            {i < missing.length - 1 ? ", " : ""}
          </span>
        ))}
      </p>
      <p className="text-xs mt-1 text-red-300/80">
        See bootstrap guide:{" "}
        <span className="font-mono">artifacts/research/credential-bootstrap-guide.md</span>
      </p>
    </div>
  );
}
