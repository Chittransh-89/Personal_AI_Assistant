"""
Main Desktop Application Window for Nova Personal AI Assistant.
Built using PySide6 with 100% asynchronous background workers and modern ChatGPT-like UI.
"""

import sys
import uuid
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QKeyEvent, QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QComboBox, QFrame, QMessageBox,
    QApplication
)

from config import DEFAULT_MODEL
from core.ollama_brain import OllamaBrain
from core.memory import MemoryManager
from voice.stt import STTEngine
from voice.tts import TTSEngine
from ui.chat_widget import ChatArea

logger = logging.getLogger(__name__)


# ==========================================
# Worker Threads for Asynchronous Processing
# ==========================================

class InferenceWorker(QThread):
    """Background thread for LLM reasoning and tool execution."""
    finished = Signal(dict, bool)  # response_dict, is_voice_turn
    error = Signal(str)

    def __init__(self, brain: OllamaBrain, message: str, history: list, is_voice: bool, parent=None):
        super().__init__(parent)
        self.brain = brain
        self.message = message
        self.history = history
        self.is_voice = is_voice

    def run(self):
        try:
            result = self.brain.process_turn(self.message, self.history)
            self.finished.emit(result, self.is_voice)
        except Exception as e:
            logger.error(f"InferenceWorker error: {e}", exc_info=True)
            self.error.emit(str(e))


class TranscriptionWorker(QThread):
    """Background thread for local audio transcription using faster-whisper."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, stt_engine: STTEngine, parent=None):
        super().__init__(parent)
        self.stt_engine = stt_engine

    def run(self):
        try:
            text = self.stt_engine.stop_recording_and_transcribe()
            self.finished.emit(text)
        except Exception as e:
            logger.error(f"TranscriptionWorker error: {e}", exc_info=True)
            self.error.emit(str(e))


# ==========================================
# Smart Multi-line Input Widget
# ==========================================

class ChatInputField(QTextEdit):
    """Text input field with Enter to submit and Shift+Enter for new line."""
    return_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.return_pressed.emit()
        else:
            super().keyPressEvent(event)


# ==========================================
# Main Application Window
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self, brain: OllamaBrain, memory: MemoryManager, stt: STTEngine, tts: TTSEngine):
        super().__init__()
        self.brain = brain
        self.memory = memory
        self.stt = stt
        self.tts = tts
        self.session_id = str(uuid.uuid4())

        self.setWindowTitle("Nova - Personal AI Assistant")
        self.resize(1050, 780)
        self.setMinimumSize(820, 620)

        self._init_ui()
        self._load_models_to_dropdown()
        self._load_previous_session()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Header Bar
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(18, 12, 18, 12)
        header_layout.setSpacing(12)

        # App Logo & Local Tag
        title_lbl = QLabel("Nova AI")
        title_lbl.setObjectName("appLogo")
        header_layout.addWidget(title_lbl)

        local_badge = QLabel("Local • Offline")
        local_badge.setObjectName("localTag")
        header_layout.addWidget(local_badge)

        # Ollama Connection & Activity Status Badges
        self.conn_badge = QLabel("● Ollama Connecting...")
        self.conn_badge.setObjectName("ollamaStatusBadge")
        header_layout.addWidget(self.conn_badge)

        self.activity_badge = QLabel("● Ready")
        self.activity_badge.setObjectName("activityBadge")
        self.activity_badge.setProperty("state", "ready")
        header_layout.addWidget(self.activity_badge)

        header_layout.addStretch()

        # Model Selector Dropdown
        model_lbl = QLabel("Model:")
        model_lbl.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 13px;")
        header_layout.addWidget(model_lbl)

        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        header_layout.addWidget(self.model_combo)

        # Refresh Models Button
        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("actionBtn")
        refresh_btn.setToolTip("Refresh installed Ollama models")
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self._load_models_to_dropdown)
        header_layout.addWidget(refresh_btn)

        # Stop Speaking Button
        self.stop_speak_btn = QPushButton("⏹ Stop Speaking")
        self.stop_speak_btn.setObjectName("stopSpeakBtn")
        self.stop_speak_btn.setToolTip("Interrupt voice response immediately")
        self.stop_speak_btn.clicked.connect(self._on_stop_speaking)
        self.stop_speak_btn.setVisible(False)
        header_layout.addWidget(self.stop_speak_btn)

        # Clear Conversation Button
        clear_btn = QPushButton("🗑 Clear Chat")
        clear_btn.setObjectName("actionBtn")
        clear_btn.setToolTip("Clear conversation history")
        clear_btn.clicked.connect(self._on_clear_chat)
        header_layout.addWidget(clear_btn)

        main_layout.addWidget(header_frame)

        # 2. Scrollable Chat Area
        self.chat_area = ChatArea(self)
        main_layout.addWidget(self.chat_area, 1)

        # 3. Bottom Input Frame
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(18, 12, 18, 14)
        input_layout.setSpacing(10)

        # Input Capsule Container
        capsule_frame = QFrame()
        capsule_frame.setObjectName("inputCapsule")
        capsule_layout = QHBoxLayout(capsule_frame)
        capsule_layout.setContentsMargins(8, 4, 8, 4)
        capsule_layout.setSpacing(8)

        # Microphone Button
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setObjectName("micBtn")
        self.mic_btn.setToolTip("Click to speak (Hindi or English)")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.clicked.connect(self._toggle_mic)
        capsule_layout.addWidget(self.mic_btn)

        # Text Input Field
        self.text_input = ChatInputField()
        self.text_input.setObjectName("chatInputField")
        self.text_input.setPlaceholderText("Message Nova... (e.g. 'Explain Python decorators', 'Open Chrome', 'Notepad kholo')")
        self.text_input.setFixedHeight(48)
        self.text_input.return_pressed.connect(self._send_text_message)
        capsule_layout.addWidget(self.text_input, 1)

        # Send Button
        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedHeight(40)
        self.send_btn.clicked.connect(self._send_text_message)
        capsule_layout.addWidget(self.send_btn)

        input_layout.addWidget(capsule_frame)
        main_layout.addWidget(input_frame)

    def _load_models_to_dropdown(self):
        """Detect and populate installed Ollama models dynamically."""
        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        connected, status_msg = self.brain.check_connection()
        if connected:
            self.conn_badge.setText("● Ollama Connected")
            self.conn_badge.setProperty("offline", "false")
            self.conn_badge.style().unpolish(self.conn_badge)
            self.conn_badge.style().polish(self.conn_badge)

            models = self.brain.list_installed_models()
            if models:
                self.model_combo.addItems(models)
                # Select DEFAULT_MODEL if present
                if DEFAULT_MODEL in models:
                    idx = models.index(DEFAULT_MODEL)
                    self.model_combo.setCurrentIndex(idx)
                    self.brain.set_model(DEFAULT_MODEL)
                else:
                    self.brain.set_model(models[0])
            else:
                self.model_combo.addItem("No models found")
        else:
            self.conn_badge.setText("● Ollama Offline")
            self.conn_badge.setProperty("offline", "true")
            self.conn_badge.style().unpolish(self.conn_badge)
            self.conn_badge.style().polish(self.conn_badge)
            self.model_combo.addItem("Ollama Disconnected")

        self.model_combo.blockSignals(False)

    def _on_model_changed(self, index: int):
        """User selected a different Ollama model."""
        selected_model = self.model_combo.currentText()
        if selected_model and selected_model not in ("No models found", "Ollama Disconnected"):
            self.brain.set_model(selected_model)
            logger.info(f"Switched model to {selected_model}")

    def _load_previous_session(self):
        """Load recent chat history from local SQLite persistence."""
        recent = self.memory.get_session_history(self.session_id, limit=20)
        for msg in recent:
            self.chat_area.add_message(
                role=msg["role"],
                text=msg["content"],
                tool_results=msg.get("tool_results"),
                timestamp=msg.get("timestamp")
            )

        if not recent:
            # Welcoming message
            welcome_text = (
                "Namaste! I am **Nova**, your personal local AI desktop assistant.\n\n"
                "You can chat with me naturally or give me desktop commands like:\n"
                "- 🌐 `Open Chrome`\n"
                "- 📝 `Notepad kholo`\n"
                "- 🎥 `YouTube par Python tutorial search karo`\n"
                "- 🧮 `Open calculator`\n"
                "- 🔍 `Google par weather in Delhi search karo`\n\n"
                "Feel free to type or press the **🎤 microphone** button to speak in English, Hindi, or Hinglish!"
            )
            self.chat_area.add_message(role="assistant", text=welcome_text)

    # ==========================================
    # Message Dispatch & Inference Pipeline
    # ==========================================

    def _send_text_message(self):
        """Handle sending user text message."""
        text = self.text_input.toPlainText().strip()
        if not text:
            return

        self.text_input.clear()
        self._dispatch_message(text, is_voice_turn=False)

    def _dispatch_message(self, text: str, is_voice_turn: bool = False):
        """Add user message to UI and trigger asynchronous LLM reasoning."""
        # 1. Update UI with user message
        self.chat_area.add_message(role="user", text=text)
        self.memory.save_message(self.session_id, role="user", content=text)

        # 2. Update status indicator
        self._set_activity("● Thinking...", state="thinking")
        self.send_btn.setEnabled(False)
        self.text_input.setEnabled(False)

        # 3. Retrieve conversation context
        history = self.memory.get_session_history(self.session_id, limit=10)

        # 4. Launch background inference thread
        self.worker = InferenceWorker(self.brain, text, history, is_voice_turn, self)
        self.worker.finished.connect(self._on_inference_finished)
        self.worker.error.connect(self._on_inference_error)
        self.worker.start()

    @Slot(dict, bool)
    def _on_inference_finished(self, response: dict, is_voice_turn: bool):
        """Handle response from background LLM worker."""
        self.send_btn.setEnabled(True)
        self.text_input.setEnabled(True)
        self.text_input.setFocus()

        content = response.get("content", "")
        tools = response.get("executed_tools", [])

        # Display assistant message
        self.chat_area.add_message(role="assistant", text=content, tool_results=tools)
        self.memory.save_message(
            self.session_id,
            role="assistant",
            content=content,
            tool_results=tools
        )

        # Voice output if user interacted via microphone
        if is_voice_turn and content:
            self._set_activity("● Speaking...", state="speaking")
            self.stop_speak_btn.setVisible(True)
            self.tts.speak(content, on_finished=self._on_speech_finished)
        else:
            self._set_activity("● Ready", state="ready")

    @Slot(str)
    def _on_inference_error(self, err_msg: str):
        """Handle worker failure."""
        self.send_btn.setEnabled(True)
        self.text_input.setEnabled(True)
        self._set_activity("● Error", state="ready")
        self.chat_area.add_message(role="assistant", text=f"⚠️ Error: {err_msg}")

    # ==========================================
    # Voice Input (STT) & Output (TTS) Controls
    # ==========================================

    def _toggle_mic(self):
        """Toggle microphone recording and transcription."""
        if not self.stt.is_recording:
            # Start recording
            try:
                self.stt.start_recording()
                self.mic_btn.setText("⏹")
                self.mic_btn.setProperty("recording", "true")
                self.mic_btn.style().unpolish(self.mic_btn)
                self.mic_btn.style().polish(self.mic_btn)
                self._set_activity("● Listening...", state="listening")
            except Exception as e:
                QMessageBox.warning(self, "Microphone Error", f"Unable to start microphone: {e}")
        else:
            # Stop recording and transcribe in background
            self.mic_btn.setText("⏳")
            self.mic_btn.setProperty("recording", "false")
            self.mic_btn.style().unpolish(self.mic_btn)
            self.mic_btn.style().polish(self.mic_btn)
            self._set_activity("● Transcribing...", state="transcribing")

            self.stt_worker = TranscriptionWorker(self.stt, self)
            self.stt_worker.finished.connect(self._on_transcription_finished)
            self.stt_worker.error.connect(self._on_transcription_error)
            self.stt_worker.start()

    @Slot(str)
    def _on_transcription_finished(self, transcribed_text: str):
        """Receive transcribed text from background worker."""
        self.mic_btn.setText("🎤")
        if transcribed_text.strip():
            logger.info(f"Recognized voice query: {transcribed_text}")
            self._dispatch_message(transcribed_text, is_voice_turn=True)
        else:
            self._set_activity("● Ready", state="ready")

    @Slot(str)
    def _on_transcription_error(self, err_msg: str):
        """Handle transcription error."""
        self.mic_btn.setText("🎤")
        self._set_activity("● Ready", state="ready")
        logger.error(f"STT Error: {err_msg}")

    def _on_stop_speaking(self):
        """Interrupt and silence TTS output immediately."""
        self.tts.stop()
        self.stop_speak_btn.setVisible(False)
        self._set_activity("● Ready", state="ready")

    def _on_speech_finished(self):
        """Callback when TTS finishes speaking naturally."""
        QTimer.singleShot(0, self._handle_speech_finished_ui)

    def _handle_speech_finished_ui(self):
        self.stop_speak_btn.setVisible(False)
        self._set_activity("● Ready", state="ready")

    # ==========================================
    # Conversation Actions & Status
    # ==========================================

    def _on_clear_chat(self):
        """Clear current conversation history."""
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            "Are you sure you want to clear the conversation history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.memory.clear_session(self.session_id)
            self.chat_area.clear()
            self.chat_area.add_message(
                role="assistant",
                text="Conversation history cleared. How can I help you today?"
            )

    def _set_activity(self, text: str, state: str = "ready"):
        """Update activity indicator badge styling."""
        self.activity_badge.setText(text)
        self.activity_badge.setProperty("state", state)
        self.activity_badge.style().unpolish(self.activity_badge)
        self.activity_badge.style().polish(self.activity_badge)
