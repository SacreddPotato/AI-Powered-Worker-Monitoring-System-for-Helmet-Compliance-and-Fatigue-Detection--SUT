import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

function jsonResponse(data, init = {}) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("api client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(jsonResponse({ ok: true }))));
    global.URL.createObjectURL = vi.fn(() => "blob:preview");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("calls camera CRUD endpoints", async () => {
    await api.listCameras();
    await api.createCamera({ name: "Gate", source_url: "0" });
    await api.updateCamera(7, { name: "Gate 2" });
    await api.deleteCamera(7);

    expect(fetch).toHaveBeenNthCalledWith(1, "/api/v1/cameras/", expect.objectContaining({ headers: expect.any(Object) }));
    expect(fetch).toHaveBeenNthCalledWith(2, "/api/v1/cameras/", expect.objectContaining({ method: "POST" }));
    expect(fetch).toHaveBeenNthCalledWith(3, "/api/v1/cameras/7/", expect.objectContaining({ method: "PUT" }));
    expect(fetch).toHaveBeenNthCalledWith(4, "/api/v1/cameras/7/", expect.objectContaining({ method: "DELETE" }));
  });

  it("calls model, alert, detection, and threshold endpoints", async () => {
    await api.listModels();
    await api.updateModel("helmet", { enabled: false });
    await api.updateCameraModel(3, "helmet", { enabled: true });
    await api.listAlerts({ status: "open" });
    await api.acknowledgeAlert(9);
    await api.analyze(3);
    await api.getThresholds();
    await api.updateThresholds({ confidence: 0.5 });

    expect(fetch).toHaveBeenCalledWith("/api/v1/models/", expect.any(Object));
    expect(fetch).toHaveBeenCalledWith("/api/v1/models/helmet/", expect.objectContaining({ method: "PUT" }));
    expect(fetch).toHaveBeenCalledWith("/api/v1/cameras/3/models/helmet/", expect.objectContaining({ method: "PUT" }));
    expect(fetch).toHaveBeenCalledWith("/api/v1/alerts/?status=open", expect.any(Object));
    expect(fetch).toHaveBeenCalledWith("/api/v1/alerts/9/acknowledge/", expect.objectContaining({ method: "PATCH" }));
    expect(fetch).toHaveBeenCalledWith("/api/v1/detections/analyze/", expect.objectContaining({ method: "POST" }));
    expect(fetch).toHaveBeenCalledWith("/api/v1/dev/thresholds/", expect.any(Object));
    expect(fetch).toHaveBeenCalledWith("/api/v1/dev/thresholds/", expect.objectContaining({ method: "PUT" }));
  });

  it("builds stream URLs with overlays", () => {
    expect(api.cameraStreamUrl(4, ["helmet", "fatigue"])).toContain("/api/v1/cameras/4/stream/");
    expect(api.cameraStreamUrl(4, ["helmet", "fatigue"])).toContain("annotated=1");
    expect(api.cameraStreamUrl(4, ["helmet", "fatigue"])).toContain("overlays=helmet%2Cfatigue");

    expect(api.videoStreamUrl(8, ["vest"])).toContain("/api/v1/dev/videos/8/stream/");
    expect(api.videoFileUrl(8)).toContain("/api/v1/dev/videos/8/file/");
  });
});
