"""
Modern ChatGPT-like Scrollable Chat Interface with High-Contrast Message Bubbles
and Action Badges.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import html

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy
)


class ToolBadgeWidget(QFrame):
    """Visual card displaying desktop action execution details."""
    def __init__(self, tool_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        success = tool_info.get("success", False)
        tool_name = tool_info.get("tool", "desktop_tool")
        message = tool_info.get("message", "")

        bg_color = "#0e2a22" if success else "#2e1215"
        border_color = "#10b981" if success else "#ef4444"
        text_color = "#a7f3d0" if success else "#fca5a5"
        icon = "✓" if success else "✗"
        status_text = "Success" if success else "Failed"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        header = QLabel(f"<b>⚙ Desktop Tool:</b> <code>{html.escape(tool_name)}</code> &nbsp; <span style='color: {border_color}; font-weight: bold;'>[{icon} {status_text}]</span>")
        header.setTextFormat(Qt.RichText)
        header.setStyleSheet("font-size: 12px; color: #ffffff;")
        layout.addWidget(header)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet(f"font-size: 12px; color: {text_color}; font-family: Segoe UI, sans-serif;")
            layout.addWidget(msg_lbl)


class MessageBubble(QFrame):
    """
    High-contrast ChatGPT-like message bubble for user and AI assistant.
    Features selectable text, markdown rendering, avatars, and timestamps.
    """
    def __init__(
        self,
        role: str,
        text: str,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.role = role
        is_user = (role == "user")

        # Frame Styling
        if is_user:
            self.setStyleSheet("""
                QFrame#bubbleFrame {
                    background-color: #2563eb;
                    border: 1px solid #3b82f6;
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom-left-radius: 16px;
                    border-bottom-right-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#bubbleFrame {
                    background-color: #1e2029;
                    border: 1px solid #2f3445;
                    border-top-left-radius: 16px;
                    border-top-right-radius: 16px;
                    border-bottom-left-radius: 4px;
                    border-bottom-right-radius: 16px;
                }
            """)
        self.setObjectName("bubbleFrame")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 1. Header Bar (Avatar + Name + Time)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        time_str = timestamp or datetime.now().strftime("%I:%M %p")
        if is_user:
            badge_html = "<span style='background-color: #1d4ed8; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>👤 You</span>"
        else:
            badge_html = "<span style='background-color: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 4px; font-weight: bold;'>✨ Nova AI</span>"

        sender_label = QLabel(f"{badge_html} &nbsp; <span style='color: #94a3b8; font-size: 11px;'>{time_str}</span>")
        sender_label.setTextFormat(Qt.RichText)
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. Content Label (Rich Text Markdown)
        if text.strip():
            content_lbl = self._create_content_label(text, is_user)
            layout.addWidget(content_lbl)

        # 3. Tool execution badges
        if tool_results:
            for tr in tool_results:
                badge = ToolBadgeWidget(tr, self)
                layout.addWidget(badge)

    def _create_content_label(self, raw_text: str, is_user: bool) -> QLabel:
        """Render markdown text with styled high-contrast HTML."""
        doc = QTextDocument()
        doc.setMarkdown(raw_text)
        html_body = doc.toHtml()

        text_color = "#ffffff" if is_user else "#f8fafc"
        code_bg = "#1d4ed8" if is_user else "#121318"
        code_color = "#ffffff" if is_user else "#38bdf8"
        link_color = "#bfdbfe" if is_user else "#60a5fa"

        styled_html = f"""
        <html>
        <head>
        <style>
            body {{
                color: {text_color};
                font-family: "Segoe UI", -apple-system, Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.55;
                margin: 0;
                padding: 0;
            }}
            p {{
                margin: 0 0 8px 0;
            }}
            p:last-child {{
                margin-bottom: 0px;
            }}
            code {{
                background-color: {code_bg};
                color: {code_color};
                font-family: "Consolas", "Courier New", monospace;
                font-size: 13px;
                padding: 2px 6px;
                border-radius: 4px;
            }}
            pre {{
                background-color: {code_bg};
                color: {code_color};
                font-family: "Consolas", "Courier New", monospace;
                padding: 10px 12px;
                border-radius: 6px;
                margin: 6px 0;
            }}
            ul, ol {{
                margin: 4px 0 8px 18px;
                padding: 0;
            }}
            li {{
                margin-bottom: 4px;
            }}
            a {{
                color: {link_color};
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        lbl = QLabel()
        lbl.setTextFormat(Qt.RichText)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        lbl.setOpenExternalLinks(True)
        lbl.setWordWrap(True)
        lbl.setText(styled_html)
        lbl.setStyleSheet("background: transparent; border: none; padding: 0;")
        return lbl


class ChatArea(QScrollArea):
    """Scrollable container managing chat message history."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatScrollArea")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container = QWidget()
        self.container.setObjectName("chatContainer")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(18)
        self.layout.addStretch()

        self.setWidget(self.container)
        self._bubbles: List[MessageBubble] = []

    def add_message(
        self,
        role: str,
        text: str,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[str] = None
    ):
        """Add a new message bubble to the chat."""
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        bubble = MessageBubble(role, text, tool_results, timestamp, parent=row_widget)
        self._bubbles.append(bubble)
        self._apply_bubble_max_width(bubble)

        if role == "user":
            row_layout.addStretch()
            row_layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            row_layout.addWidget(bubble, 0, Qt.AlignLeft)
            row_layout.addStretch()

        # Insert before trailing stretch
        count = self.layout.count()
        self.layout.insertWidget(count - 1, row_widget)

        # Smooth auto-scroll
        QTimer.singleShot(50, self.scroll_to_bottom)

    def _apply_bubble_max_width(self, bubble: MessageBubble):
        """Keep bubbles elegantly proportioned relative to window size."""
        current_width = self.viewport().width()
        if current_width > 200:
            ratio = 0.72 if bubble.role == "user" else 0.80
            max_w = max(420, int(current_width * ratio))
            bubble.setMaximumWidth(max_w)
        else:
            bubble.setMaximumWidth(750)

    def resizeEvent(self, event):
        """Dynamically adapt message bubble widths on window resize."""
        super().resizeEvent(event)
        for bubble in self._bubbles:
            self._apply_bubble_max_width(bubble)

    def scroll_to_bottom(self):
        """Scroll vertical bar smoothly to the newest message."""
        v_bar = self.verticalScrollBar()
        v_bar.setValue(v_bar.maximum())

    def clear(self):
        """Clear all messages from the conversation view."""
        self._bubbles.clear()
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
