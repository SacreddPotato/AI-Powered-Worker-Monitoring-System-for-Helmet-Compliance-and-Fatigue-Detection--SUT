import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import VisualEntry from "../components/VisualEntry";

// --- HEALPER COMPONENT FOR SCROLL REVEAL ---
const Reveal = ({ children, delay = 0, className = "" }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal-hidden ${isVisible ? "reveal-active" : ""} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
};

// --- DYNAMIC CARD COMPONENT (Mouse Interaction) ---
const DynamicCard = ({ children, className = "", delay = 0, style = {} }) => {
  const cardRef = useRef(null);
  const [mousePos, setMousePos] = useState({ rotateX: 0, rotateY: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Set CSS variables for spotlight
    cardRef.current.style.setProperty("--mouse-x", `${x}px`);
    cardRef.current.style.setProperty("--mouse-y", `${y}px`);

    // Calculate rotation for 3D tilt
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (centerY - y) / 25; // Slightly gentler as requested previously
    const rotateY = (x - centerX) / 25;
    setMousePos({ rotateX, rotateY });
  };

  return (
    <Reveal delay={delay} className="w-full">
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => {
          setIsHovered(false);
          setMousePos({ rotateX: 0, rotateY: 0 });
        }}
        className={`dynamic-card glass-card rounded-2xl group ${className}`}
        style={{
          ...style,
          transform: isHovered 
            ? `perspective(1000px) rotateX(${mousePos.rotateX}deg) rotateY(${mousePos.rotateY}deg) scale(1.02)` 
            : `perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)`,
        }}
      >
        <div className="spotlight-wrapper">
          <div className="spotlight" />
        </div>
        <div className="tech-bracket tech-bracket-tl" />
        <div className="tech-bracket tech-bracket-br" />
        <div className="relative z-10 h-full">{children}</div>
      </div>
    </Reveal>
  );
};

const features = [
  { title: "Fatigue Detection", desc: "Prevents drowsy worker incidents that cause 20% of all workplace injuries globally. Detects fatigue 2-3 seconds before critical errors occur, protecting your workforce.", color: "purple" },
  { title: "Helmet Detection", desc: "Ensures mandatory head protection. Head injuries represent 25% of fatal workplace accidents globally. Proper helmets reduce fatal head injury risk by 60%+.", color: "blue" },
  { title: "Vest Detection", desc: "Verifies high-visibility protection in hazardous zones. Visibility gear prevents 70% of struck-by incidents globally, eliminating visibility-related near-misses.", color: "green" },
  { title: "Goggles Detection", desc: "Detects protective eyewear compliance in hazardous environments. Eye injuries cause 2,000 lost work days per year in the US. Proper goggles prevent 90% of preventable eye injuries.", color: "cyan" },
  { title: "Gloves Detection", desc: "Monitors hand protection compliance across all teams. Hand and finger injuries account for 10-12% of all workplace injuries worldwide. Proper gloves prevent 80% of these preventable incidents.", color: "orange" },
  { title: "Face Shield Detection", desc: "Protects against eye and face hazards. Face/eye injuries cause 4% of all workplace incidents globally and are a leading cause of blindness. Shields prevent 90% of these injuries.", color: "amber" },
  { title: "Safety Suit Detection", desc: "Ensures full-body protection compliance in hazardous environments. Comprehensive PPE usage reduces serious injury incidents by 65-75% across all industries worldwide.", color: "indigo" },
  { title: "Shoes Detection", desc: "Verifies safety footwear in high-risk work zones. Foot injuries are responsible for 10% of workplace accidents globally. Proper safety shoes prevent 85% of lower-body injuries.", color: "amber" },
];

const techStack = [
  { name: "Computer Vision", desc: "State-of-the-art visual recognition algorithms for real-time safety compliance.", emoji: "👁️", color: "green" },
  { name: "Deep Learning", desc: "Advanced neural network architectures trained on industrial safety scenarios.", emoji: "🧠", color: "purple" },
  { name: "PyTorch", desc: "The industry-leading machine learning framework powering all model inference.", emoji: "🔥", color: "red" },
  { name: "YOLO", desc: "Ultra-fast object detection optimized for real-time helmet and PPE identification.", emoji: "💠", color: "blue" },
  { name: "SwinV2", desc: "Shifted-window vision transformers used for high-accuracy fatigue classification.", emoji: "🤖", color: "cyan" },
  { name: "React", desc: "Modern, high-performance web interface for real-time data visualization.", emoji: "⚛️", color: "indigo" },
];

const steps = [
  { num: "01", title: "Seamless Integration", desc: "Easily link your existing site cameras to our platform. Setup takes just a few clicks to start monitoring your workspace." },
  { num: "02", title: "Continuous Monitoring", desc: "Our intelligent software watches out for your team round the clock, ensuring safety gear is worn and signs of fatigue are caught early." },
  { num: "03", title: "Immediate Notifications", desc: "Receive instant alerts the moment a potential hazard is caught, allowing supervisors to respond swiftly and keep everyone safe." },
];

const REPO_URL = "https://github.com/SacreddPotato/AI-Powered-Worker-Monitoring-System-for-Helmet-Compliance-and-Fatigue-Detection--SUT";

// Helper icons for detection layers
const featureIcons = {
  purple: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><path d="M8 15c0 0 1.5 2 4 2s4-2 4-2"/><line x1="9" y1="10" x2="9.01" y2="10"/><line x1="15" y1="10" x2="15.01" y2="10"/>
    </svg>
  ),
  blue: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2C7.58 2 4 5.58 4 10v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2c0-4.42-3.58-8-8-8z"/><path d="M4 12v1a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1"/><line x1="2" y1="14" x2="22" y2="14"/>
    </svg>
  ),
  green: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 5l1.5-3h9L18 5L20 22H4L6 5Z" /><path d="M9 5v4" /><path d="M15 5v4" />
    </svg>
  ),
  cyan: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7" cy="12" r="4" /><circle cx="17" cy="12" r="4" /><path d="M11 12h2" /><path d="M3 12h.01" /><path d="M21 12h.01" />
    </svg>
  ),
  orange: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 21V9a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v12" /><path d="M10 5V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2" />
    </svg>
  ),
  amber: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 10v4" /><path d="M20 10v4" /><path d="M6 4h12c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><path d="M8 4v16" /><path d="M16 4v16" />
    </svg>
  ),
  indigo: (
    <svg viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 4h8" /><path d="M12 4v16" /><path d="M8 20h8" /><path d="M5 8h14" /><path d="M5 16h14" />
    </svg>
  )
};

export default function LandingPage() {
  const [showEntry, setShowEntry] = useState(true);
  const heroRef = useRef(null);

  const handleHeroMouseMove = (e) => {
    if (!heroRef.current) return;
    const rect = heroRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    heroRef.current.style.setProperty("--mouse-x", `${x}px`);
    heroRef.current.style.setProperty("--mouse-y", `${y}px`);
  };

  return (
    <div className="min-h-screen bg-[#140f1f] text-zinc-100 selection:bg-indigo-500/30 selection:text-indigo-200">
      {showEntry && <VisualEntry onComplete={() => setShowEntry(false)} />}
      
      {/* ========== NAVBAR ========== */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-5 bg-[#140f1f]/80 backdrop-blur-xl border-b border-indigo-900/20">
        <div className="flex items-center gap-3 font-black text-xl tracking-tight">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.8)] animate-pulse" />
          SafeVision AI
        </div>
        <div className="flex items-center gap-8">
          <div className="hidden lg:flex items-center gap-8">
            <a href="#models" className="text-[11px] font-black text-zinc-500 hover:text-indigo-400 tracking-widest transition-all">Detection Models</a>
            <a href="#how-it-works" className="text-[11px] font-black text-zinc-500 hover:text-indigo-400 tracking-widest transition-all">How It Works</a>
            <a href="#tech" className="text-[11px] font-black text-zinc-500 hover:text-indigo-400 tracking-widest transition-all">Under the Hood</a>
            <a href="#guarantee" className="text-[11px] font-black text-zinc-500 hover:text-indigo-400 tracking-widest transition-all">Our Guarantee</a>
          </div>
          <Link
            to="/feeds"
            className="px-6 py-2.5 rounded-lg text-[11px] font-black tracking-widest text-white bg-indigo-600 hover:bg-indigo-500 shadow-[0_4px_20px_rgba(79,70,229,0.3)] hover:shadow-[0_4px_25px_rgba(79,70,229,0.5)] transition-all"
          >
            Launch Dashboard &rarr;
          </Link>
        </div>
      </nav>

      {/* ========== HERO ========== */}
      <section 
        ref={heroRef}
        onMouseMove={handleHeroMouseMove}
        className="relative min-h-screen flex items-center justify-center overflow-hidden"
      >
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-[url('/images/Construction-Safety-Equipment.jpg')] bg-cover bg-center" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#09090b]/70 via-[#09090b]/40 to-[#09090b]" />
          
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{
              background: `radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(99,102,241,0.1), transparent)`
            }}
          />
        </div>

        <div className="relative z-10 text-center px-6 max-w-[900px]">
          <Reveal>
            <div className="inline-flex items-center gap-3 text-[10px] font-black tracking-[0.4em] uppercase text-indigo-400 mb-8 px-6 py-2.5 rounded-full border border-indigo-500/20 bg-indigo-950/20 backdrop-blur-md">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping" />
              AI-Powered Safety Monitoring
            </div>
          </Reveal>
          
          <Reveal delay={200}>
            <h1 className="text-6xl md:text-[92px] font-black text-white leading-[0.9] mb-8 tracking-tighter">
              See the Danger<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 animate-gradient">Before It Happens.</span>
            </h1>
          </Reveal>

          <Reveal delay={400}>
            <p className="text-lg text-zinc-300 font-bold leading-relaxed max-w-[650px] mx-auto mb-12">
              Computer vision that watches every feed, detects every hazard, and alerts your team in real time — so every worker comes home safe.
            </p>
          </Reveal>

          <Reveal delay={600}>
            <Link
              to="/feeds"
              className="inline-flex items-center gap-4 px-10 py-5 rounded-xl text-sm font-black tracking-widest text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:-translate-y-0.5 hover:shadow-[0_10px_40px_rgba(99,102,241,0.4)] transition-all"
            >
              Launch Dashboard &rarr;
            </Link>
          </Reveal>
          
          <div className="absolute -top-12 -left-12 hud-coordinates animate-[float_6s_ease-in-out_infinite] opacity-40 hidden xl:block">
            SCAN_INIT [ 0.2341, 1.2942 ]<br/>
            COORD_Z // 87.2%
          </div>
          <div className="absolute -bottom-12 -right-12 hud-coordinates animate-[float_8s_ease-in-out_infinite_reverse] opacity-40 hidden xl:block">
            REFRACTION_ENGINE // ON<br/>
            FPS_STABLE // 60.0
          </div>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section id="models" className="py-24 px-6 md:px-12 max-w-[1400px] mx-auto">
        <Reveal className="mb-20">
          <span className="inline-block text-[11px] font-black tracking-[4px] uppercase text-indigo-500 mb-4">Detection Models</span>
          <h2 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">The Eight Safety AI Models</h2>
          <p className="text-base text-zinc-500 max-w-[600px] leading-relaxed tracking-widest">
            Eight formidable deep learning models working in perfect harmony to deliver comprehensive workplace hazard detection.
          </p>
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <DynamicCard key={f.title} delay={i * 50} className="p-8 min-h-[280px] flex flex-col">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-white/5 border border-white/10 group-hover:bg-indigo-500/20 group-hover:border-indigo-500/30 transition-all duration-300 mb-8">
                {featureIcons[f.color]}
              </div>
              <h3 className="text-lg font-black text-white tracking-tight mb-4 group-hover:text-indigo-400 transition-colors">{f.title}</h3>
              <p className="text-[13px] text-zinc-500 font-bold leading-relaxed tracking-wider">{f.desc}</p>
            </DynamicCard>
          ))}
        </div>
      </section>

      {/* ========== HOW IT WORKS ========== */}
      <section id="how-it-works" className="py-32 bg-[#181224] border-y border-white/5">
        <div className="px-6 md:px-12 max-w-[1200px] mx-auto">
          <Reveal className="text-center mb-24">
            <div className="inline-flex items-center gap-3 text-[10px] font-black tracking-[0.5em] uppercase px-6 py-2.5 rounded-full bg-cyan-950/20 border border-cyan-500/20 text-cyan-500 mb-8">
               <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse" />
               Operational Workflow
            </div>
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tighter">Three Steps to Safer Workplaces</h2>
          </Reveal>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {steps.map((s, i) => (
              <DynamicCard key={s.num} delay={i * 100} className="p-10 border-l-2 border-l-cyan-500/30 hover:border-l-cyan-500 transition-all">
                <div className="absolute top-10 right-10 text-5xl font-black text-white/5 group-hover:text-white/10 transition-colors">{s.num}</div>
                <h3 className="text-xl font-black text-white mb-6 tracking-tight">{s.title}</h3>
                <p className="text-sm text-zinc-400 font-bold leading-relaxed tracking-widest">{s.desc}</p>
              </DynamicCard>
            ))}
          </div>
        </div>
      </section>

      {/* ========== TECH STACK ========== */}
      <section id="tech" className="py-32 px-6 md:px-12 max-w-[1400px] mx-auto">
        <Reveal className="mb-16">
          <span className="text-[11px] font-black tracking-[4px] uppercase text-purple-500 mb-6 block">Building Blocks</span>
          <h2 className="text-5xl font-black text-white tracking-tighter">Under the Hood</h2>
        </Reveal>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {techStack.map((t, i) => (
            <DynamicCard key={t.name} delay={i * 50} className="p-6 flex items-center gap-5 hover:border-purple-500/30">
               <div className="w-14 h-14 rounded-xl flex items-center justify-center text-3xl bg-white/5 border border-white/10">
                  {t.emoji}
               </div>
               <div>
                  <h4 className="text-[13px] font-black text-white tracking-widest mb-1">{t.name}</h4>
                  <p className="text-[11px] font-bold text-zinc-600">{t.desc}</p>
               </div>
            </DynamicCard>
          ))}
        </div>
      </section>

      {/* ========== GUARANTEE ========== */}
      <section id="guarantee" className="py-32 bg-[#140f1f] border-t border-indigo-900/10">
        <div className="px-6 md:px-12 max-w-[1200px] mx-auto text-center">
          <Reveal>
             <span className="inline-block text-[11px] font-black tracking-[4px] uppercase text-green-500 mb-8">Our Guarantee</span>
             <h2 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-12">Built For Industrial Demands.</h2>
          </Reveal>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            <DynamicCard className="p-10 border-t-2 border-t-green-500/30 hover:border-t-green-500 transition-all">
              <h3 className="text-lg font-black text-white mb-6 flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                Privacy By Default
              </h3>
              <p className="text-sm text-zinc-400 font-bold leading-relaxed tracking-wider">
                All data is processed strictly on-edge. We never store facial records, and any untriggered streams expire immediately after evaluation.
              </p>
            </DynamicCard>
            <DynamicCard className="p-10 border-t-2 border-t-blue-500/30 hover:border-t-blue-500 transition-all">
              <h3 className="text-lg font-black text-white mb-6 flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                Hardware Agnostic
              </h3>
              <p className="text-sm text-zinc-400 font-bold leading-relaxed tracking-wider">
                Works straight out of the box with your existing RTSP or USB feeds. No proprietary hardware or expensive camera infrastructure required.
              </p>
            </DynamicCard>
            <DynamicCard className="p-10 border-t-2 border-t-purple-500/30 hover:border-t-purple-500 transition-all">
              <h3 className="text-lg font-black text-white mb-6 flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-purple-500" />
                Infinite Scalability
              </h3>
              <p className="text-sm text-zinc-400 font-bold leading-relaxed tracking-wider">
                Monitor a single small site entrance or an intense, multi-zone heavy manufacturing facility. Scale your deployment limits instantly.
              </p>
            </DynamicCard>
          </div>
        </div>
      </section>

      {/* ========== FOOTER ========== */}
      <footer className="py-20 border-t border-white/5 bg-[#140f1f]">
        <div className="px-6 md:px-12 max-w-[1400px] mx-auto flex flex-col md:flex-row items-center justify-between gap-12 text-center md:text-left">
          <div>
            <div className="text-2xl font-black text-white tracking-tighter mb-2">Safe Vision AI</div>
            <p className="text-[10px] text-zinc-500 font-black tracking-[0.5em]">&copy; 2026 &middot; AI-powered Worker Safety</p>
          </div>
          <div className="flex gap-12">
            <a href={REPO_URL} target="_blank" className="text-[11px] font-black text-zinc-500 hover:text-indigo-400 transition-colors tracking-[0.2em] flex items-center gap-3">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58v-2.03c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.02 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.82.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/></svg>
              GitHub_Repo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
