import { defineConfig } from "vite";
import { execSync } from "child_process";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const commitHash = (() => {
  try {
    return execSync("git rev-parse --short HEAD").toString().trim();
  } catch {
    return "unknown";
  }
})();

export default defineConfig({
  define: {
    __COMMIT_HASH__: JSON.stringify(commitHash),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:7860",
      "/ws": {
        target: "ws://localhost:7860",
        ws: true,
      },
    },
  },
});
