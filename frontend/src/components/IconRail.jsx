import { NavLink } from "react-router-dom";

const icons = {
  feeds: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="8" height="8" rx="1" /><rect x="14" y="3" width="8" height="8" rx="1" />
      <rect x="2" y="13" width="8" height="8" rx="1" /><rect x="14" y="13" width="8" height="8" rx="1" />
    </svg>
  ),
  alerts: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  ),
  models: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  devlab: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
    </svg>
  ),
  overview: (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 10.5L12 3l9 7.5" />
      <path d="M5.5 9.5V20h13V9.5" />
      <path d="M10 20v-5h4v5" />
    </svg>
  ),
};

const navItems = [
  { to: "/feeds", icon: "feeds", label: "Feeds" },
  { to: "/alerts", icon: "alerts", label: "Alerts" },
  { to: "/models", icon: "models", label: "Models" },
  { to: "/devlab", icon: "devlab", label: "Dev Lab" },
];

const overviewItem = { to: "/", icon: "overview", label: "Project Overview" };

export default function IconRail({ alertCount = 0, currentPath = "", onNavigateStart }) {
  return (
    <nav className="w-14 bg-[#0c0c0f] border-r border-zinc-800/60 flex flex-col items-center py-3 gap-1.5 shrink-0">
      <div className="w-8 h-8 rounded-lg overflow-hidden border border-zinc-800 mb-4 bg-zinc-900">
        <img
          src="/images/assets/logo.jpg"
          alt="SafeVision AI"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="flex flex-col items-center gap-1.5 w-full flex-1">
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => {
              if (to !== currentPath) onNavigateStart?.(to);
            }}
            className={({ isActive }) =>
              `w-9 h-9 rounded-lg flex items-center justify-center relative transition-colors ${
                isActive ? "bg-blue-500/10 text-blue-400" : "text-zinc-600 hover:text-zinc-400 hover:bg-white/[0.03]"
              }`
            }
            title={label}
          >
            {icons[icon]}
            {icon === "alerts" && alertCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-[#0c0c0f] animate-pulse-dot" />
            )}
          </NavLink>
        ))}

        <NavLink
          key={overviewItem.to}
          to={overviewItem.to}
          onClick={() => {
            if (overviewItem.to !== currentPath) onNavigateStart?.(overviewItem.to);
          }}
          className={({ isActive }) =>
            `w-9 h-9 rounded-lg flex items-center justify-center relative transition-colors mt-auto ${
              isActive ? "bg-blue-500/10 text-blue-400" : "text-zinc-600 hover:text-zinc-400 hover:bg-white/[0.03]"
            }`
          }
          title={overviewItem.label}
        >
          {icons[overviewItem.icon]}
        </NavLink>
      </div>
    </nav>
  );
}
