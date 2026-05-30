"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import VoiceOrb from "@/components/VoiceOrb";
import ChatInterface from "@/components/ChatInterface";
import DevicePanel from "@/components/DevicePanel";
import TasksPanel from "@/components/TasksPanel";
import NotificationCenter from "@/components/NotificationCenter";
import { IRISProvider, useIRIS, useNotify } from "@/lib/store";
import { wsClient } from "@/lib/websocket";
import { authApi, devicesApi, type Device } from "@/lib/api";

// ─── Inner dashboard (needs IRISProvider context) ─────────────────────────────
function DashboardInner() {
  const router = useRouter();
  const { state, dispatch } = useIRIS();
  const notify = useNotify();
  const [currentTime, setCurrentTime] = useState("");
  const [activeTab, setActiveTab] = useState<"chat" | "tasks" | "devices">("chat");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  // ── Clock ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const tick = () =>
      setCurrentTime(
        new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // ── Load user + devices ────────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("iris_access_token");
    if (!token) { router.replace("/"); return; }

    authApi.getMe()
      .then((user) => dispatch({ type: "SET_USER", payload: user }))
      .catch(() => { router.replace("/"); });

    devicesApi.list()
      .then((devices) => dispatch({ type: "SET_DEVICES", payload: devices }))
      .catch(() => {});
  }, [dispatch, router]);

  // ── Connect WebSocket ──────────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("iris_access_token");
    if (!token) return;

    wsClient.connect("web-dashboard", token);

    const unsubConnected = wsClient.on("connected", () => {
      setWsStatus("connected");
      dispatch({ type: "SET_WS_CONNECTED", payload: true });
      notify("IRIS Connected", "Real-time link established", "info");
    });

    const unsubDisconnected = wsClient.on("disconnected", () => {
      setWsStatus("disconnected");
      dispatch({ type: "SET_WS_CONNECTED", payload: false });
    });

    const unsubReconnecting = wsClient.on("reconnecting", () => {
      setWsStatus("connecting");
    });

    // Handle device telemetry from other devices
    const unsubTelemetry = wsClient.on("device_telemetry", (data: unknown) => {
      const d = data as { device_id: string; data: Device["telemetry"] };
      dispatch({
        type: "UPDATE_DEVICE_TELEMETRY",
        payload: { device_id: d.device_id, data: d.data },
      });
    });

    // Handle system events
    const unsubSystem = wsClient.on("system_event", (data: unknown) => {
      const d = data as { event: string; data: { device_id: string } };
      if (d.event === "device_connected") {
        dispatch({
          type: "UPDATE_DEVICE_STATUS",
          payload: { device_id: d.data.device_id, status: "online" },
        });
        notify("Device Connected", `${d.data.device_id} is now online`, "info");
      } else if (d.event === "device_disconnected") {
        dispatch({
          type: "UPDATE_DEVICE_STATUS",
          payload: { device_id: d.data.device_id, status: "offline" },
        });
      }
    });

    return () => {
      unsubConnected();
      unsubDisconnected();
      unsubReconnecting();
      unsubTelemetry();
      unsubSystem();
      wsClient.disconnect();
    };
  }, [dispatch, notify]);

  async function handleLogout() {
    wsClient.disconnect();
    await authApi.logout().catch(() => {});
    localStorage.clear();
    router.push("/");
  }

  const wsStatusColors = {
    connected: "text-[#39ff9a]",
    connecting: "text-[#ffc947]",
    disconnected: "text-[#ff4a6e]",
  };

  const wsStatusLabels = {
    connected: "● ONLINE",
    connecting: "◌ CONNECTING",
    disconnected: "○ OFFLINE",
  };

  return (
    <div className="h-screen w-screen overflow-hidden relative flex flex-col" style={{ background: "var(--iris-bg)" }}>
      {/* Grid background */}
      <div className="grid-bg" />
      <div className="scanlines absolute inset-0 pointer-events-none z-10" />

      {/* Ambient glow */}
      <div className="absolute top-0 left-1/3 w-[500px] h-[300px] rounded-full bg-[#4ae0ff] opacity-[0.025] blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[200px] rounded-full bg-[#1e90ff] opacity-[0.03] blur-3xl pointer-events-none" />

      {/* ── Top HUD Bar ──────────────────────────────────────────────────── */}
      <header className="relative z-20 flex items-center justify-between px-6 py-2 border-b border-[rgba(74,224,255,0.1)] glass shrink-0">
        {/* Left: Logo */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full bg-radial" style={{
            background: "radial-gradient(circle, rgba(74,224,255,0.8), rgba(30,144,255,0.3))",
            boxShadow: "0 0 12px rgba(74,224,255,0.5)",
          }} />
          <div>
            <h1 className="text-sm font-black tracking-[0.2em] text-glow-sm" style={{ fontFamily: "var(--font-display)" }}>
              IRIS
            </h1>
            <p className="text-[0.45rem] tracking-[0.25em] text-[rgba(74,224,255,0.35)] uppercase -mt-0.5">
              AI Command Center
            </p>
          </div>
        </div>

        {/* Center: Clock + Date */}
        <div className="text-center">
          <div
            className="text-xl font-bold tracking-[0.15em] text-glow"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {currentTime}
          </div>
          <div className="text-[0.5rem] tracking-[0.2em] text-[rgba(74,224,255,0.35)] uppercase">
            {new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
          </div>
        </div>

        {/* Right: Status + User + Logout */}
        <div className="flex items-center gap-4">
          <div className={`text-[0.6rem] font-bold tracking-widest ${wsStatusColors[wsStatus]}`}>
            {wsStatusLabels[wsStatus]}
          </div>
          {state.user && (
            <div className="text-right">
              <p className="text-[0.65rem] font-bold">
                {state.user.full_name || state.user.email.split("@")[0]}
              </p>
              <p className="text-[0.5rem] text-[rgba(74,224,255,0.3)] uppercase">{state.user.role}</p>
            </div>
          )}
          <button
            id="iris-logout"
            onClick={handleLogout}
            className="btn-iris text-[0.6rem] px-3 py-1"
          >
            LOGOUT
          </button>
        </div>
      </header>

      {/* ── Main Content ──────────────────────────────────────────────────── */}
      <main className="relative z-20 flex flex-1 overflow-hidden">

        {/* ── Left Panel: Devices ─────────────────────────────────────────── */}
        <aside className="w-72 shrink-0 border-r border-[rgba(74,224,255,0.1)] p-4 overflow-hidden flex flex-col">
          <DevicePanel />
        </aside>

        {/* ── Center Panel: Orb + Chat ────────────────────────────────────── */}
        <section className="flex-1 flex flex-col overflow-hidden">
          {/* Top: Voice Orb */}
          <div className="flex items-center justify-center py-6 border-b border-[rgba(74,224,255,0.1)] shrink-0">
            <VoiceOrb />
          </div>

          {/* Middle: Mobile tab nav for narrower breakpoints — always visible on desktop */}
          <div className="flex border-b border-[rgba(74,224,255,0.08)] shrink-0 xl:hidden">
            {(["chat", "tasks", "devices"] as const).map((tab) => (
              <button
                key={tab}
                id={`iris-tab-${tab}`}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-2 text-[0.6rem] tracking-widest uppercase transition-colors ${
                  activeTab === tab
                    ? "text-[#4ae0ff] border-b-2 border-[#4ae0ff]"
                    : "text-[rgba(74,224,255,0.35)]"
                }`}
              >
                {tab === "chat" ? "◈ Chat" : tab === "tasks" ? "✓ Tasks" : "📡 Devices"}
              </button>
            ))}
          </div>

          {/* Chat interface */}
          <div className="flex-1 overflow-hidden p-4">
            <ChatInterface />
          </div>
        </section>

        {/* ── Right Panel: Tasks ──────────────────────────────────────────── */}
        <aside className="w-80 shrink-0 border-l border-[rgba(74,224,255,0.1)] p-4 overflow-hidden flex flex-col">
          <TasksPanel />
        </aside>
      </main>

      {/* ── Bottom Status Bar ────────────────────────────────────────────── */}
      <footer className="relative z-20 flex items-center justify-between px-6 py-1.5 border-t border-[rgba(74,224,255,0.08)] shrink-0">
        <div className="flex gap-6">
          <span className="text-[0.5rem] tracking-wider text-[rgba(74,224,255,0.3)] uppercase">
            IRIS AI v1.0.0
          </span>
          <span className="text-[0.5rem] tracking-wider text-[rgba(74,224,255,0.2)] uppercase">
            {state.devices.filter((d) => d.status === "online").length} device(s) online
          </span>
        </div>
        <div className="flex gap-4">
          <span className="text-[0.5rem] text-[rgba(74,224,255,0.2)] uppercase tracking-wider">
            End-to-End Encrypted
          </span>
        </div>
      </footer>

      {/* Global notification toasts */}
      <NotificationCenter />
    </div>
  );
}

// ─── Page wrapper with Provider ───────────────────────────────────────────────
export default function DashboardPage() {
  return (
    <IRISProvider>
      <DashboardInner />
    </IRISProvider>
  );
}
