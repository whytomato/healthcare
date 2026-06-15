import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api/ai": {
        target: "http://localhost:8081",
        changeOrigin: true
      },
      "/api/triage": {
        target: "http://localhost:8082",
        changeOrigin: true
      },
      "/api/records": {
        target: "http://localhost:8083",
        changeOrigin: true
      }
    }
  }
});
