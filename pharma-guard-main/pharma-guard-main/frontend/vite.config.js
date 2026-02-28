import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "https://pharmaguard-1-fp7v.onrender.com",
        changeOrigin: true,
      },
    },
  },
});
