/**
 * IRIS AI — API Client
 * Axios-based HTTP client with automatic JWT token refresh and auth interceptor.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Token helpers ─────────────────────────────────────────────────────────────
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("iris_access_token");
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("iris_refresh_token");
}

export function clearTokens() {
  localStorage.removeItem("iris_access_token");
  localStorage.removeItem("iris_refresh_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearTokens();
    window.location.href = "/";
    return null;
  }

  const data = await res.json();
  localStorage.setItem("iris_access_token", data.access_token);
  localStorage.setItem("iris_refresh_token", data.refresh_token);
  return data.access_token;
}

// ─── Core fetch wrapper ────────────────────────────────────────────────────────
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken();
    if (newToken) return apiFetch<T>(endpoint, options, false);
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json();
}

// ─── Auth API ─────────────────────────────────────────────────────────────────
export const authApi = {
  getMe: () => apiFetch<{ id: number; email: string; full_name: string; role: string }>("/auth/me"),
  logout: () => apiFetch("/auth/logout", { method: "POST" }),
};

// ─── Chat API ─────────────────────────────────────────────────────────────────
export const chatApi = {
  send: (message: string, conversationId?: number, deviceId?: string) =>
    apiFetch<{ conversation_id: number; message: { content: string }; intent?: string }>(
      "/chat/",
      {
        method: "POST",
        body: JSON.stringify({ message, conversation_id: conversationId, device_id: deviceId }),
      }
    ),
  listConversations: () => apiFetch<Conversation[]>("/chat/conversations"),
  getConversation: (id: number) => apiFetch<ConversationFull>(`/chat/conversations/${id}`),
  deleteConversation: (id: number) =>
    apiFetch(`/chat/conversations/${id}`, { method: "DELETE" }),
};

// ─── Devices API ──────────────────────────────────────────────────────────────
export const devicesApi = {
  list: () => apiFetch<Device[]>("/devices/"),
  register: (name: string, type: string) =>
    apiFetch<Device & { auth_token: string }>("/devices/register", {
      method: "POST",
      body: JSON.stringify({ device_name: name, device_type: type }),
    }),
  sendCommand: (deviceId: number, action: string, params = {}) =>
    apiFetch(`/devices/${deviceId}/command`, {
      method: "POST",
      body: JSON.stringify({ action, params }),
    }),
  delete: (deviceId: number) =>
    apiFetch(`/devices/${deviceId}`, { method: "DELETE" }),
};

// ─── Tasks API ────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (status?: string) =>
    apiFetch<Task[]>(`/productivity/tasks${status ? `?status=${status}` : ""}`),
  create: (data: Partial<Task>) =>
    apiFetch<Task>("/productivity/tasks", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Task>) =>
    apiFetch<Task>(`/productivity/tasks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: number) =>
    apiFetch(`/productivity/tasks/${id}`, { method: "DELETE" }),
};

// ─── Notes API ────────────────────────────────────────────────────────────────
export const notesApi = {
  list: (search?: string) =>
    apiFetch<Note[]>(`/productivity/notes${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  create: (data: Partial<Note>) =>
    apiFetch<Note>("/productivity/notes", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Note>) =>
    apiFetch<Note>(`/productivity/notes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: number) =>
    apiFetch(`/productivity/notes/${id}`, { method: "DELETE" }),
};

// ─── Memory API ───────────────────────────────────────────────────────────────
export const memoryApi = {
  search: (q: string) =>
    apiFetch<{ documents: string[]; query: string }>(`/memory/search?q=${encodeURIComponent(q)}`),
};

// ─── Type Definitions ─────────────────────────────────────────────────────────
export interface Device {
  id: number;
  device_name: string;
  device_type: string;
  status: string;
  telemetry?: {
    cpu?: number;
    ram?: number;
    battery?: number;
    disk?: number;
    network?: number;
  };
  last_seen: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: string;
  priority: string;
  due_date?: string;
  completed_at?: string;
  created_at: string;
}

export interface Note {
  id: number;
  title: string;
  content?: string;
  tags?: string;
  is_pinned: boolean;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ConversationFull extends Conversation {
  messages: Message[];
}
