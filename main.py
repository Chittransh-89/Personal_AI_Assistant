"""
Main Entry Point for Nova Personal AI Desktop Assistant.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication

from config import DEFAULT_MODEL
from core.ollama_brain import OllamaBrain
from core.memory import MemoryManager
from voice.stt import STTEngine
from voice.tts import TTSEngine
from ui.main_window import MainWindow
from ui.styles import DARK_THEME_QSS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("NovaDesktopApp")


def main():
    logger.info("Initializing Nova Personal AI Assistant...")

    # Initialize Core Engines
    memory = MemoryManager()
    brain = OllamaBrain(model=DEFAULT_MODEL)
    stt = STTEngine()
    tts = TTSEngine()

    # Pre-check Ollama status
    connected, conn_msg = brain.check_connection()
    if connected:
        logger.info(f"Ollama server connected. Detected models: {brain.list_installed_models()}")
    else:
        logger.warning(f"Ollama warning at startup: {conn_msg}")

    # Start PySide6 Application
    app = QApplication(sys.argv)
    app.setApplicationName("Nova AI Assistant")
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow(brain=brain, memory=memory, stt=stt, tts=tts)
    window.show()

    logger.info("Nova Desktop Assistant GUI launched successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
