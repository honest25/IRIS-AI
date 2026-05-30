"use client";

import { useEffect } from "react";
import { useIRIS, useNotify } from "@/lib/store";
import { wsClient } from "@/lib/websocket";

export default function NotificationCenter() {
  const { state, dispatch } = useIRIS();
  const notify = useNotify();

  // Register WS notification handler
  useEffect(() => {
    const unsub = wsClient.on("notification", (data: unknown) => {
      const d = data as {
        notification?: { title: string; body: string; notification_type: string };
      };
      if (d.notification) {
        notify(
          d.notification.title,
          d.notification.body,
          (d.notification.notification_type as "info" | "warning" | "error") || "info"
        );

        // Also fire browser notification if permitted
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification(d.notification.title, { body: d.notification.body });
        }
      }
    });

    // Request browser notification permission
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    return unsub;
  }, [notify]);

  const typeColors: Record<string, string> = {
    info:     "border-l-[#4ae0ff] bg-[rgba(74,224,255,0.05)]",
    warning:  "border-l-[#ffc947] bg-[rgba(255,201,71,0.05)]",
    error:    "border-l-[#ff4a6e] bg-[rgba(255,74,110,0.05)]",
    reminder: "border-l-[#a855f7] bg-[rgba(168,85,247,0.05)]",
  };

  const typeIcons: Record<string, string> = {
    info: "ℹ", warning: "⚠", error: "✕", reminder: "🔔",
  };

  if (state.notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 w-72">
      {state.notifications.map((n) => (
        <div
          key={n.id}
          className={`glass border-l-2 rounded-md p-3 animate-slideRight ${typeColors[n.type] || typeColors.info}`}
        >
          <div className="flex items-start gap-2">
            <span className="text-[0.8rem] shrink-0 mt-0.5">
              {typeIcons[n.type] || "ℹ"}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-[0.7rem] font-bold truncate">{n.title}</p>
              <p className="text-[0.65rem] text-[rgba(74,224,255,0.6)] mt-0.5 line-clamp-2">
                {n.body}
              </p>
            </div>
            <button
              onClick={() =>
                dispatch({ type: "REMOVE_NOTIFICATION", payload: n.id })
              }
              className="shrink-0 text-[0.6rem] text-[rgba(74,224,255,0.3)] hover:text-[rgba(74,224,255,0.8)] transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
