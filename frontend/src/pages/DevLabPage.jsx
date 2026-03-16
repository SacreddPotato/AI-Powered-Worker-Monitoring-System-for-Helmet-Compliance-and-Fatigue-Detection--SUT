import { useState, useEffect, useRef } from "react";
import { api } from "../api";
import Toggle from "../components/Toggle";

const TABS = ["Video Analysis", "Live Camera Test", "Threshold Tuning"];
const ALL_MODELS = ["helmet", "fatigue", "vest", "gloves", "goggles"];

export default function DevLabPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [visited, setVisited] = useState(new Set([0]));

  function switchTab(i) {
    setActiveTab(i);
    setVisited((prev) => {
      if (prev.has(i)) return prev;
      const next = new Set(prev);
      next.add(i);
      return next;
    });
  }

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Developer Lab</h1>
          <span className="text-xs text-zinc-600">Testing & debugging</span>
        </div>
        <span className="text-[9px] font-mono text-zinc-700 select-all" title={`Built ${__BUILD_TIME__}`}>
          {__COMMIT_HASH__}
        </span>
      </div>

      <div className="flex border-b border-zinc-800/60 px-5 shrink-0">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => switchTab(i)}
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

      {/* Tab panels stay mounted (hidden via CSS) so streams aren't killed */}
      <div className="flex-1 overflow-hidden relative">
        {visited.has(0) && (
          <div className={`h-full ${activeTab === 0 ? "" : "hidden"}`}>
            <VideoAnalysis />
          </div>
        )}
        {visited.has(1) && (
          <div className={`h-full ${activeTab === 1 ? "" : "hidden"}`}>
            <LiveCameraTest />
          </div>
        )}
        {visited.has(2) && (
          <div className={`h-full ${activeTab === 2 ? "" : "hidden"}`}>
            <ThresholdTuning />
          </div>
        )}

        {/* Floating performance monitor — always visible */}
        <PerfMonitor />
      </div>
    </>
  );
}

// ============================================================
// Client-side canvas annotation drawing
// ============================================================

const ANNO_COLORS = {
  helmet: "rgb(80,200,0)",
  fatigue: "rgb(255,140,0)",
  vest: "rgb(50,160,255)",
  gloves: "rgb(255,220,0)",
  goggles: "rgb(0,200,220)",
  red: "rgb(255,60,0)",
  green: "rgb(80,200,0)",
  blue: "rgb(50,160,255)",
  yellow: "rgb(255,220,0)",
  cyan: "rgb(0,200,220)",
  orange: "rgb(255,140,0)",
  white: "rgb(255,255,255)",
};

function drawPPEBoxes(ctx, payload, modelKey, tx, ty, s) {
  const defaultColor = ANNO_COLORS[modelKey] || ANNO_COLORS.white;
  for (const box of payload.boxes || []) {
    const x1 = tx(box.x1), y1 = ty(box.y1);
    const x2 = tx(box.x2), y2 = ty(box.y2);
    const label = box.label || modelKey;
    const color = ANNO_COLORS[box.color] || defaultColor;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    const fontSize = Math.max(10, Math.round(12 * s));
    ctx.font = `bold ${fontSize}px sans-serif`;
    const tm = ctx.measureText(label);
    const lh = fontSize + 4;
    ctx.fillStyle = color;
    ctx.fillRect(x1, y1 - lh, tm.width + 8, lh);
    ctx.fillStyle = "#000";
    ctx.fillText(label, x1 + 4, y1 - 3);
  }
}

function drawFatigue(ctx, payload, tx, ty, s) {
  const color = ANNO_COLORS.fatigue;
  const isFatigued = payload.is_fatigued;
  const boxColor = isFatigued ? ANNO_COLORS.red : color;
  const faceBox = payload.face_box;

  if (faceBox) {
    const x1 = tx(faceBox.x1), y1 = ty(faceBox.y1);
    const x2 = tx(faceBox.x2), y2 = ty(faceBox.y2);
    ctx.strokeStyle = boxColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    const hybrid = payload.hybrid_score || 0;
    const tag = isFatigued ? "FATIGUED" : "Alert";
    const label = `${tag} (${Math.round(hybrid * 100)}%)`;
    const fontSize = Math.max(10, Math.round(12 * s));
    ctx.font = `bold ${fontSize}px sans-serif`;
    const tm = ctx.measureText(label);
    const lh = fontSize + 4;
    ctx.fillStyle = boxColor;
    ctx.fillRect(x1, y1 - lh, tm.width + 8, lh);
    ctx.fillStyle = "#000";
    ctx.fillText(label, x1 + 4, y1 - 3);
  }

  ctx.fillStyle = color;
  for (const pt of payload.landmarks || []) {
    if (pt.length >= 2) {
      ctx.beginPath();
      ctx.arc(tx(pt[0]), ty(pt[1]), Math.max(1, 1.5 * s), 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const pose = payload.pose_line;
  if (pose) {
    const sx = tx(pose.start[0]), sy = ty(pose.start[1]);
    const ex = tx(pose.end[0]), ey = ty(pose.end[1]);
    ctx.strokeStyle = ANNO_COLORS.cyan;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(ex, ey);
    ctx.stroke();
    const angle = Math.atan2(ey - sy, ex - sx);
    const tipLen = 8 * s;
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - tipLen * Math.cos(angle - 0.4), ey - tipLen * Math.sin(angle - 0.4));
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - tipLen * Math.cos(angle + 0.4), ey - tipLen * Math.sin(angle + 0.4));
    ctx.stroke();
  }

  if (faceBox) {
    const lines = [];
    if (payload.ear != null) lines.push(`EAR ${payload.ear.toFixed(2)}`);
    if (payload.mar != null) lines.push(`MAR ${payload.mar.toFixed(2)}`);
    if (payload.head_tilt_degrees != null) lines.push(`Tilt ${payload.head_tilt_degrees.toFixed(1)}`);
    const mfs = Math.max(9, Math.round(11 * s));
    ctx.font = `${mfs}px monospace`;
    ctx.fillStyle = color;
    const xT = tx(faceBox.x2) + 5;
    let yT = ty(faceBox.y1) + 14 * s;
    for (const txt of lines) {
      ctx.fillText(txt, xT, yT);
      yT += 16 * s;
    }
  }
}

// ============================================================
// Video Analysis — live WebSocket streaming
// ============================================================

function VideoAnalysis() {
  const [file, setFile] = useState(null);
  const [localUrl, setLocalUrl] = useState(null);
  const [video, setVideo] = useState(null);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [overlays, setOverlays] = useState([...ALL_MODELS]);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({ sample_every_n_frames: 3 });
  const [videoDone, setVideoDone] = useState(false);

  const fileRef = useRef();
  const videoRef = useRef();
  const canvasRef = useRef();
  const animRef = useRef();
  const wsRef = useRef(null);
  const overlaysRef = useRef(overlays);

  // Live analysis data stored in refs (updated by WS, read by draw loop)
  const frameMapRef = useRef(new Map());
  const sortedFramesRef = useRef([]);
  const fpsRef = useRef(30);
  const runningRef = useRef(false);
  const analysisDoneRef = useRef(false);
  const playbarRef = useRef();

  useEffect(() => { overlaysRef.current = overlays; }, [overlays]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      stopDrawLoop();
    };
  }, []);

  function addLog(level, msg) {
    const ts = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { ts, level, msg }]);
  }

  function toggleOverlay(key) {
    setOverlays((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

  function stopDrawLoop() {
    if (animRef.current) {
      cancelAnimationFrame(animRef.current);
      animRef.current = null;
    }
    const c = canvasRef.current;
    if (c) c.getContext("2d").clearRect(0, 0, c.width, c.height);
  }

  function handleFileSelect(e) {
    const f = e.target.files[0];
    if (!f) return;
    handleStop();
    setFile(f);
    setVideo(null);
    setAnalysisData(null);
    setProgress(null);
    setVideoDone(false);
    frameMapRef.current.clear();
    sortedFramesRef.current = [];
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

  function handleStart() {
    if (!video) return;

    // Reset previous analysis
    frameMapRef.current.clear();
    sortedFramesRef.current = [];
    setAnalysisData(null);
    setProgress({ analyzed: 0, total: 0 });
    setVideoDone(false);
    setRunning(true);
    runningRef.current = true;
    analysisDoneRef.current = false;
    stopDrawLoop();

    // Close any existing socket
    if (wsRef.current) wsRef.current.close();

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/video-analysis/`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: "start",
        video_id: video.id,
        sample_every_n_frames: config.sample_every_n_frames,
      }));
      addLog("info", `Live analysis started — sampling every ${config.sample_every_n_frames} frames`);
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === "init") {
        fpsRef.current = data.fps;
        setProgress((p) => ({ ...p, total: data.total_frames }));
        addLog("info", `${data.total_frames} frames @ ${data.fps} FPS — models: ${data.enabled_models.join(", ")}`);
        // Video stays paused — draw loop sync will play it once buffer is ready
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
        }
        startDrawLoop();
      }

      if (data.type === "frame") {
        frameMapRef.current.set(data.frame, data.detections);
        sortedFramesRef.current.push(data.frame);
        setProgress((p) => ({ ...p, analyzed: (p?.analyzed || 0) + 1 }));

        // Resume video if paused and we have >= 1 second of buffer ahead
        const vid = videoRef.current;
        if (vid && vid.paused && !vid.ended) {
          const bufferAhead = (data.frame / fpsRef.current) - vid.currentTime;
          if (bufferAhead >= 1.0) {
            vid.play();
          }
        }
      }

      if (data.type === "done") {
        analysisDoneRef.current = true;
        // All frames analyzed — let video play freely to the end
        const vid = videoRef.current;
        if (vid && vid.paused && !vid.ended) vid.play();

        const results = sortedFramesRef.current.map((f) => ({
          frame: f,
          detections: frameMapRef.current.get(f),
        }));
        setAnalysisData({
          fps: fpsRef.current,
          frames_total: data.frames_total,
          frames_analyzed: data.frames_analyzed,
          results,
        });
        setRunning(false);
        runningRef.current = false;
        addLog("ok", `Complete — ${data.frames_analyzed}/${data.frames_total} frames analyzed`);
      }

      if (data.type === "error") {
        setRunning(false);
        runningRef.current = false;
        addLog("err", `Analysis error: ${data.message}`);
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    ws.onerror = () => {
      setRunning(false);
      addLog("err", "WebSocket connection failed");
    };
  }

  function handleStop() {
    if (wsRef.current) {
      try { wsRef.current.send(JSON.stringify({ action: "stop" })); } catch {}
      wsRef.current.close();
      wsRef.current = null;
    }
    if (videoRef.current) videoRef.current.pause();
    setRunning(false);
    runningRef.current = false;
    addLog("info", "Analysis stopped");
  }

  function handleRestart() {
    setVideoDone(false);
    handleStart();
  }

  // --- Canvas draw loop ---
  function startDrawLoop() {
    stopDrawLoop();
    const vid = videoRef.current;
    const canvas = canvasRef.current;
    if (!vid || !canvas) return;
    const ctx = canvas.getContext("2d");

    function draw() {
      const rect = canvas.getBoundingClientRect();
      const w = Math.round(rect.width);
      const h = Math.round(rect.height);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update playback position bar
      if (playbarRef.current && vid.duration) {
        playbarRef.current.style.width = `${(vid.currentTime / vid.duration) * 100}%`;
      }

      const vW = vid.videoWidth;
      const vH = vid.videoHeight;
      if (vW && vH) {
        const fps = fpsRef.current;
        const currentFrame = Math.floor(vid.currentTime * fps);

        // --- SYNC: pause video if it has caught up to the analysis frontier ---
        if (runningRef.current && !analysisDoneRef.current) {
          const frames = sortedFramesRef.current;
          if (frames.length > 0) {
            const latestAnalyzedTime = frames[frames.length - 1] / fps;
            const bufferAhead = latestAnalyzedTime - vid.currentTime;
            if (!vid.paused && bufferAhead < 0.15) {
              vid.pause();
            }
          }
        }

        const nearest = findNearest(sortedFramesRef.current, currentFrame);

        if (nearest !== null) {
          const detections = frameMapRef.current.get(nearest);
          if (detections) {
            const scale = Math.min(canvas.width / vW, canvas.height / vH);
            const offX = (canvas.width - vW * scale) / 2;
            const offY = (canvas.height - vH * scale) / 2;
            const tx = (x) => offX + x * scale;
            const ty = (y) => offY + y * scale;

            const active = overlaysRef.current;
            for (const [key, det] of Object.entries(detections)) {
              if (!active.includes(key)) continue;
              if (det.status !== "ok") continue;
              const payload = det.payload || {};
              if (key === "fatigue") drawFatigue(ctx, payload, tx, ty, scale);
              else drawPPEBoxes(ctx, payload, key, tx, ty, scale);
            }
          }
        }
      }

      animRef.current = requestAnimationFrame(draw);
    }

    animRef.current = requestAnimationFrame(draw);
  }

  // Track video end
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;
    const onEnd = () => setVideoDone(true);
    const onPlay = () => setVideoDone(false);
    vid.addEventListener("ended", onEnd);
    vid.addEventListener("play", onPlay);
    return () => {
      vid.removeEventListener("ended", onEnd);
      vid.removeEventListener("play", onPlay);
    };
  }, [video]);

  const pct = progress && progress.total > 0
    ? Math.round((progress.analyzed / (progress.total / config.sample_every_n_frames)) * 100)
    : 0;

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
              <div className="space-y-2">
                <ConfigRow label="Sample every N frames" value={config.sample_every_n_frames} onChange={(v) => setConfig((c) => ({ ...c, sample_every_n_frames: parseInt(v) || 1 }))} />
                {!running ? (
                  <button
                    onClick={handleStart}
                    className="w-full py-2.5 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25"
                  >
                    Play & Analyze Live
                  </button>
                ) : (
                  <button
                    onClick={handleStop}
                    className="w-full py-2.5 rounded-lg bg-red-500/15 text-red-400 text-[10px] font-semibold hover:bg-red-500/25"
                  >
                    Stop Analysis
                  </button>
                )}
              </div>
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

      {/* Right: Video with canvas overlay */}
      <div className="w-1/2 p-4 overflow-y-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-zinc-100">
            {running ? "Live Analysis" : analysisData ? "Analysis Complete" : "Video Preview"}
            {running && <span className="ml-2 text-[9px] text-red-400 animate-pulse">LIVE</span>}
          </h3>
          {running && progress && (
            <span className="text-[9px] text-zinc-500 font-mono">
              {progress.analyzed} frames analyzed{progress.total > 0 ? ` · ${Math.min(pct, 100)}%` : ""}
            </span>
          )}
        </div>

        {/* Progress bar */}
        {running && progress && progress.total > 0 && (
          <div className="h-0.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
        )}

        <div className="relative bg-surface-alt border border-zinc-800 rounded-lg aspect-video overflow-hidden">
          {localUrl || video ? (
            <>
              <video
                ref={videoRef}
                src={video ? api.videoFileUrl(video.id) : localUrl}
                className="w-full h-full object-contain"
              />
              <canvas
                ref={canvasRef}
                className="absolute inset-0 w-full h-full pointer-events-none"
              />
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <span className="text-[10px] text-zinc-700">Select a video to preview</span>
            </div>
          )}

          {videoDone && !running && (
            <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3">
              <span className="text-[11px] text-zinc-300">Playback complete</span>
              <button
                onClick={handleRestart}
                className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 text-[10px] font-semibold border border-blue-500/30 hover:bg-blue-500/30"
              >
                Restart Analysis
              </button>
            </div>
          )}
        </div>

        {/* Playback position bar (driven by draw loop, no re-renders) */}
        {(running || analysisData) && (
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div ref={playbarRef} className="h-full bg-blue-500 transition-[width] duration-150" style={{ width: 0 }} />
          </div>
        )}

        {analysisData && (
          <>
            <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
              <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Detection Summary</h4>
              <ResultRow label="Frames analyzed" value={`${analysisData.frames_analyzed} / ${analysisData.frames_total}`} />
              <ResultRow label="Video FPS" value={analysisData.fps} />
              {summarizeResults(analysisData.results).map(({ key, count }) => (
                <ResultRow key={key} label={`${key} detections`} value={`${count} frames`} variant={count > 0 ? "danger" : "ok"} />
              ))}
              {summarizeResults(analysisData.results).length === 0 && (
                <ResultRow label="No detections" value="All clear" variant="ok" />
              )}
            </div>

            <div className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
              <h4 className="text-[11px] font-semibold text-zinc-100 mb-2">Per-Frame Results</h4>
              <div className="max-h-48 overflow-y-auto space-y-1">
                {analysisData.results.map((fr) => (
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

// Binary search: find nearest analyzed frame <= target
function findNearest(sortedFrames, target) {
  if (sortedFrames.length === 0) return null;
  let lo = 0, hi = sortedFrames.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (sortedFrames[mid] <= target) lo = mid;
    else hi = mid - 1;
  }
  return sortedFrames[lo] <= target ? sortedFrames[lo] : null;
}

// ============================================================
// Live Camera Test
// ============================================================

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

// ============================================================
// Threshold Tuning
// ============================================================

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

// ============================================================
// Floating Performance Monitor
// ============================================================

function PerfMonitor() {
  const [open, setOpen] = useState(false);
  const [perf, setPerf] = useState(null);

  useEffect(() => {
    loadPerf();
    const interval = setInterval(loadPerf, 3000);
    return () => clearInterval(interval);
  }, []);

  function loadPerf() {
    api.getPerformance().then(setPerf).catch(() => {});
  }

  if (!perf) return null;

  return (
    <div className="absolute bottom-3 right-3 z-30">
      {open ? (
        <div className="bg-[#0c0c0f]/95 backdrop-blur border border-zinc-800 rounded-lg p-3 w-56 animate-slide-in">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[9px] text-zinc-500 uppercase tracking-wider font-semibold">System</span>
            <button onClick={() => setOpen(false)} className="text-zinc-600 hover:text-zinc-400 text-[10px]">
              <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="4" x2="12" y2="12" /><line x1="12" y1="4" x2="4" y2="12" /></svg>
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <MiniStat label="CPU" value={`${perf.cpu_percent}%`} good={perf.cpu_percent < 80} />
            <MiniStat label="RAM" value={`${perf.memory_mb}MB`} good={perf.memory_mb < 4000} />
            <MiniStat label="GPU" value={perf.gpu_percent >= 0 ? `${perf.gpu_percent}%` : perf.gpu_available ? "idle" : "N/A"} good={perf.gpu_available && perf.gpu_percent < 80} />
            <MiniStat label="VRAM" value={perf.gpu_mem_used_mb > 0 ? `${perf.gpu_mem_used_mb}/${perf.gpu_mem_total_mb}` : "N/A"} good={perf.gpu_available} />
          </div>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 bg-[#0c0c0f]/90 backdrop-blur border border-zinc-800 rounded-lg px-3 py-1.5 hover:border-zinc-700 transition-colors"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${perf.cpu_percent < 80 ? "bg-green-500" : "bg-amber-500"}`} />
          <span className="text-[9px] text-zinc-500 font-mono">
            CPU {perf.cpu_percent}%{perf.gpu_percent >= 0 ? ` · GPU ${perf.gpu_percent}%` : ""} · {perf.memory_mb}MB
          </span>
        </button>
      )}
    </div>
  );
}

function MiniStat({ label, value, good }) {
  return (
    <div className="text-center">
      <div className={`text-sm font-bold font-mono ${good ? "text-green-400" : "text-amber-400"}`}>{value}</div>
      <div className="text-[8px] text-zinc-600 uppercase">{label}</div>
    </div>
  );
}

// ============================================================
// Shared sub-components
// ============================================================

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
