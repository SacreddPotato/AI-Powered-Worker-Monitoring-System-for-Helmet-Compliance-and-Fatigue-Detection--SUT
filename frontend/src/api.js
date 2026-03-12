const BASE = "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  // Cameras
  listCameras: () => request("/cameras/"),
  createCamera: (data) => request("/cameras/", { method: "POST", body: JSON.stringify(data) }),
  updateCamera: (id, data) => request(`/cameras/${id}/`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCamera: (id) => request(`/cameras/${id}/`, { method: "DELETE" }),
  cameraStatus: (id) => request(`/cameras/${id}/status/`),
  discoverDevices: () => request("/cameras/discover/"),

  /** Build MJPEG stream URL with optional annotation overlays.
   *  @param {number} id - camera id
   *  @param {string[]} overlays - model keys to draw, e.g. ['helmet','fatigue'] (empty = raw) */
  cameraStreamUrl: (id, overlays = []) => {
    const params = new URLSearchParams();
    if (overlays.length > 0) {
      params.set("annotated", "1");
      params.set("overlays", overlays.join(","));
    }
    const qs = params.toString();
    return `${BASE}/cameras/${id}/stream/${qs ? "?" + qs : ""}`;
  },

  // Models
  listModels: () => request("/models/"),
  updateModel: (key, data) => request(`/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),
  listCameraModels: (camId) => request(`/cameras/${camId}/models/`),
  updateCameraModel: (camId, key, data) => request(`/cameras/${camId}/models/${key}/`, { method: "PUT", body: JSON.stringify(data) }),

  // Alerts
  listAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/alerts/${qs ? "?" + qs : ""}`);
  },
  acknowledgeAlert: (id) => request(`/alerts/${id}/acknowledge/`, { method: "PATCH" }),

  // Detections
  analyze: (cameraId) => request("/detections/analyze/", { method: "POST", body: JSON.stringify({ camera_id: cameraId }) }),

  // Dev Lab
  uploadVideo: (file) => {
    const form = new FormData();
    form.append("video", file);
    return fetch(`${BASE}/dev/videos/`, { method: "POST", body: form }).then((r) => r.json());
  },
  listVideos: () => request("/dev/videos/"),
  videoFileUrl: (id) => `${BASE}/dev/videos/${id}/file/`,

  /** Build annotated MJPEG stream URL for a dev video.
   *  @param {number} id - video id
   *  @param {string[]} overlays - model keys (empty = raw stream) */
  videoStreamUrl: (id, overlays = []) => {
    const params = new URLSearchParams();
    if (overlays.length > 0) {
      params.set("annotated", "1");
      params.set("overlays", overlays.join(","));
    }
    const qs = params.toString();
    return `${BASE}/dev/videos/${id}/stream/${qs ? "?" + qs : ""}`;
  },

  analyzeVideo: (id, opts) => request(`/dev/videos/${id}/analyze/`, { method: "POST", body: JSON.stringify(opts) }),
  getThresholds: () => request("/dev/thresholds/"),
  updateThresholds: (data) => request("/dev/thresholds/", { method: "PUT", body: JSON.stringify(data) }),
  getPerformance: () => request("/dev/performance/"),
};
