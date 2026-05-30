"use client";

import { useIRIS } from "@/lib/store";
import { devicesApi, type Device } from "@/lib/api";

const DEVICE_ICONS: Record<string, string> = {
  macos: "🍎",
  windows: "🪟",
  linux: "🐧",
  android: "📱",
  web: "🌐",
};

function GaugeBar({ value, warn = 75, crit = 90 }: { value?: number; warn?: number; crit?: number }) {
  const v = value ?? 0;
  const fillClass = v >= crit ? "gauge-fill crit" : v >= warn ? "gauge-fill warn" : "gauge-fill";
  return (
    <div className="gauge-bar flex-1">
      <div className={fillClass} style={{ width: `${Math.min(v, 100)}%` }} />
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value?: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[0.55rem] text-[rgba(74,224,255,0.4)] w-10 shrink-0">{label}</span>
      <GaugeBar value={value} />
      <span className="text-[0.6rem] w-8 text-right shrink-0">
        {value != null ? `${Math.round(value)}%` : "--"}
      </span>
    </div>
  );
}

function DeviceCard({ device, onCommand }: { device: Device; onCommand: (action: string) => void }) {
  const icon = DEVICE_ICONS[device.device_type] || "💻";
  const { telemetry } = device;

  return (
    <div className="glass hud-corners rounded-md p-3 animate-fadeInUp">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-[0.7rem] font-bold truncate">{device.device_name}</p>
          <p className="text-[0.55rem] text-[rgba(74,224,255,0.4)] uppercase tracking-wider">
            {device.device_type}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`status-dot ${device.status}`} />
          <span className="text-[0.55rem] text-[rgba(74,224,255,0.4)] capitalize">
            {device.status}
          </span>
        </div>
      </div>

      {/* Telemetry */}
      {telemetry && device.status === "online" && (
        <div className="space-y-1.5 mb-3">
          <MetricRow label="CPU" value={telemetry.cpu} />
          <MetricRow label="RAM" value={telemetry.ram} />
          <MetricRow label="DISK" value={telemetry.disk} />
          {telemetry.battery != null && (
            <MetricRow label="BAT" value={telemetry.battery} />
          )}
        </div>
      )}

      {/* Quick Commands */}
      {device.status === "online" && (
        <div className="flex gap-1.5 flex-wrap">
          {[
            { action: "lock_screen", label: "🔒 Lock" },
            { action: "sleep",       label: "💤 Sleep" },
            { action: "volume_up",   label: "🔊 Vol+" },
            { action: "volume_down", label: "🔉 Vol-" },
          ].map(({ action, label }) => (
            <button
              key={action}
              id={`iris-cmd-${device.id}-${action}`}
              onClick={() => onCommand(action)}
              className="btn-iris text-[0.55rem] px-2 py-1"
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DevicePanel() {
  const { state, dispatch } = useIRIS();
  const { devices } = state;

  async function handleCommand(device: Device, action: string) {
    try {
      await devicesApi.sendCommand(device.id, action);
    } catch (err) {
      console.error("Command failed:", err);
    }
  }

  async function handleRefresh() {
    try {
      const data = await devicesApi.list();
      dispatch({ type: "SET_DEVICES", payload: data });
    } catch {
      // silent fail
    }
  }

  const online = devices.filter((d) => d.status === "online").length;

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="section-header flex-1">Devices</div>
        <div className="flex items-center gap-2 ml-2">
          <span className="text-[0.6rem] text-[rgba(74,224,255,0.4)]">
            {online}/{devices.length} online
          </span>
          <button
            id="iris-devices-refresh"
            onClick={handleRefresh}
            className="btn-iris text-[0.6rem] px-2 py-1"
          >
            ↻
          </button>
        </div>
      </div>

      {/* Device list */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {devices.length === 0 && (
          <div className="text-center py-8 opacity-40">
            <p className="text-2xl mb-2">📡</p>
            <p className="text-[0.65rem] tracking-wider uppercase">No devices registered</p>
            <p className="text-[0.6rem] mt-1 text-[rgba(74,224,255,0.3)]">
              Run the desktop agent to connect
            </p>
          </div>
        )}

        {devices.map((device) => (
          <DeviceCard
            key={device.id}
            device={device}
            onCommand={(action) => handleCommand(device, action)}
          />
        ))}
      </div>
    </div>
  );
}
