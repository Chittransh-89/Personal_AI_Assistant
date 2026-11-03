"""
Unit tests for safe allowlisted Desktop Tools.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.registry import tool_registry, ToolResult


class TestDesktopTools(unittest.TestCase):
    def test_registered_tools_exist(self):
        """Ensure all 5 required tools are registered in allowlist."""
        expected = ["open_chrome", "open_notepad", "open_calculator", "open_youtube", "open_google"]
        names = tool_registry.get_tool_names()
        for t in expected:
            self.assertIn(t, names)

    def test_unauthorized_tool_rejected(self):
        """Ensure unauthorized tools cannot be executed."""
        result = tool_registry.execute("format_hard_drive", {})
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.message)

    def test_invalid_arguments_rejected(self):
        """Ensure arguments must be a dictionary."""
        result = tool_registry.execute("open_notepad", "malicious_string_not_dict")
        self.assertFalse(result.success)

    @patch("webbrowser.open")
    def test_open_youtube_with_query(self, mock_browser):
        result = tool_registry.execute("open_youtube", {"query": "Python tutorial"})
        self.assertTrue(result.success)
        mock_browser.assert_called_once()
        called_url = mock_browser.call_args[0][0]
        self.assertIn("youtube.com/results?search_query=Python+tutorial", called_url)

    @patch("webbrowser.open")
    def test_open_google_with_query(self, mock_browser):
        result = tool_registry.execute("open_google", {"query": "weather in Delhi"})
        self.assertTrue(result.success)
        mock_browser.assert_called_once()
        called_url = mock_browser.call_args[0][0]
        self.assertIn("google.com/search?q=weather+in+Delhi", called_url)

    @patch("subprocess.Popen")
    def test_open_notepad(self, mock_popen):
        result = tool_registry.execute("open_notepad", {})
        self.assertTrue(result.success)
        mock_popen.assert_called_once_with(["notepad.exe"])

    @patch("subprocess.Popen")
    def test_open_calculator(self, mock_popen):
        result = tool_registry.execute("open_calculator", {})
        self.assertTrue(result.success)
        mock_popen.assert_called_once_with(["calc.exe"])


if __name__ == "__main__":
    unittest.main()
