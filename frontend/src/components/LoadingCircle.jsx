export default function LoadingCircle({ label = "Loading..." }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center gap-3">
      <svg viewBox="0 0 24 24" className="w-7 h-7 text-blue-400 animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 12a9 9 0 1 1-2.64-6.36" />
      </svg>
      <p className="text-[11px] text-zinc-400">{label}</p>
    </div>
  );
}
