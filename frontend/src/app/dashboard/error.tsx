"use client";

import { useEffect } from "react";
import posthog from "posthog-js";
import { Button } from "@/components/ui/button";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // PostHog is initialized globally in instrumentation-client.ts; this
    // boundary catches an error before it reaches window.onerror, so report it
    // explicitly rather than relying on automatic exception capture.
    posthog.captureException(error, { route: "/dashboard", digest: error.digest });
    console.error("Dashboard render error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-lg font-semibold text-foreground">Something went wrong</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        The dashboard hit an unexpected error. Try reloading, if it keeps happening
        let us know.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
