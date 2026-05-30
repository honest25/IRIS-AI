"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bootComplete, setBootComplete] = useState(false);
  const [statusLines, setStatusLines] = useState<string[]>([]);

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Boot sequence animation
  useEffect(() => {
    const lines = [
      "IRIS AI v1.0.0 — Intelligent Responsive Integrated System",
      "Initializing neural core...",
      "Loading memory modules... OK",
      "Establishing secure channel... OK",
      "Connecting to AI provider... OK",
      "System ready. Awaiting authentication.",
    ];
    let i = 0;
    const interval = setInterval(() => {
      if (i < lines.length) {
        setStatusLines((prev) => [...prev, lines[i]]);
        i++;
      } else {
        setBootComplete(true);
        clearInterval(interval);
      }
    }, 350);
    return () => clearInterval(interval);
  }, []);

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem("iris_access_token");
    if (token) router.replace("/dashboard");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === "login") {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const res = await fetch(`${API}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData.toString(),
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Login failed");
        }

        const data = await res.json();
        localStorage.setItem("iris_access_token", data.access_token);
        localStorage.setItem("iris_refresh_token", data.refresh_token);
        router.push("/dashboard");
      } else {
        const res = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Registration failed");
        }

        setMode("login");
        setError("Account created! Please log in.");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden flex items-center justify-center bg-[#050a12]">
      {/* Grid background */}
      <div className="grid-bg" />

      {/* Ambient glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[#4ae0ff] opacity-[0.03] blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full bg-[#1e90ff] opacity-[0.05] blur-3xl pointer-events-none" />

      {/* Scanlines */}
      <div className="scanlines absolute inset-0 pointer-events-none" />

      {/* Main container */}
      <div className="relative z-10 flex flex-col items-center gap-8 w-full max-w-md px-6">

        {/* Logo & Title */}
        <div className="text-center animate-fadeInUp">
          {/* IRIS Logo — SVG circle with orbiting dot */}
          <div className="mx-auto mb-6 relative w-24 h-24 flex items-center justify-center">
            <div className="orb w-20 h-20" style={{ animationDuration: "3s" }} />
            <div className="orb-ring orb-ring-1 absolute" style={{ width: "90px", height: "90px" }} />
          </div>

          <h1
            className="text-4xl font-black tracking-[0.3em] text-glow mb-1"
            style={{ fontFamily: "var(--font-display)" }}
          >
            IRIS
          </h1>
          <p className="text-[0.6rem] tracking-[0.4em] text-[rgba(74,224,255,0.45)] uppercase">
            Intelligent Responsive Integrated System
          </p>
        </div>

        {/* Boot terminal */}
        {!bootComplete && (
          <div className="glass hud-corners w-full p-4 rounded-md animate-fadeIn">
            <div className="text-[0.65rem] space-y-1">
              {statusLines.map((line, i) => (
                <div key={i} className="flex gap-2 animate-fadeInUp" style={{ animationDelay: `${i * 0.05}s` }}>
                  <span className="text-[#4ae0ff] opacity-50">›</span>
                  <span className={i === statusLines.length - 1 ? "typing-cursor text-[#4ae0ff]" : "text-[rgba(74,224,255,0.6)]"}>
                    {line}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Login Form */}
        {bootComplete && (
          <div className="glass hud-corners w-full rounded-md animate-fadeInUp p-6">
            {/* Tab switcher */}
            <div className="flex mb-6 border-b border-[rgba(74,224,255,0.15)]">
              {(["login", "register"] as const).map((tab) => (
                <button
                  key={tab}
                  id={`iris-tab-${tab}`}
                  onClick={() => { setMode(tab); setError(""); }}
                  className={`flex-1 pb-2 text-[0.65rem] tracking-[0.15em] uppercase font-bold transition-colors ${
                    mode === tab
                      ? "text-[#4ae0ff] border-b-2 border-[#4ae0ff] -mb-[1px]"
                      : "text-[rgba(74,224,255,0.35)] hover:text-[rgba(74,224,255,0.65)]"
                  }`}
                >
                  {tab === "login" ? "[ AUTHENTICATE ]" : "[ REGISTER ]"}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div>
                  <label className="section-header mb-2 block">Full Name</label>
                  <input
                    id="iris-input-name"
                    type="text"
                    className="input-iris"
                    placeholder="Your name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              )}

              <div>
                <label className="section-header mb-2 block">Email</label>
                <input
                  id="iris-input-email"
                  type="email"
                  className="input-iris"
                  placeholder="user@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div>
                <label className="section-header mb-2 block">Password</label>
                <input
                  id="iris-input-password"
                  type="password"
                  className="input-iris"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>

              {error && (
                <div
                  className={`text-[0.7rem] p-2 rounded border animate-fadeIn ${
                    error.includes("created")
                      ? "text-[#39ff9a] border-[rgba(57,255,154,0.3)] bg-[rgba(57,255,154,0.05)]"
                      : "text-[#ff4a6e] border-[rgba(255,74,110,0.3)] bg-[rgba(255,74,110,0.05)]"
                  }`}
                >
                  {error}
                </div>
              )}

              <button
                id="iris-btn-submit"
                type="submit"
                disabled={loading}
                className="btn-iris btn-iris-primary w-full py-3 mt-2 text-xs tracking-widest disabled:opacity-50"
              >
                {loading ? (
                  <span className="typing-cursor">Processing</span>
                ) : mode === "login" ? (
                  "[ AUTHENTICATE ]"
                ) : (
                  "[ CREATE ACCOUNT ]"
                )}
              </button>
            </form>
          </div>
        )}

        {/* Footer */}
        <p className="text-[0.55rem] tracking-[0.25em] text-[rgba(74,224,255,0.2)] uppercase animate-fadeIn">
          IRIS AI — All systems nominal
        </p>
      </div>
    </div>
  );
}
