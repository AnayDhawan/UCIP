"use client";

import { useEffect } from "react";

// Registers public/sw.js in production builds, which makes the site installable
// as a web app and lets it reopen offline. Skipped inside an iframe, so a page
// that embeds /embed/ward/* never gets a worker from us.
export default function RegisterServiceWorker() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    if (window.self !== window.top) return;
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.error("[sw] registration failed:", err);
    });
  }, []);
  return null;
}
