import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = process.env.API_PROXY || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  appType: "spa",
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": api,
      "/health": api,
    },
  },
});
