import { useState, useEffect, useRef } from "react";
import { api } from "../api";
import Toggle from "../components/Toggle";

const TABS = ["Video Analysis", "Live Camera Test", "Threshold Tuning", "Performance"];
const ALL_MODELS = ["helmet", "fatigue", "vest", "gloves", "goggles"];

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
  const [localUrl, setLocalUrl] = useState(null);
  const [video, setVideo] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [streamActive, setStreamActive] = useState(false);
  const [results, setResults] = useState(null);
  const [overlays, setOverlays] = useState([...ALL_MODELS]);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({ sample_every_n_frames: 10, max_samples: 50 });
  const fileRef = useRef();
  const streamRef = useRef();

  function addLog(level, msg) {
    const ts = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { ts, level, msg }]);
  }

  function toggleOverlay(key) {
    setOverlays((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

  function handleFileSelect(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setVideo(null);
    setResults(null);
    setStreamActive(false);
    if (localUrl) URL.revokeObjectURL(localUrl);
    setLocalUrl(URL.createObjectURL(f));
  }

  async function handleUpload() {
    if (!file) return;
    addLog("info", `Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`);
    try {
      const v = await api.uploadVideo(file);
      setVideo(v);
      addLog("ok", `Upload complete — ID: ${v.id}, ${v.duration ? v.duration.toFixed(1) + "s" : "unknown duration"}`);
    } catch (err) {
      addLog("err", `Upload failed: ${err.message}`);
    }
  }

  function handleAnalyzeStream() {
    if (!video || overlays.length === 0) return;
    setStreamActive(true);
    setResults(null);
    addLog("info", `Streaming annotated analysis — overlays: ${overlays.join(", ")}`);
  }

  async function handleAnalyzeJson() {
    if (!video) return;
    setAnalyzing(true);
    setResults(null);
    addLog("info", `JSON analysis — ${config.max_samples} samples @ every ${config.sample_every_n_frames} frames`);
    try {
      const r = await api.analyzeVideo(video.id, config);
      setResults(r);
      addLog("ok", `Analysis complete — ${r.frames_analyzed}/${r.frames_total} frames`);
    } catch (err) {
      addLog("err", `Analysis failed: ${err.message}`);
    }
    setAnalyzing(false);
  }

  function handleStopStream() {
    setStreamActive(false);
    addLog("info", "Stream stopped");
  }

  // When stream img errors (connection closed = video ended), mark done
  function handleStreamEnd() {
    if (streamActive) {
      setStreamActive(false);
      addLog("ok", "Annotated stream complete");
    }
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
            <input ref={fileRef} type="file" accept="video/*" className="hidden" onChange={handleFileSelect} />
          </div>
          {file && !video && (
            <button onClick={handleUpload} className="mt-2 w-full py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25">
              Upload & Prepare for Analysis
            </button>
          )}
        </Section>

        {video && (
          <>
            <Section title="Annotation Overlays">
              <div className="flex flex-wrap gap-x-4 gap-y-2">
                {ALL_MODELS.map((key) => (
                  <label key={key} className="flex items-center gap-1.5 cursor-pointer select-none">
                    <Toggle enabled={overlays.includes(key)} onChange={() => toggleOverlay(key)} size="sm" />
                    <span className={`text-[10px] capitalize ${overlays.includes(key) ? "text-zinc-300" : "text-zinc-600"}`}>{key}</span>
                  </label>
                ))}
              </div>
            </Section>

            <Section title="Analysis">
              {!streamActive ? (
                <div className="space-y-2">
                  <button
                    onClick={handleAnalyzeStream}
                    disabled={overlays.length === 0}
                    className="w-full py-2.5 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25 disabled:opacity-40"
                  >
                    Stream with Annotations
                  </button>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-px bg-zinc-800" />
                    <span className="text-[8px] text-zinc-600 uppercase">or</span>
                    <div className="flex-1 h-px bg-zinc-800" />
                  </div>
                  <div className="space-y-2">
                    <ConfigRow label="Sample every N frames" value={config.sample_every_n_frames} onChange={(v) => setConfig((c) => ({ ...c, sample_every_n_frames: parseInt(v) || 1 }))} />
                    <ConfigRow label="Max samples" value={config.max_samples} onChange={(v) => setConfig((c) => ({ ...c, max_samples: parseInt(v) || 1 }))} />
                    <button
                      onClick={handleAnalyzeJson}
                      disabled={analyzing}
                      className="w-full py-2 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] font-semibold hover:bg-white/[0.02] disabled:opacity-40"
                    >
                      {analyzing ? "Analyzing..." : "Run JSON Analysis (sampled)"}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleStopStream}
                  className="w-full py-2.5 rounded-lg bg-red-500/15 text-red-400 text-[10px] font-semibold hover:bg-red-500/25"
                >
                  Stop Stream
                </button>
              )}
            </Section>
          </>
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
        <h3 className="text-xs font-semibold text-zinc-100">
          {streamActive ? "Annotated Stream" : "Video Preview"}
          {streamActive && <span className="ml-2 text-[9px] text-red-400 animate-pulse">ANALYZING</span>}
        </h3>
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video flex items-center justify-center overflow-hidden">
          {streamActive && video ? (
            /* Annotated MJPEG stream — bounding boxes drawn server-side */
            <img
              ref={streamRef}
              src={api.videoStreamUrl(video.id, overlays)}
              alt="Annotated analysis"
              className="w-full h-full object-contain"
              onError={handleStreamEnd}
            />
          ) : localUrl ? (
            <video
              src={video ? api.videoFileUrl(video.id) : localUrl}
              controls
              className="w-full h-full object-contain"
            />
          ) : (
            <span className="text-[10px] text-zinc-700">Select a video to preview</span>
          )}
        </div>

        {results && (
          <>
            <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
              <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Detection Summary</h4>
              <ResultRow label="Frames analyzed" value={`${results.frames_analyzed} / ${results.frames_total}`} />
              {summarizeResults(results.results).map(({ key, count, total }) => (
                <ResultRow key={key} label={`${key} detections`} value={`${count} / ${total} frames`} variant={count > 0 ? "danger" : "ok"} />
              ))}
              {summarizeResults(results.results).length === 0 && (
                <ResultRow label="No detections" value="All clear" variant="ok" />
              )}
            </div>

            <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
              <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Per-Frame Results</h4>
              <div className="max-h-48 overflow-y-auto space-y-1">
                {results.results.map((fr) => (
                  <div key={fr.frame} className="flex items-center gap-2 text-[9px] py-1 border-b border-zinc-800/40">
                    <span className="text-zinc-600 font-mono w-16 shrink-0">Frame {fr.frame}</span>
                    <div className="flex gap-1 flex-wrap">
                      {Object.entries(fr.detections || {}).map(([key, det]) => (
                        <span
                          key={key}
                          className={`px-1.5 py-0.5 rounded text-[8px] font-medium ${
                            det.detected
                              ? "bg-red-500/15 text-red-400"
                              : "bg-green-500/10 text-green-500"
                          }`}
                        >
                          {key}: {det.detected ? "detected" : "clear"}
                          {det.confidence != null ? ` (${(det.confidence * 100).toFixed(0)}%)` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function LiveCameraTest() {
  const [cameras, setCameras] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [overlays, setOverlays] = useState([...ALL_MODELS]);

  useEffect(() => {
    api.listCameras().then((data) => setCameras(data.results || data));
  }, []);

  function toggleOverlay(key) {
    setOverlays((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

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
      <Section title="Overlays">
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          {ALL_MODELS.map((key) => (
            <label key={key} className="flex items-center gap-1.5 cursor-pointer select-none">
              <Toggle enabled={overlays.includes(key)} onChange={() => toggleOverlay(key)} size="sm" />
              <span className={`text-[10px] capitalize ${overlays.includes(key) ? "text-zinc-300" : "text-zinc-600"}`}>{key}</span>
            </label>
          ))}
        </div>
      </Section>
      {selectedId && (
        <div className="bg-surface-alt border border-zinc-800 rounded-lg aspect-video overflow-hidden">
          <img src={api.cameraStreamUrl(selectedId, overlays)} alt="Live test" className="w-full h-full object-contain" />
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
