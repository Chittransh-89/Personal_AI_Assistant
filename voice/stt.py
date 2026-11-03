"""
Speech-to-Text Engine using local faster-whisper and sounddevice.
Operates 100% offline on CPU with int8 quantization.
Supports English, Hindi, and mixed language auto-detection.
"""

import queue
import logging
import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(
        self,
        model_size: str = WHISPER_MODEL_SIZE,
        device: str = WHISPER_DEVICE,
        compute_type: str = WHISPER_COMPUTE_TYPE
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self._is_recording = False
        self._audio_queue = queue.Queue()
        self._recorded_chunks = []
        self._stream = None
        self._lock = threading.Lock()

    def load_model(self):
        """Lazy load or pre-load the faster-whisper model."""
        if self.model is None:
            logger.info(f"Loading faster-whisper ({self.model_size}) on {self.device} ({self.compute_type})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("faster-whisper model loaded.")

    def start_recording(self):
        """Begin audio capture from default microphone."""
        with self._lock:
            if self._is_recording:
                return
            self._recorded_chunks = []
            self._is_recording = True

            def _audio_callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Sounddevice status: {status}")
                if self._is_recording:
                    self._recorded_chunks.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=AUDIO_SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=_audio_callback
            )
            self._stream.start()
            logger.info("Audio recording started.")

    def stop_recording_and_transcribe(
        self,
        language: Optional[str] = None
    ) -> str:
        """
        Stop recording, concatenate audio chunks, and transcribe using faster-whisper.
        Returns recognized string.
        """
        with self._lock:
            if not self._is_recording:
                return ""
            self._is_recording = False
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning(f"Error closing stream: {e}")
                self._stream = None

            if not self._recorded_chunks:
                return ""

            # Concatenate chunks into a single 1D numpy array
            audio_data = np.concatenate(self._recorded_chunks, axis=0).flatten()

        # If audio is empty or essentially silence
        if len(audio_data) < AUDIO_SAMPLE_RATE * 0.3:  # Less than 300ms
            logger.info("Recorded audio was too short, skipping.")
            return ""

        max_amp = np.max(np.abs(audio_data))
        if max_amp < 0.005:  # Near pure silence
            logger.info(f"Recorded audio is silent (max amp: {max_amp}), skipping.")
            return ""

        # Ensure model is loaded
        self.load_model()

        try:
            # Transcribe with language detection (multilingual supports English & Hindi)
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=3,
                language=language,  # None means auto-detect
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            text_parts = [segment.text.strip() for segment in segments]
            transcription = " ".join(text_parts).strip()
            logger.info(f"Transcribed (detected {info.language}, prob {info.language_probability:.2f}): {transcription}")
            return transcription
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""

    @property
    def is_recording(self) -> bool:
        return self._is_recording
