"""
Ollama Brain: Local AI Engine with Dynamic Model Detection, Native Tool Calling,
and Robust Structured Fallback.
Strictly local inference (localhost:11434). Zero cloud fallback.
"""

import json
import re
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple

from config import OLLAMA_HOST, DEFAULT_MODEL, OLLAMA_TIMEOUT, SYSTEM_PROMPT
from core.registry import tool_registry, ToolResult

logger = logging.getLogger(__name__)


class OllamaBrain:
    def __init__(self, host: str = OLLAMA_HOST, model: str = DEFAULT_MODEL):
        self.host = host.rstrip("/")
        self.model = model
        self.has_native_tools: Optional[bool] = None

    def check_connection(self) -> Tuple[bool, str]:
        """Check whether local Ollama server is reachable."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return True, "Connected to Ollama"
            return False, f"Ollama returned HTTP {resp.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Please ensure Ollama is running locally on port 11434."
        except Exception as e:
            return False, f"Ollama connection error: {str(e)}"

    def list_installed_models(self) -> List[str]:
        """Dynamically detect and return list of installed Ollama models."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return models
            return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    def set_model(self, model_name: str):
        """Switch active Ollama model and reset tool verification."""
        self.model = model_name
        self.has_native_tools = None
        logger.info(f"Ollama model switched to: {model_name}")

    def verify_tool_calling_support(self, model_name: Optional[str] = None) -> bool:
        """
        Test whether the model supports native Ollama function calling.
        Cached per model.
        """
        target_model = model_name or self.model
        if self.has_native_tools is not None and target_model == self.model:
            return self.has_native_tools

        test_payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": "Open Notepad"}],
            "tools": tool_registry.get_schemas(),
            "stream": False
        }
        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json=test_payload,
                timeout=30
            )
            if resp.status_code == 200:
                result = resp.json()
                msg = result.get("message", {})
                # If it accepted the tool schema and didn't fail with a 400/500, it supports native tools
                self.has_native_tools = True
                return True
            else:
                logger.warning(f"Native tool check failed with code {resp.status_code}: {resp.text}")
                self.has_native_tools = False
                return False
        except Exception as e:
            logger.warning(f"Exception during native tool test: {e}")
            self.has_native_tools = False
            return False

    def process_turn(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a user message through the local Ollama LLM.
        Distinguishes between conversation mode and desktop action mode.
        Returns a dict:
        {
            "content": str,               # Text response to show user
            "executed_tools": list,       # List of tool execution results
            "mode": "conversation"|"action",
            "error": Optional[str]
        }
        """
        # Ensure connection
        connected, msg = self.check_connection()
        if not connected:
            return {
                "content": f"Ollama connection error: {msg}. Please start Ollama (`ollama serve`) and try again.",
                "executed_tools": [],
                "mode": "conversation",
                "error": msg
            }

        # Check tool calling capability if not determined yet
        if self.has_native_tools is None:
            self.verify_tool_calling_support()

        if self.has_native_tools:
            return self._process_native_tools(user_message, conversation_history)
        else:
            return self._process_structured_fallback(user_message, conversation_history)

    def _process_native_tools(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process turn using Ollama's native tool calling."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Append recent history (last 10 turns)
        for h in conversation_history[-10:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tool_registry.get_schemas(),
            "stream": False
        }

        try:
            resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT)
            if resp.status_code != 200:
                logger.warning(f"Native tool call returned {resp.status_code}. Falling back to structured mode.")
                return self._process_structured_fallback(user_message, conversation_history)

            res_json = resp.json()
            message = res_json.get("message", {})
            content = message.get("content", "").strip()
            tool_calls = message.get("tool_calls", [])

            # Case 1: Pure conversation mode (no tool calls)
            if not tool_calls:
                return {
                    "content": content if content else "Main yahan hoon, bataiye main aapki kya madad kar sakta hoon?",
                    "executed_tools": [],
                    "mode": "conversation",
                    "error": None
                }

            # Case 2: Action mode (model emitted tool calls)
            executed_results = []
            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name")
                tool_args = fn.get("arguments", {})
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except Exception:
                        tool_args = {}

                logger.info(f"Executing approved tool: {tool_name} with args: {tool_args}")
                result = tool_registry.execute(tool_name, tool_args)
                executed_results.append(result.to_dict())

            # Send tool outputs back to LLM to formulate a polite, context-aware closing response
            followup_messages = list(messages)
            followup_messages.append(message)
            for er in executed_results:
                followup_messages.append({
                    "role": "tool",
                    "content": json.dumps(er)
                })

            followup_payload = {
                "model": self.model,
                "messages": followup_messages,
                "stream": False
            }

            try:
                followup_resp = requests.post(f"{self.host}/api/chat", json=followup_payload, timeout=60)
                if followup_resp.status_code == 200:
                    final_content = followup_resp.json().get("message", {}).get("content", "").strip()
                else:
                    final_content = ""
            except Exception as e:
                logger.warning(f"Error getting tool follow-up response: {e}")
                final_content = ""

            # If LLM didn't produce a follow-up string, produce a natural default summary
            if not final_content:
                summaries = [er.get("message", "Action performed.") for er in executed_results]
                final_content = " ".join(summaries)

            return {
                "content": final_content,
                "executed_tools": executed_results,
                "mode": "action",
                "error": None
            }

        except Exception as e:
            logger.error(f"Error in _process_native_tools: {e}")
            return {
                "content": f"An error occurred while communicating with Ollama: {str(e)}",
                "executed_tools": [],
                "mode": "conversation",
                "error": str(e)
            }

    def _process_structured_fallback(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Safe fallback mechanism when the model doesn't support native tool calling.
        Uses structured prompt engineering to detect actions vs conversation.
        """
        available_tools = tool_registry.get_tool_names()
        fallback_prompt = f"""{SYSTEM_PROMPT}

AVAILABLE DESKTOP TOOLS:
1. open_chrome() -> Open Google Chrome browser.
2. open_notepad() -> Open Notepad.
3. open_calculator() -> Open Windows Calculator.
4. open_youtube(query="optional search query") -> Open YouTube (optionally search).
5. open_google(query="optional search query") -> Open Google (optionally search).

RULES:
- If the user is asking a question or just chatting, set "type": "conversation" and provide your response in "reply".
- If the user wants to execute an action (e.g. open an app, search YouTube/Google), set "type": "action", specify "tool_name", and "arguments".
- Respond ONLY with valid JSON in this exact format:
```json
{{
  "type": "conversation" | "action",
  "reply": "Your conversational reply here (if conversation)",
  "tool_name": "name_of_tool_or_null",
  "arguments": {{}}
}}
```
Do not include any text before or after the JSON.
"""
        messages = [{"role": "system", "content": fallback_prompt}]
        for h in conversation_history[-10:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "format": "json"
                },
                timeout=OLLAMA_TIMEOUT
            )
            if resp.status_code != 200:
                return {
                    "content": f"Ollama error: HTTP {resp.status_code}",
                    "executed_tools": [],
                    "mode": "conversation",
                    "error": resp.text
                }

            raw_text = resp.json().get("message", {}).get("content", "").strip()
            parsed = self._extract_json(raw_text)

            if parsed and parsed.get("type") == "action":
                tool_name = parsed.get("tool_name")
                args = parsed.get("arguments", {})
                if tool_name in available_tools:
                    result = tool_registry.execute(tool_name, args)
                    res_dict = result.to_dict()
                    reply = parsed.get("reply") or result.message
                    return {
                        "content": reply,
                        "executed_tools": [res_dict],
                        "mode": "action",
                        "error": None
                    }

            # Default conversational fallback
            content = parsed.get("reply") if parsed else raw_text
            return {
                "content": content or "Main aapki kya madad kar sakta hoon?",
                "executed_tools": [],
                "mode": "conversation",
                "error": None
            }

        except Exception as e:
            logger.error(f"Structured fallback error: {e}")
            return {
                "content": f"Processing error: {str(e)}",
                "executed_tools": [],
                "mode": "conversation",
                "error": str(e)
            }

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON object from LLM response safely."""
        try:
            return json.loads(text)
        except Exception:
            pass

        # Match markdown ```json ... ``` or first { ... }
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        return None
