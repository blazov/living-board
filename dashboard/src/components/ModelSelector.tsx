interface Props {
  value: string;
  onChange: (model: string) => void;
  label?: string;
  size?: "sm" | "md";
}

const MODELS = [
  { value: "", label: "Default", description: "Opus orchestrator decides" },
  { value: "opus", label: "Opus", description: "Complex reasoning" },
  { value: "sonnet", label: "Sonnet", description: "Standard execution" },
  { value: "haiku", label: "Haiku", description: "Simple tasks" },
];

const MODEL_COLOR: Record<string, string> = {
  "": "text-white/30 border-white/10",
  opus: "text-purple-400 border-purple-500/30",
  sonnet: "text-blue-400 border-blue-500/30",
  haiku: "text-green-400 border-green-500/30",
};

export function ModelSelector({ value, onChange, label, size = "md" }: Props) {
  const selected = MODELS.find((m) => m.value === value) ?? MODELS[0];
  const colorClass = MODEL_COLOR[value] ?? MODEL_COLOR[""];

  if (size === "sm") {
    return (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`text-[10px] px-1.5 py-0.5 rounded border bg-transparent cursor-pointer focus:outline-none ${colorClass}`}
        title="Model override"
      >
        {MODELS.map((m) => (
          <option key={m.value} value={m.value} className="bg-[#111] text-white">
            {m.label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-white/30">{label}:</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`text-xs px-2 py-1 rounded border bg-transparent cursor-pointer focus:outline-none ${colorClass}`}
      >
        {MODELS.map((m) => (
          <option key={m.value} value={m.value} className="bg-[#111] text-white">
            {m.label} — {m.description}
          </option>
        ))}
      </select>
    </div>
  );
}
