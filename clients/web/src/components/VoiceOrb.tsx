"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useIRIS } from "@/lib/store";
import { wsClient } from "@/lib/websocket";

interface VoiceOrbProps {
  onTranscript?: (text: string) => void;
}

// Web Speech API type stubs
declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  }
}

export default function VoiceOrb({ onTranscript }: VoiceOrbProps) {
  const { state, dispatch } = useIRIS();
  const { isListening, isSpeaking, wsConnected } = state;
  const [transcript, setTranscript] = useState("");
  const [supported, setSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    const SpeechRec =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    setSupported(!!SpeechRec);
    if (SpeechRec) {
      const rec = new SpeechRec();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = "en-US";

      rec.onresult = (event: SpeechRecognitionEvent) => {
        const interim = Array.from(event.results)
          .map((r) => r[0].transcript)
          .join("");
        setTranscript(interim);

        const final = Array.from(event.results)
          .filter((r) => r.isFinal)
          .map((r) => r[0].transcript)
          .join("");

        if (final) {
          onTranscript?.(final);
          wsClient.sendVoiceCommand(final);
          setTranscript("");
        }
      };

      rec.onend = () => {
        dispatch({ type: "SET_LISTENING", payload: false });
      };

      rec.onerror = () => {
        dispatch({ type: "SET_LISTENING", payload: false });
      };

      recognitionRef.current = rec;
    }

    synthRef.current = window.speechSynthesis;
  }, [dispatch, onTranscript]);

  // Listen for IRIS responses to speak aloud
  useEffect(() => {
    const unsub = wsClient.on("llm_response", (data: unknown) => {
      const d = data as { content?: string };
      if (d.content && synthRef.current) {
        dispatch({ type: "SET_SPEAKING", payload: true });
        const utterance = new SpeechSynthesisUtterance(d.content);
        utterance.rate = 1.05;
        utterance.pitch = 0.9;
        // Try to use a British/neutral voice
        const voices = synthRef.current.getVoices();
        const preferred = voices.find(
          (v) =>
            v.lang === "en-GB" ||
            v.name.includes("Daniel") ||
            v.name.includes("Google UK")
        );
        if (preferred) utterance.voice = preferred;
        utterance.onend = () => dispatch({ type: "SET_SPEAKING", payload: false });
        synthRef.current.speak(utterance);
      }
    });
    return unsub;
  }, [dispatch]);

  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      dispatch({ type: "SET_LISTENING", payload: false });
    } else {
      if (synthRef.current?.speaking) synthRef.current.cancel();
      recognitionRef.current.start();
      dispatch({ type: "SET_LISTENING", payload: true });
    }
  }, [isListening, dispatch]);

  const orbClass = isSpeaking ? "orb speaking" : isListening ? "orb listening" : "orb";

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Orb */}
      <div className="orb-container" style={{ width: 240, height: 240 }}>
        {/* Orbit rings */}
        <div className="orb-ring orb-ring-1" />
        <div className="orb-ring orb-ring-2" />
        <div className="orb-ring orb-ring-3" />

        {/* Main orb — clickable */}
        <button
          id="iris-voice-orb"
          onClick={toggleListening}
          disabled={!supported || !wsConnected}
          className={`${orbClass} relative z-10 border-0 bg-transparent cursor-pointer disabled:opacity-30`}
          title={supported ? "Click to speak to IRIS" : "Voice not supported in this browser"}
        />

        {/* Connection indicator */}
        <div
          className={`absolute bottom-8 right-8 status-dot ${wsConnected ? "online" : "offline"}`}
          title={wsConnected ? "Connected to IRIS" : "Disconnected"}
        />
      </div>

      {/* Status text */}
      <div className="text-center" style={{ minHeight: 40 }}>
        {isSpeaking && (
          <p className="text-[0.7rem] tracking-widest text-[rgba(255,196,70,0.8)] uppercase animate-fadeIn">
            ◈ IRIS SPEAKING
          </p>
        )}
        {isListening && !isSpeaking && (
          <p className="text-[0.7rem] tracking-widest text-glow-sm uppercase animate-fadeIn">
            ◈ LISTENING...
          </p>
        )}
        {!isListening && !isSpeaking && wsConnected && (
          <p className="text-[0.65rem] tracking-[0.25em] text-[rgba(74,224,255,0.35)] uppercase">
            TAP TO SPEAK
          </p>
        )}
        {!wsConnected && (
          <p className="text-[0.65rem] tracking-widest text-[rgba(255,74,110,0.6)] uppercase">
            OFFLINE
          </p>
        )}
      </div>

      {/* Live transcript */}
      {transcript && (
        <div className="glass px-4 py-2 rounded text-[0.7rem] max-w-xs text-center animate-fadeIn">
          <span className="typing-cursor">{transcript}</span>
        </div>
      )}

      {/* Mic not supported warning */}
      {!supported && (
        <p className="text-[0.6rem] text-[rgba(255,74,110,0.6)] text-center max-w-xs">
          Voice not supported. Use Chrome or Edge for voice commands.
        </p>
      )}
    </div>
  );
}
