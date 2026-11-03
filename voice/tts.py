"""
Offline Text-to-Speech Engine using Windows SAPI5 (pyttsx3).
Thread-safe, non-blocking, with immediate stop/interruption support.
"""

import threading
import queue
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_text_for_speech(text: str) -> str:
    """Strip markdown code blocks, links, and formatting for natural spoken output."""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", " Code snippet omitted. ", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown symbols (*, _, #)
    text = re.sub(r"[\*\_#>]", "", text)
    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TTSEngine:
    def __init__(self, rate: int = 180, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._stop_event = threading.Event()
        self._current_engine = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.is_speaking = False

    def speak(self, text: str, on_finished: Optional[callable] = None):
        """Speak text in a non-blocking background thread."""
        self.stop()  # Stop any ongoing speech first

        clean_text = clean_text_for_speech(text)
        if not clean_text:
            if on_finished:
                on_finished()
            return

        self._stop_event.clear()
        self.is_speaking = True

        def _worker():
            import pythoncom
            import pyttsx3

            pythoncom.CoInitialize()
            try:
                engine = pyttsx3.init()
                with self._lock:
                    self._current_engine = engine

                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)

                # Split text into small sentences to allow quick interruption
                sentences = re.split(r"(?<=[.!?\n])\s+", clean_text)
                for sentence in sentences:
                    if self._stop_event.is_set():
                        break
                    s = sentence.strip()
                    if not s:
                        continue
                    engine.say(s)
                    engine.runAndWait()

            except Exception as e:
                logger.error(f"TTS execution error: {e}")
            finally:
                with self._lock:
                    self._current_engine = None
                    self.is_speaking = False
                pythoncom.CoUninitialize()
                if on_finished:
                    on_finished()

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Immediately interrupt/stop speech."""
        self._stop_event.set()
        with self._lock:
            if self._current_engine:
                try:
                    self._current_engine.stop()
                except Exception:
                    pass
        self.is_speaking = False
