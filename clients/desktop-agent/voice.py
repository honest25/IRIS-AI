"""
IRIS AI — Desktop Agent: Voice Engine
Speech-to-text and text-to-speech for the desktop agent.
Uses: speech_recognition (STT) + pyttsx3 (TTS, fully offline).
"""
import threading
import queue
import pyttsx3
import speech_recognition as sr
from typing import Callable, Optional

WAKE_WORDS = ["hey iris", "ok iris", "iris"]


class VoiceEngine:
    def __init__(self):
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.8

        # TTS engine (runs in a dedicated thread to avoid blocking)
        self._tts = pyttsx3.init()
        self._setup_tts()
        self._tts_queue: queue.Queue = queue.Queue()
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()

        self._on_command: Optional[Callable[[str], None]] = None
        self._is_listening = False
        self._stop_event = threading.Event()

    def _setup_tts(self):
        """Configure TTS voice properties."""
        voices = self._tts.getProperty("voices")
        # Prefer a British male voice for IRIS
        preferred_ids = ["HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_HAZEL_11.0",
                         "com.apple.speech.synthesis.voice.daniel.premium",
                         "com.apple.speech.synthesis.voice.daniel"]
        for voice in voices:
            if any(pid.lower() in voice.id.lower() for pid in preferred_ids):
                self._tts.setProperty("voice", voice.id)
                break
        self._tts.setProperty("rate", 185)    # slightly faster than default (200)
        self._tts.setProperty("volume", 0.95)

    def _tts_worker(self):
        """Run TTS in a background thread to avoid blocking the event loop."""
        while True:
            text = self._tts_queue.get()
            if text is None:
                break
            try:
                self._tts.say(text)
                self._tts.runAndWait()
            except Exception as e:
                print(f"[IRIS Voice] TTS error: {e}")

    def speak(self, text: str):
        """Queue text for speech synthesis."""
        # Clean up text for speech
        clean = text.replace("◈", "").replace("*", "").strip()
        if clean:
            print(f"[IRIS Voice] Speaking: {clean[:80]}{'...' if len(clean) > 80 else ''}")
            self._tts_queue.put(clean)

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for a single phrase and return the transcription.
        Returns None on failure.
        """
        with sr.Microphone() as source:
            print("[IRIS Voice] Adjusting for ambient noise...")
            self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("[IRIS Voice] Listening...")
            try:
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return None

        try:
            text = self._recognizer.recognize_google(audio)
            print(f"[IRIS Voice] Heard: {text}")
            return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[IRIS Voice] STT request error: {e}")
            # Fallback to Vosk/offline if Google fails
            return None

    def _contains_wake_word(self, text: str) -> tuple[bool, str]:
        """Check if text starts with a wake word. Returns (triggered, remainder)."""
        text_lower = text.lower().strip()
        for wake in WAKE_WORDS:
            if text_lower.startswith(wake):
                command = text_lower[len(wake):].strip()
                return True, command
        return False, text

    def start_continuous_listening(self, on_command: Callable[[str], None]):
        """
        Start continuous background listening for wake word + command.
        on_command(text) is called when a command is detected.
        """
        self._on_command = on_command
        self._stop_event.clear()

        def _listen_loop():
            print("[IRIS Voice] Background listening started. Say 'Hey IRIS' to activate.")
            while not self._stop_event.is_set():
                text = self.listen_once(timeout=5)
                if not text:
                    continue

                triggered, command = self._contains_wake_word(text)
                if triggered:
                    print(f"[IRIS Voice] Wake word detected! Command: '{command or \"(listening)\"}'")
                    if not command:
                        self.speak("Yes? I'm listening.")
                        command = self.listen_once(timeout=8) or ""
                    if command:
                        on_command(command)

        thread = threading.Thread(target=_listen_loop, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop all voice engine activity."""
        self._stop_event.set()
        self._tts_queue.put(None)  # Signal TTS worker to exit
