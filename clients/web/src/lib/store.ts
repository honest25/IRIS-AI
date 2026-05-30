"use client";

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  ReactNode,
} from "react";
import type { Device, Task, Note, Message, Conversation } from "./api";

// ─── State Types ──────────────────────────────────────────────────────────────
export interface IRISState {
  user: { id: number; email: string; full_name: string } | null;
  devices: Device[];
  activeConversationId: number | null;
  conversations: Conversation[];
  messages: Message[];
  tasks: Task[];
  notes: Note[];
  wsConnected: boolean;
  isListening: boolean;
  isSpeaking: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  type: "info" | "warning" | "error" | "reminder";
  timestamp: number;
}

// ─── Actions ──────────────────────────────────────────────────────────────────
type Action =
  | { type: "SET_USER"; payload: IRISState["user"] }
  | { type: "SET_DEVICES"; payload: Device[] }
  | { type: "UPDATE_DEVICE_TELEMETRY"; payload: { device_id: string; data: Device["telemetry"] } }
  | { type: "UPDATE_DEVICE_STATUS"; payload: { device_id: string; status: string } }
  | { type: "SET_WS_CONNECTED"; payload: boolean }
  | { type: "SET_LISTENING"; payload: boolean }
  | { type: "SET_SPEAKING"; payload: boolean }
  | { type: "SET_CONVERSATIONS"; payload: Conversation[] }
  | { type: "SET_ACTIVE_CONVERSATION"; payload: number | null }
  | { type: "SET_MESSAGES"; payload: Message[] }
  | { type: "APPEND_MESSAGE"; payload: Message }
  | { type: "APPEND_MESSAGE_CHUNK"; payload: { conversationId: number; chunk: string } }
  | { type: "SET_TASKS"; payload: Task[] }
  | { type: "ADD_TASK"; payload: Task }
  | { type: "UPDATE_TASK"; payload: Task }
  | { type: "REMOVE_TASK"; payload: number }
  | { type: "SET_NOTES"; payload: Note[] }
  | { type: "ADD_NOTIFICATION"; payload: Notification }
  | { type: "REMOVE_NOTIFICATION"; payload: string };

// ─── Initial State ────────────────────────────────────────────────────────────
const initialState: IRISState = {
  user: null,
  devices: [],
  activeConversationId: null,
  conversations: [],
  messages: [],
  tasks: [],
  notes: [],
  wsConnected: false,
  isListening: false,
  isSpeaking: false,
  notifications: [],
};

// ─── Reducer ──────────────────────────────────────────────────────────────────
function irisReducer(state: IRISState, action: Action): IRISState {
  switch (action.type) {
    case "SET_USER":
      return { ...state, user: action.payload };

    case "SET_DEVICES":
      return { ...state, devices: action.payload };

    case "UPDATE_DEVICE_TELEMETRY":
      return {
        ...state,
        devices: state.devices.map((d) =>
          d.device_name === action.payload.device_id
            ? { ...d, telemetry: action.payload.data, status: "online" }
            : d
        ),
      };

    case "UPDATE_DEVICE_STATUS":
      return {
        ...state,
        devices: state.devices.map((d) =>
          d.device_name === action.payload.device_id
            ? { ...d, status: action.payload.status }
            : d
        ),
      };

    case "SET_WS_CONNECTED":
      return { ...state, wsConnected: action.payload };

    case "SET_LISTENING":
      return { ...state, isListening: action.payload };

    case "SET_SPEAKING":
      return { ...state, isSpeaking: action.payload };

    case "SET_CONVERSATIONS":
      return { ...state, conversations: action.payload };

    case "SET_ACTIVE_CONVERSATION":
      return { ...state, activeConversationId: action.payload };

    case "SET_MESSAGES":
      return { ...state, messages: action.payload };

    case "APPEND_MESSAGE":
      return { ...state, messages: [...state.messages, action.payload] };

    case "SET_TASKS":
      return { ...state, tasks: action.payload };

    case "ADD_TASK":
      return { ...state, tasks: [action.payload, ...state.tasks] };

    case "UPDATE_TASK":
      return {
        ...state,
        tasks: state.tasks.map((t) =>
          t.id === action.payload.id ? action.payload : t
        ),
      };

    case "REMOVE_TASK":
      return { ...state, tasks: state.tasks.filter((t) => t.id !== action.payload) };

    case "SET_NOTES":
      return { ...state, notes: action.payload };

    case "ADD_NOTIFICATION": {
      const notifs = [action.payload, ...state.notifications].slice(0, 10);
      return { ...state, notifications: notifs };
    }

    case "REMOVE_NOTIFICATION":
      return {
        ...state,
        notifications: state.notifications.filter((n) => n.id !== action.payload),
      };

    default:
      return state;
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────
const IRISContext = createContext<{
  state: IRISState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function IRISProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(irisReducer, initialState);
  return (
    <IRISContext.Provider value={{ state, dispatch }}>
      {children}
    </IRISContext.Provider>
  );
}

export function useIRIS() {
  const ctx = useContext(IRISContext);
  if (!ctx) throw new Error("useIRIS must be used within IRISProvider");
  return ctx;
}

// ─── Notification helper ──────────────────────────────────────────────────────
export function useNotify() {
  const { dispatch } = useIRIS();
  return useCallback(
    (
      title: string,
      body: string,
      type: Notification["type"] = "info"
    ) => {
      const id = `${Date.now()}-${Math.random()}`;
      dispatch({
        type: "ADD_NOTIFICATION",
        payload: { id, title, body, type, timestamp: Date.now() },
      });
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        dispatch({ type: "REMOVE_NOTIFICATION", payload: id });
      }, 5000);
    },
    [dispatch]
  );
}
