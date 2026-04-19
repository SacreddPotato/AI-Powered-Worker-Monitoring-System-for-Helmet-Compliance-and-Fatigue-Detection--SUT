import { useEffect, useRef, useState } from "react";

/**
 * Connect to a camera's WebSocket stream and return a blob URL for the
 * latest frame.  The blob URL is revoked automatically when a new frame
 * arrives or the hook unmounts.
 *
 * @param {number|null} cameraId  Camera PK (null to disconnect)
 * @param {string[]|undefined|null} overlays  Model keys for annotation overlays; omit/null for all
 * @returns {{ src: string|null, status: "connecting"|"live"|"error" }}
 */
export default function useCameraStream(cameraId, overlays = null) {
  const [src, setSrc] = useState(null);
  const [status, setStatus] = useState("connecting");
  const wsRef = useRef(null);
  const prevBlobRef = useRef(null);
  const reconnectRef = useRef(null);

  useEffect(() => {
    if (cameraId == null) {
      setStatus("error");
      return;
    }

    let disposed = false;

    function connect() {
      if (disposed) return;
      setStatus("connecting");

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const url = `${protocol}//${window.location.host}/ws/cameras/${cameraId}/stream/`;
      const ws = new WebSocket(url);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        if (disposed) { ws.close(); return; }
        setStatus("live");
        // Send overlay configuration only when explicitly provided.
        if (Array.isArray(overlays)) {
          ws.send(JSON.stringify({ overlays }));
        }
      };

      ws.onmessage = (e) => {
        if (disposed) return;
        // Revoke previous blob to avoid memory leaks
        if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current);

        const blob = new Blob([e.data], { type: "image/jpeg" });
        const blobUrl = URL.createObjectURL(blob);
        prevBlobRef.current = blobUrl;
        setSrc(blobUrl);
        setStatus("live");
      };

      ws.onclose = () => {
        if (disposed) return;
        setStatus("error");
        // Auto-reconnect after 2 seconds
        reconnectRef.current = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (prevBlobRef.current) {
        URL.revokeObjectURL(prevBlobRef.current);
        prevBlobRef.current = null;
      }
      setSrc(null);
    };
  }, [cameraId]);

  // When overlays change, send updated config over the existing WS
  useEffect(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN && Array.isArray(overlays)) {
      ws.send(JSON.stringify({ overlays }));
    }
  }, [Array.isArray(overlays) ? overlays.join(",") : "__all__"]);

  return { src, status };
}
