import { useState, useEffect, useRef } from "react";
import { api } from "../api";

const TABS = ["Video Analysis", "Live Camera Test", "Threshold Tuning", "Performance"];

export default function DevLabPage() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Developer Lab</h1>
          <span className="text-xs text-zinc-600">Testing & debugging</span>
        </div>
      </div>

      <div className="flex border-b border-zinc-800/60 px-5 shrink-0">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-[11px] border-b-2 -mb-px transition-colors ${
              activeTab === i
                ? "text-blue-400 border-blue-500"
                : "text-zinc-600 border-transparent hover:text-zinc-400"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 0 && <VideoAnalysis />}
        {activeTab === 1 && <LiveCameraTest />}
        {activeTab === 2 && <ThresholdTuning />}
        {activeTab === 3 && <PerformanceTab />}
      </div>
    </>
  );
}

function VideoAnalysis() {
  const [file, setFile] = useState(null);
  const [video, setVideo] = useState(null);
  const [results, setResults] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({ sample_every_n_frames: 10, max_samples: 50 });
  const [previewMode, setPreviewMode] = useState("raw");
  const fileRef = useRef();

  function addLog(level, msg) {
    const ts = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { ts, level, msg }]);
  }

  async function handleUpload() {
    if (!file) return;
    addLog("info", `Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`);
    const v = await api.uploadVideo(file);
    setVideo(v);
    addLog("ok", `Upload complete — ID: ${v.id}`);
  }

  async function handleAnalyze() {
    if (!video) return;
    setAnalyzing(true);
    addLog("info", `Analysis started — ${config.max_samples} samples @ every ${config.sample_every_n_frames} frames`);
    try {
      const r = await api.analyzeVideo(video.id, config);
      setResults(r);
      addLog("ok", `Analysis complete — ${r.frames_analyzed}/${r.frames_total} frames`);
    } catch (err) {
      addLog("err", `Analysis failed: ${err.message}`);
    }
    setAnalyzing(false);
  }

  return (
    <div className="flex h-full">
      {/* Left: Controls */}
      <div className="w-1/2 border-r border-zinc-800/60 p-4 overflow-y-auto space-y-5">
        <Section title="Upload Video">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-zinc-800 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500/50 transition-colors"
          >
            <div className="text-2xl text-zinc-600 mb-2">&#128206;</div>
            <div className="text-[11px] text-zinc-500">{file ? file.name : "Drop video or click to browse"}</div>
            <div className="text-[9px] text-zinc-700 mt-1">MP4, AVI, MOV</div>
            <input ref={fileRef} type="file" accept="video/*" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
          </div>
          {file && !video && (
            <button onClick={handleUpload} className="mt-2 w-full py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25">
              Upload
            </button>
          )}
        </Section>

        {video && (
          <Section title="Analysis Configuration">
            <ConfigRow label="Sample every N frames" value={config.sample_every_n_frames} onChange={(v) => setConfig((c) => ({ ...c, sample_every_n_frames: parseInt(v) }))} />
            <ConfigRow label="Max samples" value={config.max_samples} onChange={(v) => setConfig((c) => ({ ...c, max_samples: parseInt(v) }))} />
            <button onClick={handleAnalyze} disabled={analyzing} className="mt-3 w-full py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25 disabled:opacity-50">
              {analyzing ? "Analyzing..." : "Run Analysis"}
            </button>
          </Section>
        )}

        <Section title="Execution Log">
          <div className="bg-[#0c0c0f] border border-zinc-800/60 rounded-lg p-2.5 font-mono text-[9px] leading-relaxed max-h-40 overflow-y-auto">
            {logs.map((l, i) => (
              <div key={i}>
                <span className="text-zinc-700">[{l.ts}]</span>{" "}
                <span className={logColor(l.level)}>{l.level.toUpperCase()}</span>{" "}
                <span className="text-zinc-500">{l.msg}</span>
              </div>
            ))}
            {logs.length === 0 && <span className="text-zinc-700">Waiting for activity...</span>}
          </div>
        </Section>
      </div>

      {/* Right: Preview & Results */}
      <div className="w-1/2 p-4 overflow-y-auto space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-xs font-semibold text-zinc-100">Preview</h3>
          <div className="flex gap-1">
            {["raw", "annotated"].map((mode) => (
              <button
                key={mode}
                onClick={() => setPreviewMode(mode)}
                className={`px-2.5 py-1 rounded-md border text-[9px] capitalize ${
                  previewMode === mode
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    : "text-zinc-600 border-zinc-800"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video flex items-center justify-center overflow-hidden">
          {video ? (
            <img src={api.videoStreamUrl(video.id, previewMode === "annotated")} alt="Preview" className="w-full h-full object-contain" />
          ) : (
            <span className="text-[10px] text-zinc-700">Upload a video to preview</span>
          )}
        </div>

        {results && (
          <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
            <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Detection Summary</h4>
            <ResultRow label="Frames analyzed" value={`${results.frames_analyzed} / ${results.frames_total}`} />
            {summarizeResults(results.results).map(({ key, count }) => (
              <ResultRow key={key} label={`${key} detections`} value={`${count}`} variant={count > 0 ? "danger" : "ok"} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function LiveCameraTest() {
  const [cameras, setCameras] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    api.listCameras().then((data) => setCameras(data.results || data));
  }, []);

  return (
    <div className="p-5 space-y-4">
      <Section title="Select Camera">
        <div className="flex gap-2 flex-wrap">
          {cameras.map((cam) => (
            <button
              key={cam.id}
              onClick={() => setSelectedId(cam.id)}
              className={`px-3 py-1.5 rounded-lg border text-[10px] ${
                selectedId === cam.id
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                  : "text-zinc-500 border-zinc-800"
              }`}
            >
              {cam.name}
            </button>
          ))}
        </div>
      </Section>
      {selectedId && (
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video overflow-hidden">
          <img src={api.cameraStreamUrl(selectedId, true)} alt="Live test" className="w-full h-full object-contain" />
        </div>
      )}
    </div>
  );
}

function ThresholdTuning() {
  const [thresholds, setThresholds] = useState(null);

  useEffect(() => {
    api.getThresholds().then(setThresholds);
  }, []);

  async function handleChange(key, value) {
    const updated = { ...thresholds, [key]: value };
    setThresholds(updated);
    await api.updateThresholds({ [key]: value });
  }

  if (!thresholds) return <div className="p-5 text-zinc-600 text-xs">Loading...</div>;

  return (
    <div className="p-5 max-w-lg space-y-5">
      <Section title="Detection Thresholds">
        <Slider label="Confidence threshold" value={thresholds.confidence} min={0} max={1} step={0.01} onChange={(v) => handleChange("confidence", v)} />
        <Slider label="Fatigue consecutive frames" value={thresholds.fatigue_consecutive_frames} min={1} max={30} step={1} onChange={(v) => handleChange("fatigue_consecutive_frames", v)} />
        <Slider label="EAR threshold" value={thresholds.ear_threshold} min={0} max={0.5} step={0.01} onChange={(v) => handleChange("ear_threshold", v)} />
        <Slider label="MAR threshold" value={thresholds.mar_threshold} min={0} max={1} step={0.01} onChange={(v) => handleChange("mar_threshold", v)} />
        <Slider label="Head tilt degrees" value={thresholds.head_tilt_degrees} min={5} max={45} step={0.5} onChange={(v) => handleChange("head_tilt_degrees", v)} />
      </Section>
    </div>
  );
}

function PerformanceTab() {
  const [perf, setPerf] = useState(null);

  useEffect(() => {
    loadPerf();
    const interval = setInterval(loadPerf, 2000);
    return () => clearInterval(interval);
  }, []);

  function loadPerf() {
    api.getPerformance().then(setPerf).catch(() => {});
  }

  if (!perf) return <div className="p-5 text-zinc-600 text-xs">Loading...</div>;

  return (
    <div className="p-5">
      <div className="grid grid-cols-2 gap-3 max-w-md">
        <PerfCard label="CPU Usage" value={`${perf.cpu_percent}%`} good={perf.cpu_percent < 80} />
        <PerfCard label="Memory" value={`${perf.memory_mb}MB`} good={perf.memory_mb < 4000} />
        <PerfCard label="GPU Available" value={perf.gpu_available ? "Yes" : "No"} good={perf.gpu_available} />
        <PerfCard label="GPU Usage" value={perf.gpu_percent >= 0 ? `${perf.gpu_percent}%` : "N/A"} good={perf.gpu_percent < 80} />
      </div>
    </div>
  );
}

// ---- Shared sub-components ----

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-zinc-100 mb-2.5">{title}</h3>
      {children}
    </div>
  );
}

function ConfigRow({ label, value, onChange }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
      <span className="text-[10px] text-zinc-400">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-20 text-center bg-surface-alt border border-zinc-800 rounded-md px-2 py-1 text-[10px] text-zinc-400 font-mono"
      />
    </div>
  );
}

function Slider({ label, value, min, max, step, onChange }) {
  return (
    <div className="py-2.5">
      <div className="flex justify-between text-[10px] mb-1.5">
        <span className="text-zinc-400">{label}</span>
        <span className="text-blue-400 font-mono">{typeof value === "number" ? value.toFixed(step < 1 ? 2 : 0) : value}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1 bg-zinc-800 rounded-full appearance-none cursor-pointer accent-blue-500"
      />
    </div>
  );
}

function ResultRow({ label, value, variant }) {
  const color = variant === "danger" ? "text-red-400" : variant === "ok" ? "text-green-400" : "text-zinc-400";
  return (
    <div className="flex justify-between py-1 text-[10px]">
      <span className="text-zinc-500">{label}</span>
      <span className={`font-mono ${color}`}>{value}</span>
    </div>
  );
}

function PerfCard({ label, value, good }) {
  return (
    <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3 text-center">
      <div className={`text-xl font-bold font-mono ${good ? "text-green-400" : "text-amber-400"}`}>{value}</div>
      <div className="text-[9px] text-zinc-600 uppercase tracking-wider mt-0.5">{label}</div>
    </div>
  );
}

function logColor(level) {
  return { info: "text-blue-500", ok: "text-green-500", warn: "text-amber-500", err: "text-red-500" }[level] || "text-zinc-500";
}

function summarizeResults(results) {
  const counts = {};
  (results || []).forEach((frame) => {
    Object.entries(frame.detections || {}).forEach(([key, det]) => {
      if (det.detected || (det.payload?.missing_count > 0)) {
        counts[key] = (counts[key] || 0) + 1;
      }
    });
  });
  return Object.entries(counts).map(([key, count]) => ({ key, count }));
}
