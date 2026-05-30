"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useIRIS } from "@/lib/store";
import { wsClient } from "@/lib/websocket";
import { chatApi, type Message } from "@/lib/api";

interface ChatInterfaceProps {
  onSend?: (msg: string) => void;
}

export default function ChatInterface({ onSend }: ChatInterfaceProps) {
  const { state, dispatch } = useIRIS();
  const { messages, activeConversationId, wsConnected } = state;
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // Listen to WebSocket events
  useEffect(() => {
    const unsubChunk = wsClient.on("llm_chunk", (data: unknown) => {
      const d = data as { content: string };
      setIsStreaming(true);
      setStreamingContent((prev) => prev + (d.content || ""));
    });

    const unsubDone = wsClient.on("llm_response", (data: unknown) => {
      const d = data as { content: string; conversation_id: number };
      setIsStreaming(false);
      setStreamingContent("");

      const aiMsg: Message = {
        id: Date.now(),
        role: "assistant",
        content: d.content,
        timestamp: new Date().toISOString(),
      };
      dispatch({ type: "APPEND_MESSAGE", payload: aiMsg });
      if (d.conversation_id) {
        dispatch({ type: "SET_ACTIVE_CONVERSATION", payload: d.conversation_id });
      }
    });

    return () => {
      unsubChunk();
      unsubDone();
    };
  }, [dispatch]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text) return;

    setInput("");

    // Optimistically add user message
    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    dispatch({ type: "APPEND_MESSAGE", payload: userMsg });
    onSend?.(text);

    if (wsConnected) {
      // Send via WebSocket (streaming)
      wsClient.sendVoiceCommand(text, activeConversationId ?? undefined);
    } else {
      // Fallback to HTTP
      setIsStreaming(true);
      try {
        const res = await chatApi.send(text, activeConversationId ?? undefined);
        dispatch({ type: "APPEND_MESSAGE", payload: res.message as Message });
        dispatch({ type: "SET_ACTIVE_CONVERSATION", payload: res.conversation_id });
      } catch {
        dispatch({
          type: "APPEND_MESSAGE",
          payload: {
            id: Date.now(),
            role: "assistant",
            content: "Connection to IRIS server failed. Check your connection.",
            timestamp: new Date().toISOString(),
          },
        });
      } finally {
        setIsStreaming(false);
      }
    }
  }, [input, wsConnected, activeConversationId, dispatch, onSend]);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-3 px-2 pb-2" style={{ scrollbarGutter: "stable" }}>
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full gap-3 opacity-40">
            <div className="text-3xl">◈</div>
            <p className="text-[0.65rem] tracking-[0.2em] uppercase">
              Ask IRIS anything...
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={msg.id || i}
            className={`animate-fadeInUp flex gap-3 ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
            style={{ animationDelay: `${Math.min(i * 0.03, 0.3)}s` }}
          >
            {/* Avatar */}
            <div
              className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[0.5rem] font-bold mt-1 ${
                msg.role === "user"
                  ? "bg-[rgba(74,224,255,0.15)] border border-[rgba(74,224,255,0.3)]"
                  : "bg-[rgba(30,144,255,0.15)] border border-[rgba(30,144,255,0.3)]"
              }`}
            >
              {msg.role === "user" ? "U" : "◈"}
            </div>

            {/* Bubble */}
            <div className="max-w-[80%]">
              <div
                className={`px-3 py-2 text-[0.8rem] leading-relaxed ${
                  msg.role === "user" ? "chat-bubble-user" : "chat-bubble-iris"
                }`}
              >
                {msg.content}
              </div>
              <div className="text-[0.55rem] text-[rgba(74,224,255,0.25)] mt-1 px-1">
                {formatTime(msg.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Streaming response */}
        {isStreaming && (
          <div className="flex gap-3 animate-fadeIn">
            <div className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[0.5rem] font-bold mt-1 bg-[rgba(30,144,255,0.15)] border border-[rgba(30,144,255,0.3)]">
              ◈
            </div>
            <div className="chat-bubble-iris px-3 py-2 text-[0.8rem] leading-relaxed max-w-[80%]">
              {streamingContent ? (
                <span className="typing-cursor">{streamingContent}</span>
              ) : (
                <span className="text-[rgba(74,224,255,0.4)]">
                  <span className="typing-cursor">Processing</span>
                </span>
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="pt-3 border-t border-[rgba(74,224,255,0.1)]">
        <div className="flex gap-2 items-center">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              id="iris-chat-input"
              type="text"
              className="input-iris pr-12"
              placeholder="Send a message to IRIS..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={isStreaming}
              autoComplete="off"
            />
          </div>
          <button
            id="iris-chat-send"
            onClick={sendMessage}
            disabled={!input.trim() || isStreaming}
            className="btn-iris btn-iris-primary px-4 py-2 disabled:opacity-30 shrink-0"
          >
            ▶
          </button>
        </div>
        <p className="text-[0.55rem] text-[rgba(74,224,255,0.25)] mt-1">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
