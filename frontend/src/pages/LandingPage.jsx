import { Link } from "react-router-dom";

const features = [
  { title: "Helmet Detection", desc: "YOLOv8-powered real-time helmet compliance monitoring across all camera feeds simultaneously.", tag: "YOLOv8", tagColor: "blue" },
  { title: "Fatigue Detection", desc: "SwinV2 transformer with facial landmark analysis detects drowsiness before accidents happen.", tag: "SwinV2", tagColor: "purple" },
  { title: "PPE Compliance", desc: "Full protective equipment checks — vests, gloves, goggles — all detected in a single pass.", tag: "6-Class", tagColor: "green" },
  { title: "Real-Time Alerts", desc: "Instant WebSocket-powered notifications when safety violations are detected on any feed.", tag: "WebSocket", tagColor: "red" },
  { title: "Live Monitoring", desc: "Multi-camera MJPEG streams with canvas-overlay annotations drawn in real time.", tag: "MJPEG", tagColor: "cyan" },
  { title: "Analytics Dashboard", desc: "Centralized monitoring with live feeds, alert history, and model performance metrics.", tag: "Dashboard", tagColor: "indigo" },
];

const techStack = [
  { name: "YOLOv8 Nano", desc: "Helmet & PPE object detection — optimized for real-time inference", emoji: "\u{1F537}", color: "blue" },
  { name: "SwinV2-Small", desc: "Shifted-window vision transformer for fatigue classification", emoji: "\u{1F9E0}", color: "purple" },
  { name: "dlib 68-Point Landmarks", desc: "Facial landmark detection for EAR, MAR, and head pose analysis", emoji: "\u{1F441}\uFE0F", color: "green" },
  { name: "PyTorch", desc: "Deep learning framework powering all model inference", emoji: "\u{1F525}", color: "red" },
  { name: "Django + Channels", desc: "ASGI backend with WebSocket support via Daphne", emoji: "\u26A1", color: "cyan" },
  { name: "React 18 + Tailwind v4", desc: "Modern frontend with Vite 5, real-time canvas overlays", emoji: "\u269B\uFE0F", color: "indigo" },
];

const screenshots = [
  { src: "/images/screenshots/01_feeds.png", caption: "Live Feeds — Multi-camera grid with real-time detection overlays", fullWidth: true },
  { src: "/images/screenshots/02_alerts.png", caption: "Alert Center — Grouped by severity, camera, or model" },
  { src: "/images/screenshots/03_models.png", caption: "Model Management — Enable/disable per camera" },
  { src: "/images/screenshots/04_devlab.png", caption: "Dev Lab — Video analysis and threshold tuning" },
  { src: "/images/screenshots/05_devlab_camera.png", caption: "Live Camera Test — Real-time overlay testing" },
  { src: "/images/screenshots/06_devlab_thresholds.png", caption: "Threshold Tuning — Fine-tune detection sensitivity", fullWidth: true },
];

const stats = [
  { value: "87.7%", label: "Fatigue Accuracy", sub: "SwinV2-S \u00B7 876 samples" },
  { value: "\u2014", label: "Helmet mAP", sub: "YOLOv8n \u00B7 TBD via benchmark" },
  { value: "\u2014", label: "PPE mAP", sub: "YOLOv8n \u00B7 TBD via benchmark" },
  { value: "6", label: "Detection Classes", sub: "Helmet \u00B7 Vest \u00B7 Gloves \u00B7 Goggles \u00B7 Fatigue \u00B7 Head" },
];

const REPO_URL = "https://github.com/SacreddPotato/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT";

/* Color mappings for feature tags and illustrations */
const tagStyles = {
  blue:   { bg: "rgba(59,130,246,0.1)",  color: "#60a5fa", border: "rgba(59,130,246,0.2)" },
  purple: { bg: "rgba(168,85,247,0.1)",  color: "#a855f7", border: "rgba(168,85,247,0.2)" },
  green:  { bg: "rgba(34,197,94,0.1)",   color: "#22c55e", border: "rgba(34,197,94,0.2)" },
  red:    { bg: "rgba(239,68,68,0.1)",   color: "#ef4444", border: "rgba(239,68,68,0.2)" },
  cyan:   { bg: "rgba(6,182,212,0.1)",   color: "#06b6d4", border: "rgba(6,182,212,0.2)" },
  indigo: { bg: "rgba(99,102,241,0.1)",  color: "#818cf8", border: "rgba(99,102,241,0.2)" },
};

const illustrationStyles = [
  { gradient: "linear-gradient(135deg, #1a1a2e, #16213e)", glow: "radial-gradient(circle at 70% 30%, rgba(59,130,246,0.3) 0%, transparent 60%)" },
  { gradient: "linear-gradient(135deg, #1a1a2e, #2d1b3d)", glow: "radial-gradient(circle at 30% 70%, rgba(168,85,247,0.3) 0%, transparent 60%)" },
  { gradient: "linear-gradient(135deg, #1a2e1a, #1a1a2e)", glow: "radial-gradient(circle at 40% 40%, rgba(34,197,94,0.3) 0%, transparent 60%)" },
  { gradient: "linear-gradient(135deg, #2d1f1f, #1a1a2e)", glow: "radial-gradient(circle at 50% 50%, rgba(239,68,68,0.3) 0%, transparent 60%)" },
  { gradient: "linear-gradient(135deg, #1a1a2e, #1e3a3a)", glow: "radial-gradient(circle at 60% 60%, rgba(6,182,212,0.3) 0%, transparent 60%)" },
  { gradient: "linear-gradient(135deg, #1e1a3e, #2a1a4e)", glow: "radial-gradient(circle at 50% 30%, rgba(99,102,241,0.3) 0%, transparent 60%)" },
];

const techIconStyles = {
  blue:   { background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)" },
  purple: { background: "rgba(168,85,247,0.1)", border: "1px solid rgba(168,85,247,0.2)" },
  green:  { background: "rgba(34,197,94,0.1)",  border: "1px solid rgba(34,197,94,0.2)" },
  red:    { background: "rgba(239,68,68,0.1)",  border: "1px solid rgba(239,68,68,0.2)" },
  cyan:   { background: "rgba(6,182,212,0.1)",  border: "1px solid rgba(6,182,212,0.2)" },
  indigo: { background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" },
};

/* SVG icons for each feature card */
const featureIcons = [
  // Helmet
  <svg key="helmet" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2C7.58 2 4 5.58 4 10v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2c0-4.42-3.58-8-8-8z"/>
    <path d="M4 12v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1"/>
    <line x1="2" y1="14" x2="22" y2="14"/>
  </svg>,
  // Face
  <svg key="face" viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M8 15c0 0 1.5 2 4 2s4-2 4-2"/>
    <line x1="9" y1="10" x2="9.01" y2="10"/>
    <line x1="15" y1="10" x2="15.01" y2="10"/>
  </svg>,
  // Heart/Check (PPE)
  <svg key="ppe" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/>
    <polyline points="9 12 12 15 20 7"/>
  </svg>,
  // Triangle/Alert
  <svg key="alert" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>,
  // Pulse line
  <svg key="pulse" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
  </svg>,
  // Grid layout
  <svg key="grid" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="4" rx="1"/>
    <rect x="14" y="10" width="7" height="11" rx="1"/>
    <rect x="3" y="13" width="7" height="8" rx="1"/>
  </svg>,
];

const steps = [
  { num: "1", title: "Connect Your Cameras", desc: "Add IP cameras or webcams through the dashboard. Devices on your network are ready in seconds." },
  { num: "2", title: "AI Analyzes Every Frame", desc: "YOLOv8 and SwinV2 models process each feed in real time \u2014 detecting helmets, fatigue, and PPE violations." },
  { num: "3", title: "Get Instant Alerts", desc: "WebSocket-powered notifications fire immediately when a violation is detected. Review, acknowledge, and act." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#09090b]" style={{ backgroundImage: "none" }}>
      {/* ========== NAVBAR ========== */}
      <nav className="fixed top-0 left-0 right-0 z-100 flex items-center justify-between px-6 md:px-12 py-4 bg-[#09090b]/80 backdrop-blur-lg border-b border-zinc-800/50">
        <div className="flex items-center gap-2 text-zinc-100 font-extrabold text-lg tracking-wide">
          <span className="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.6)]" />
          SafeVision
        </div>
        <div className="flex items-center gap-7">
          <a href="#features" className="hidden md:inline text-[13px] font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Features</a>
          <a href="#how-it-works" className="hidden md:inline text-[13px] font-medium text-zinc-400 hover:text-zinc-100 transition-colors">How It Works</a>
          <a href="#tech" className="hidden md:inline text-[13px] font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Tech Stack</a>
          <a href="#screenshots" className="hidden md:inline text-[13px] font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Screenshots</a>
          <a href="#stats" className="hidden md:inline text-[13px] font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Stats</a>
          <Link
            to="/feeds"
            className="px-5 py-2 rounded-lg text-[13px] font-bold text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:-translate-y-0.5 hover:shadow-[0_4px_20px_rgba(99,102,241,0.4)] transition-all"
          >
            Launch Dashboard &rarr;
          </Link>
        </div>
      </nav>

      {/* ========== HERO ========== */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background image + overlay */}
        <div className="absolute inset-0" style={{ backgroundImage: "url('/images/hero.jpg')", backgroundSize: "cover", backgroundPosition: "center" }}>
          <div className="absolute inset-0" style={{ background: "linear-gradient(to bottom, rgba(9,9,11,0.75) 0%, rgba(9,9,11,0.55) 40%, rgba(9,9,11,0.85) 80%, #09090b 100%)" }} />
        </div>

        <div className="relative z-10 text-center px-6 pt-30 pb-20 max-w-[800px]">
          <div className="inline-flex items-center gap-2 text-xs font-semibold tracking-[2px] uppercase text-purple-400 mb-6 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/25">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />
            AI-Powered Safety Monitoring
          </div>
          <h1 className="text-4xl md:text-[64px] font-extrabold text-white leading-[1.1] mb-5">
            See the Danger<br />
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Before It Happens.</span>
          </h1>
          <p className="text-lg text-zinc-400 leading-relaxed max-w-[560px] mx-auto mb-9">
            Computer vision that watches every feed, detects every hazard, and alerts your team in real time — so every worker comes home safe.
          </p>
          <Link
            to="/feeds"
            className="inline-flex items-center gap-2 px-9 py-3.5 rounded-xl text-base font-bold text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgba(99,102,241,0.4)] transition-all tracking-wide"
          >
            Launch Dashboard
            <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          </Link>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 text-zinc-500 text-xs text-center animate-bounce">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section id="features" className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
        <span className="inline-block text-[11px] font-bold tracking-[2px] uppercase px-3 py-1 rounded-md mb-4" style={{ background: "rgba(99,102,241,0.1)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.2)" }}>
          Features
        </span>
        <h2 className="text-3xl md:text-4xl font-extrabold text-zinc-100 mb-3 leading-tight">
          Everything You Need to<br />Keep Your Team Safe
        </h2>
        <p className="text-base text-zinc-500 max-w-[560px] leading-relaxed mb-12">
          Six integrated AI capabilities working together to provide comprehensive workplace safety monitoring.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map((f, i) => {
            const ts = tagStyles[f.tagColor];
            const ill = illustrationStyles[i];
            return (
              <div
                key={f.title}
                className="group relative rounded-[14px] border border-zinc-800 bg-[#18181b] p-7 transition-all duration-300 hover:border-indigo-500 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(99,102,241,0.12)] overflow-hidden"
              >
                {/* Top gradient border on hover */}
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                {/* Illustration */}
                <div
                  className="w-14 h-14 rounded-[14px] mb-4 flex items-center justify-center relative overflow-hidden"
                  style={{ background: ill.gradient }}
                >
                  <div className="absolute inset-0" style={{ background: ill.glow }} />
                  <div className="w-7 h-7 relative z-10">
                    {featureIcons[i]}
                  </div>
                </div>

                <h3 className="text-base font-bold text-zinc-100 mb-1.5">{f.title}</h3>
                <p className="text-[13px] text-zinc-400 leading-relaxed">{f.desc}</p>
                <span
                  className="inline-block text-[10px] font-semibold tracking-[1px] uppercase px-2 py-0.5 rounded mt-3"
                  style={{ background: ts.bg, color: ts.color, border: `1px solid ${ts.border}` }}
                >
                  {f.tag}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========== HOW IT WORKS ========== */}
      <section id="how-it-works" className="bg-[#0c0c0f] border-t border-b border-[#1a1a1e]">
        <div className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
          <span className="inline-block text-[11px] font-bold tracking-[2px] uppercase px-3 py-1 rounded-md mb-4" style={{ background: "rgba(6,182,212,0.1)", color: "#22d3ee", border: "1px solid rgba(6,182,212,0.2)" }}>
            How It Works
          </span>
          <h2 className="text-3xl md:text-4xl font-extrabold text-zinc-100 mb-3 leading-tight">
            Three Steps to Safer Workplaces
          </h2>
          <p className="text-base text-zinc-500 max-w-[560px] leading-relaxed mb-12">
            From camera to alert in under a second.
          </p>

          <div className="flex flex-col md:flex-row items-start gap-6 relative">
            {steps.map((s, i) => (
              <div key={s.num} className="flex-1 relative text-center p-8 bg-[#18181b] border border-zinc-800 rounded-2xl">
                <div className="w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center text-xl font-extrabold text-indigo-400 border border-indigo-500/30" style={{ background: "linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))" }}>
                  {s.num}
                </div>
                <h3 className="text-base font-bold text-zinc-100 mb-2">{s.title}</h3>
                <p className="text-[13px] text-zinc-400 leading-relaxed">{s.desc}</p>

                {/* Arrow between steps (hidden on mobile and after last) */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-14 -right-6 z-10 text-indigo-500 text-xl w-6 text-center">
                    &rarr;
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== TECH STACK ========== */}
      <section id="tech" className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
        <span className="inline-block text-[11px] font-bold tracking-[2px] uppercase px-3 py-1 rounded-md mb-4" style={{ background: "rgba(168,85,247,0.1)", color: "#c084fc", border: "1px solid rgba(168,85,247,0.2)" }}>
          Under the Hood
        </span>
        <h2 className="text-3xl md:text-4xl font-extrabold text-zinc-100 mb-3 leading-tight">
          Built on Proven Technology
        </h2>
        <p className="text-base text-zinc-500 max-w-[560px] leading-relaxed mb-12">
          A modern full-stack architecture with state-of-the-art deep learning models.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {techStack.map((t) => {
            const iconStyle = techIconStyles[t.color];
            return (
              <div
                key={t.name}
                className="flex items-center gap-4 p-5 rounded-xl border border-zinc-800 bg-[#18181b] transition-all hover:border-zinc-700"
              >
                <div
                  className="w-11 h-11 rounded-[10px] flex items-center justify-center text-[22px] shrink-0"
                  style={iconStyle}
                >
                  {t.emoji}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-zinc-100 mb-0.5">{t.name}</h4>
                  <span className="text-xs text-zinc-500">{t.desc}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========== SCREENSHOTS ========== */}
      <section id="screenshots" className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
        <span className="inline-block text-[11px] font-bold tracking-[2px] uppercase px-3 py-1 rounded-md mb-4" style={{ background: "rgba(59,130,246,0.1)", color: "#60a5fa", border: "1px solid rgba(59,130,246,0.2)" }}>
          The Dashboard
        </span>
        <h2 className="text-3xl md:text-4xl font-extrabold text-zinc-100 mb-3 leading-tight">
          See It in Action
        </h2>
        <p className="text-base text-zinc-500 max-w-[560px] leading-relaxed mb-12">
          Real screenshots from the SafeVision monitoring dashboard.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {screenshots.map((s) => (
            <div
              key={s.src}
              className={`rounded-xl overflow-hidden border border-zinc-800 bg-[#18181b] transition-all hover:border-zinc-700 hover:-translate-y-0.5${s.fullWidth ? " md:col-span-2" : ""}`}
            >
              <img src={s.src} alt={s.caption} className="w-full h-auto block" />
              <div className="px-4 py-3 text-[13px] text-zinc-400 font-medium">{s.caption}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ========== STATS ========== */}
      <section id="stats" className="bg-[#0c0c0f] border-t border-b border-[#1a1a1e]">
        <div className="py-24 px-6 md:px-12 max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <span className="inline-block text-[11px] font-bold tracking-[2px] uppercase px-3 py-1 rounded-md mb-4" style={{ background: "rgba(99,102,241,0.1)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.2)" }}>
              Performance
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-zinc-100 mb-3 leading-tight">
              Real Numbers. Real Models.
            </h2>
            <p className="text-base text-zinc-500 max-w-[560px] mx-auto leading-relaxed">
              Benchmark results from our actual model evaluation — no marketing fluff.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center py-8 px-4">
                <div className="text-5xl font-extrabold leading-none bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                  {s.value}
                </div>
                <div className="text-sm text-zinc-500 font-medium">{s.label}</div>
                <div className="text-[11px] text-zinc-600 mt-1">{s.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== FOOTER ========== */}
      <footer className="border-t border-[#1a1a1e]">
        <div className="py-12 px-6 md:px-12 max-w-[1200px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-zinc-100 text-[15px]">SafeVision</span>
            <span className="text-zinc-600 text-xs ml-3">&copy; 2026 &middot; AI-Powered Worker Safety</span>
          </div>
          <div className="flex items-center gap-5">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[13px] text-zinc-500 hover:text-zinc-100 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.02 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.82.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/></svg>
              GitHub Repo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
