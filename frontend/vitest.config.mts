import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Mirrors the "@/*" -> "./src/*" mapping in tsconfig.json, which Vitest does
    // not read on its own.
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // The published client, resolved from source so the contract test
      // checks the code that gets published rather than a stale build.
      "ucip-client": fileURLToPath(
        new URL("../clients/typescript/src/index.ts", import.meta.url)
      ),
    },
  },
  test: {
    // .tsx as well as .ts: the hook and component-helper tests (issues #42, #43)
    // need JSX, and jsdom because useWardData is a client hook that runs effects.
    // The pure-function suites are unaffected by the heavier environment.
    include: ["src/**/*.test.{ts,tsx}"],
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
  },
});
