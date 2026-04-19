export default function Toggle({ enabled, onChange, size = "md", disabled = false, title }) {
  const sizes = {
    sm: { track: "w-7 h-4", dot: "w-2.5 h-2.5", translate: "translate-x-[14px]" },
    md: { track: "w-9 h-5", dot: "w-3.5 h-3.5", translate: "translate-x-[18px]" },
  };
  const s = sizes[size] || sizes.md;

  return (
    <button
      onClick={() => {
        if (disabled) return;
        onChange(!enabled);
      }}
      disabled={disabled}
      title={title}
      className={`${s.track} rounded-full relative transition-colors ${
        disabled ? "cursor-not-allowed opacity-55" : "cursor-pointer"
      } ${
        enabled ? "bg-blue-500/40" : "bg-zinc-700"
      }`}
    >
      <span
        className={`absolute left-0.5 top-1/2 -translate-y-1/2 ${s.dot} rounded-full transition-all ${
          enabled ? `${s.translate} bg-blue-400` : "bg-zinc-500"
        }`}
      />
    </button>
  );
}
