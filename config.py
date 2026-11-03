"""
Configuration settings for Personal Windows Desktop AI Assistant.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "assistant_memory.db"

# Ollama Settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "gemma4:e4b"
OLLAMA_TIMEOUT = 120  # seconds

# Audio / Voice Settings
WHISPER_MODEL_SIZE = "base"     # 'tiny' or 'base' run exceptionally fast on CPU with int8
WHISPER_DEVICE = "cpu"          # Keep on CPU to preserve 100% RTX 4050 6GB VRAM for Ollama LLM
WHISPER_COMPUTE_TYPE = "int8"
AUDIO_SAMPLE_RATE = 16000

# Text To Speech Settings
TTS_RATE = 185                  # Words per minute
TTS_VOLUME = 1.0

# System Prompt for Assistant
SYSTEM_PROMPT = """You are Nova, a helpful, intelligent, and highly capable personal desktop AI assistant running locally on Windows.

Important guidelines:
1. CONVERSATION MODE:
   - When the user asks general questions, requests explanations, chats, or asks for advice (e.g. "Explain Python decorators", "Tell me a joke", "What is machine learning?", "How are you?"), answer naturally and politely in conversation mode.
   - DO NOT call any tool when answering regular conversational queries.

2. ACTION MODE:
   - When the user specifically requests to open an application or search the web (e.g., "Open Chrome", "Notepad kholo", "YouTube par Python tutorial search karo", "Open calculator", "Google par weather in Delhi search karo"), use the appropriate tool.
   - Always choose the exact matching tool from your available tools.

3. MULTILINGUAL SUPPORT:
   - You fully understand English, Hindi, and Hinglish.
   - Always respond naturally in the same language or blend (English, Hindi, or Hinglish) that the user addresses you in.

4. ACCURACY:
   - Never pretend that an action succeeded if you did not execute the tool or if it returned an error.
   - Be concise, clear, and friendly.
"""
