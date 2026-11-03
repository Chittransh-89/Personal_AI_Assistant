"""
Strict Allowlisted Desktop Tool Registry and Safe Execution Engine.
No arbitrary shell execution, no eval/exec. All tools and parameters are strictly validated.
"""

import subprocess
import webbrowser
import urllib.parse
import os
import sys
import logging
from typing import Dict, Any, Callable, Optional, List

logger = logging.getLogger(__name__)


class ToolResult:
    def __init__(self, success: bool, message: str, tool_name: str, data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.tool_name = tool_name
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "message": self.message,
            "data": self.data
        }


# ==========================================
# Tool Implementations
# ==========================================

def _find_chrome_executable() -> Optional[str]:
    """Find the path to Google Chrome on Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def open_chrome() -> Dict[str, Any]:
    """Open Google Chrome web browser."""
    chrome_path = _find_chrome_executable()
    try:
        if chrome_path:
            subprocess.Popen([chrome_path])
            return {"success": True, "message": "Google Chrome launched successfully."}
        else:
            # Fallback to os.startfile or default browser
            try:
                os.startfile("chrome.exe")
                return {"success": True, "message": "Google Chrome launched via system registry."}
            except Exception:
                webbrowser.open("https://www.google.com")
                return {"success": True, "message": "Opened default browser."}
    except Exception as e:
        logger.error(f"Failed to open Chrome: {e}")
        return {"success": False, "message": f"Failed to launch Chrome: {str(e)}"}


def open_notepad() -> Dict[str, Any]:
    """Open Windows Notepad application."""
    try:
        subprocess.Popen(["notepad.exe"])
        return {"success": True, "message": "Notepad opened successfully."}
    except Exception as e:
        logger.error(f"Failed to open Notepad: {e}")
        return {"success": False, "message": f"Failed to launch Notepad: {str(e)}"}


def open_calculator() -> Dict[str, Any]:
    """Open Windows Calculator application."""
    try:
        subprocess.Popen(["calc.exe"])
        return {"success": True, "message": "Calculator opened successfully."}
    except Exception as e:
        logger.error(f"Failed to open Calculator: {e}")
        return {"success": False, "message": f"Failed to launch Calculator: {str(e)}"}


def open_youtube(query: Optional[str] = None) -> Dict[str, Any]:
    """
    Open YouTube. If a query is provided, search YouTube for that query.
    """
    clean_query = (query or "").strip()
    try:
        if clean_query:
            encoded = urllib.parse.quote_plus(clean_query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            webbrowser.open(url)
            return {"success": True, "message": f"Opened YouTube search for: '{clean_query}'"}
        else:
            webbrowser.open("https://www.youtube.com")
            return {"success": True, "message": "Opened YouTube homepage."}
    except Exception as e:
        logger.error(f"Failed to open YouTube: {e}")
        return {"success": False, "message": f"Failed to open YouTube: {str(e)}"}


def open_google(query: Optional[str] = None) -> Dict[str, Any]:
    """
    Open Google. If a query is provided, search Google for that query.
    """
    clean_query = (query or "").strip()
    try:
        if clean_query:
            encoded = urllib.parse.quote_plus(clean_query)
            url = f"https://www.google.com/search?q={encoded}"
            webbrowser.open(url)
            return {"success": True, "message": f"Opened Google search for: '{clean_query}'"}
        else:
            webbrowser.open("https://www.google.com")
            return {"success": True, "message": "Opened Google homepage."}
    except Exception as e:
        logger.error(f"Failed to open Google: {e}")
        return {"success": False, "message": f"Failed to open Google: {str(e)}"}


# ==========================================
# Strict Tool Registry
# ==========================================

class ToolRegistry:
    """Strictly controlled registry of safe, allowlisted tools."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []
        self._register_default_tools()

    def _register_default_tools(self):
        self.register(
            name="open_chrome",
            func=open_chrome,
            description="Open Google Chrome browser on the desktop.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        self.register(
            name="open_notepad",
            func=open_notepad,
            description="Open the Windows Notepad text editor.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        self.register(
            name="open_calculator",
            func=open_calculator,
            description="Open the Windows Calculator application.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
        self.register(
            name="open_youtube",
            func=open_youtube,
            description="Open YouTube in the browser. Optionally search for a specific video, topic, or query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or video topic to search on YouTube (e.g. 'Python tutorial', 'latest news')"
                    }
                },
                "required": []
            }
        )
        self.register(
            name="open_google",
            func=open_google,
            description="Open Google search in the browser with an optional search query.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search on Google (e.g. 'weather in Delhi', 'Python documentation')"
                    }
                },
                "required": []
            }
        )

    def register(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """Register an allowlisted tool with its schema."""
        self._tools[name] = func
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return Ollama-compatible function schemas."""
        return self._schemas

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Safely execute an allowlisted tool by name with validated arguments.
        Rejects any unregistered tool or invalid parameters.
        """
        if tool_name not in self._tools:
            logger.warning(f"Attempted execution of unauthorized tool: '{tool_name}'")
            return ToolResult(
                success=False,
                message=f"Security violation: Tool '{tool_name}' is not in the approved allowlist.",
                tool_name=tool_name
            )

        args = arguments or {}
        if not isinstance(args, dict):
            return ToolResult(
                success=False,
                message=f"Invalid arguments for tool '{tool_name}'. Expected dictionary.",
                tool_name=tool_name
            )

        try:
            func = self._tools[tool_name]
            # Safely invoke function with expected kwargs
            if tool_name in ("open_chrome", "open_notepad", "open_calculator"):
                res = func()
            elif tool_name in ("open_youtube", "open_google"):
                query = args.get("query")
                res = func(query=query)
            else:
                res = func(**args)

            success = res.get("success", False)
            msg = res.get("message", "Execution finished.")
            return ToolResult(success=success, message=msg, tool_name=tool_name, data=res)
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                message=f"Tool execution failed: {str(e)}",
                tool_name=tool_name
            )


# Global singleton registry
tool_registry = ToolRegistry()
