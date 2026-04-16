const BASE = "/api/v1";

// MJPEG streams must bypass the Vite dev proxy which buffers the entire
// multipart response (frames arrive all at once instead of streaming).
// In production the frontend is served by Django, so same-origin works.
const STREAM_BASE = import.meta.env.DEV
  ? `http://${window.location.hostname}:7860/api/v1`
  : "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
<<<<<<< HEAD
  if (res.status === 204 || res.headers.get("content-length") === "0") return null;
  const text = await res.text();
  return text ? JSON.parse(text) : null;
=======
  return res.json();
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
}

export const api = {
  // Cameras
  listCameras: () => request("/cameras/"),
  createCamera: (data) => request("/cameras/", { method: "POST", body: JSON.stringify(data) }),
  updateCamera: (id, data) => request(`/cameras/${id}/`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCamera: (id) => request(`/cameras/${id}/`, { method: "DELETE" }),
  cameraStatus: (id) => request(`/cameras/${id}/status/`),
  discoverDevices: () => request("/cameras/discover/"),
<<<<<<< HEAD
  probeSource: async (source_url) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const res = await fetch(`${BASE}/cameras/probe/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_url }),
        signal: controller.signal,
      });

      if (!res.ok) {
        let message = `Probe failed (${res.status})`;
        try {
          const data = await res.json();
          if (data?.error) message = data.error;
        } catch {
        }
        return { ok: false, error: message, status: res.status };
      }

      const blob = await res.blob();
      return { ok: true, url: URL.createObjectURL(blob), error: null, status: res.status };
    } catch (err) {
      if (err?.name === "AbortError") {
        return { ok: false, error: "Probe timed out. Check camera IP/port and stream path.", status: 408 };
      }
      return { ok: false, error: "Probe request failed", status: 0 };
    } finally {
      clearTimeout(timer);
    }
  },
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

  cameraStreamUrl: (id, overlays = []) => {
    const params = new URLSearchParams();
    if (overlays.length > 0) {
      params.set("annotated", "1");
      params.set("overlays", overlays.join(","));
    }
    const qs = params.toString();
    return `${STREAM_BASE}/cameras/${id}/stream/${qs ? "?" + qs : ""}`;
  },

  // Models
  listModels: () => request("/models/"),
  updateModel: (key, data) => request(`/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),
  listCameraModels: (camId) => request(`/cameras/${camId}/models/`),
<<<<<<< HEAD
  listCameraModelsBulk: () => request("/cameras/models/overrides/"),
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
  updateCameraModel: (camId, key, data) => request(`/cameras/${camId}/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),

  // Alerts
  listAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/alerts/${qs ? "?" + qs : ""}`);
  },
  acknowledgeAlert: (id) => request(`/alerts/${id}/acknowledge/`, { method: "PATCH" }),
<<<<<<< HEAD
  exportAlertsExcel: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${BASE}/alerts/export/excel/${qs ? "?" + qs : ""}`);
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match?.[1] || "alerts_by_camera.xlsx";
    return { blob, filename };
  },
  getAlertsChartData: (groupBy = "severity", params = {}) => {
    const query = new URLSearchParams({ group_by: groupBy, ...params }).toString();
    return request(`/alerts/export/chart-data/?${query}`);
  },
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

  // Detections
  analyze: (cameraId) => request("/detections/analyze/", { method: "POST", body: JSON.stringify({ camera_id: cameraId }) }),

  // Dev Lab
  uploadVideo: (file) => {
    const form = new FormData();
    form.append("video", file);
    return fetch(`${BASE}/dev/videos/`, { method: "POST", body: form }).then((r) => r.json());
  },
  listVideos: () => request("/dev/videos/"),
  videoFileUrl: (id) => `${STREAM_BASE}/dev/videos/${id}/file/`,

  videoStreamUrl: (id, overlays = []) => {
    const params = new URLSearchParams();
    if (overlays.length > 0) {
      params.set("annotated", "1");
      params.set("overlays", overlays.join(","));
    }
    const qs = params.toString();
    return `${STREAM_BASE}/dev/videos/${id}/stream/${qs ? "?" + qs : ""}`;
  },

  analyzeVideo: (id, opts) => request(`/dev/videos/${id}/analyze/`, { method: "POST", body: JSON.stringify(opts) }),
  getThresholds: () => request("/dev/thresholds/"),
  updateThresholds: (data) => request("/dev/thresholds/", { method: "PUT", body: JSON.stringify(data) }),
  getPerformance: () => request("/dev/performance/"),
};
