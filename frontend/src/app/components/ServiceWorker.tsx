"use client";

import { useEffect } from "react";

// Registers public/sw.js in production builds, which makes the site installable
// as a web app and lets it reopen offline with the last data it loaded.
export default function ServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.error("[sw] registration failed:", err);
    });
  }, []);
  return null;
}
