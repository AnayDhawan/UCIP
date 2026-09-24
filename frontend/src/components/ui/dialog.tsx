"use client"

import * as React from "react"
import { Dialog as DialogPrimitive } from "radix-ui"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * Hand-written rather than generated with `npx shadcn add dialog`: that command
 * regenerates globals.css with shadcn's generic gray token scheme, overwriting
 * the brand OKLCH palette (including --background going pure white, which
 * breaks the never-pure-white rule) and can reintroduce Geist. See DESIGN.md.
 *
 * No new dependency either: the unified `radix-ui` package already in
 * package.json bundles react-dialog, react-portal and react-dismissable-layer.
 *
 * z-index note: the dashboard's map chrome (layer switcher, legend, error
 * banner) sits at z-[1000] and Leaflet's own panes run 400 to 700, so the
 * overlay and content have to clear all of it.
 */

const DIALOG_Z = "z-[2000]"

function Dialog(props: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

function DialogTrigger(props: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />
}

function DialogPortal(props: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />
}

function DialogClose(props: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn(
        DIALOG_Z,
        "fixed inset-0 bg-ink/50 backdrop-blur-[2px]",
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        className
      )}
      {...props}
    />
  )
}

function DialogContent({
  className,
  children,
  showCloseButton = true,
  showOverlay = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  /**
   * When `false`, the built-in × close button is omitted. The caller MUST
   * provide an alternative close affordance (e.g. a `DialogClose` wrapper
   * or a header button calling `onOpenChange(false)`). Without one the
   * dialog is keyboard-trapped — Escape still works but discoverability
   * suffers. See WardDialog for the intended pattern.
   */
  showCloseButton?: boolean
  /** Drop the scrim to let the content float over a still-visible, still
   *  interactive page. Pair with `modal={false}` on the Dialog root. */
  showOverlay?: boolean
}) {
  return (
    <DialogPortal>
      {showOverlay && <DialogOverlay />}
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          DIALOG_Z,
          "fixed top-1/2 left-1/2 flex w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 flex-col",
          // dvh, not vh: vh ignores mobile browser chrome, and browser zoom
          // shrinks the viewport, so a fixed vh cap let the box run past the
          // top and bottom edges with its header and footer unreachable. The
          // calc keeps a visible margin at every zoom level.
          "max-h-[min(85dvh,100dvh-2rem)] overflow-hidden rounded-xl border border-border bg-background shadow-lg",
          "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
          className
        )}
        {...props}
      >
        {children}
        {showCloseButton && (
          <DialogPrimitive.Close
            data-slot="dialog-close"
            className="absolute top-3 right-3 rounded-md p-1 text-muted-foreground opacity-80 transition-opacity hover:bg-accent hover:opacity-100 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
}

function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-header"
      className={cn("shrink-0 border-b border-border px-6 py-4 pr-14", className)}
      {...props}
    />
  )
}

function DialogFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-footer"
      className={cn("shrink-0 border-t border-border px-5 py-3", className)}
      {...props}
    />
  )
}

function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("text-lg font-semibold text-foreground", className)}
      {...props}
    />
  )
}

function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn("text-xs text-muted-foreground", className)}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogClose,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
}
