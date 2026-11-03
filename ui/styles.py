"""
Modern ChatGPT-like Dark Theme Stylesheet for PySide6 Desktop GUI.
Designed with high contrast, crisp typography, and sleek conversational aesthetics.
"""

DARK_THEME_QSS = """
/* Global Window Styling */
QMainWindow, QWidget {
    background-color: #0f1015;
    color: #f1f5f9;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "SF Pro Display", Roboto, sans-serif;
    font-size: 14px;
}

/* Header Container */
#headerFrame {
    background-color: #171821;
    border-bottom: 1px solid #252836;
    padding: 12px 20px;
}

#appLogo {
    font-size: 19px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}

#localTag {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}

/* Status Badges */
.statusPill {
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}

#ollamaStatusBadge {
    background-color: #14271f;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}

#ollamaStatusBadge[offline="true"] {
    background-color: #2e1515;
    color: #f87171;
    border: 1px solid #dc2626;
}

#activityBadge {
    background-color: #1a1e29;
    color: #94a3b8;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 600;
}

#activityBadge[state="ready"] {
    background-color: #14271f;
    color: #34d399;
    border-color: #059669;
}

#activityBadge[state="thinking"] {
    background-color: #172554;
    color: #60a5fa;
    border-color: #2563eb;
}

#activityBadge[state="speaking"] {
    background-color: #2e1065;
    color: #c084fc;
    border-color: #7c3aed;
}

#activityBadge[state="listening"] {
    background-color: #450a0a;
    color: #fca5a5;
    border-color: #ef4444;
}

#activityBadge[state="transcribing"] {
    background-color: #451a03;
    color: #fcd34d;
    border-color: #d97706;
}

/* Model Selector Combobox */
QComboBox {
    background-color: #202330;
    color: #f1f5f9;
    border: 1px solid #373b4e;
    border-radius: 8px;
    padding: 6px 14px;
    min-width: 180px;
    font-weight: 600;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #10a37f;
    background-color: #252938;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #202330;
    color: #f1f5f9;
    selection-background-color: #10a37f;
    selection-color: #ffffff;
    border: 1px solid #373b4e;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}

/* General Header Action Buttons */
QPushButton#actionBtn {
    background-color: #202330;
    color: #e2e8f0;
    border: 1px solid #373b4e;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton#actionBtn:hover {
    background-color: #2a2e40;
    border-color: #4a5068;
    color: #ffffff;
}

QPushButton#stopSpeakBtn {
    background-color: #3f1218;
    color: #fda4af;
    border: 1px solid #9f1239;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton#stopSpeakBtn:hover {
    background-color: #641924;
    color: #ffffff;
    border-color: #be123c;
}

/* Chat Scroll Area */
QScrollArea#chatScrollArea {
    border: none;
    background-color: #0f1015;
}

QWidget#chatContainer {
    background-color: #0f1015;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background: #2a2d3d;
    min-height: 32px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #3f435b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Bottom Input Bar */
#inputFrame {
    background-color: #171821;
    border-top: 1px solid #252836;
    padding: 14px 24px;
}

#inputCapsule {
    background-color: #202330;
    border: 1px solid #373b4e;
    border-radius: 14px;
    padding: 4px 8px;
}

#inputCapsule:focus-within {
    border: 1.5px solid #10a37f;
    background-color: #232736;
}

QTextEdit#chatInputField {
    background-color: transparent;
    color: #ffffff;
    border: none;
    padding: 8px 10px;
    font-size: 14px;
    line-height: 1.5;
}

/* Mic Button */
QPushButton#micBtn {
    background-color: #2a2e40;
    color: #e2e8f0;
    border: 1px solid #3e445e;
    border-radius: 10px;
    font-size: 16px;
}

QPushButton#micBtn:hover {
    background-color: #363b52;
    border-color: #10a37f;
}

QPushButton#micBtn[recording="true"] {
    background-color: #dc2626;
    color: #ffffff;
    border-color: #ef4444;
}

/* Send Button */
QPushButton#sendBtn {
    background-color: #10a37f;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 700;
    font-size: 14px;
}

QPushButton#sendBtn:hover {
    background-color: #0d8a6b;
}

QPushButton#sendBtn:disabled {
    background-color: #252936;
    color: #64748b;
}
"""
