const VARIANTS = {
  danger: "bg-red-500/15 text-red-300 border-red-500/25",
  warning: "bg-amber-500/12 text-amber-300 border-amber-500/20",
  success: "bg-green-500/10 text-green-300 border-green-500/20",
  info: "bg-blue-500/10 text-blue-300 border-blue-500/20",
  muted: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

export default function Badge({ variant = "muted", children, className = "" }) {
  return (
    <span className={`text-[8px] font-semibold px-2 py-0.5 rounded border inline-block ${VARIANTS[variant]} ${className}`}>
      {children}
    </span>
  );
}
