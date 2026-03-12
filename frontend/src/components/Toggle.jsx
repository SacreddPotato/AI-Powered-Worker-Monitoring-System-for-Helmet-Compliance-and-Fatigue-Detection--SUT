export default function Toggle({ enabled, onChange, size = "md" }) {
  const sizes = {
    sm: { track: "w-7 h-4", dot: "w-2.5 h-2.5", translate: "translate-x-3" },
    md: { track: "w-9 h-5", dot: "w-3.5 h-3.5", translate: "translate-x-4" },
  };
  const s = sizes[size] || sizes.md;

  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`${s.track} rounded-full relative transition-colors cursor-pointer ${
        enabled ? "bg-blue-500/40" : "bg-zinc-700"
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 ${s.dot} rounded-full transition-all ${
          enabled ? `${s.translate} bg-blue-400` : "bg-zinc-500"
        }`}
      />
    </button>
  );
}
