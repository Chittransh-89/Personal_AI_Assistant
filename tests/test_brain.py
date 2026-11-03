"""
Unit tests for Ollama Brain and structured fallback parser.
"""

import unittest
from core.ollama_brain import OllamaBrain


class TestOllamaBrain(unittest.TestCase):
    def setUp(self):
        self.brain = OllamaBrain(model="gemma4:e4b")

    def test_json_extractor_clean(self):
        raw = '{"type": "action", "tool_name": "open_notepad", "arguments": {}}'
        extracted = self.brain._extract_json(raw)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("tool_name"), "open_notepad")

    def test_json_extractor_markdown_block(self):
        raw = '''Here is the response:
```json
{
  "type": "conversation",
  "reply": "Python is a versatile programming language.",
  "tool_name": null,
  "arguments": {}
}
```
Hope that helps!'''
        extracted = self.brain._extract_json(raw)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("type"), "conversation")
        self.assertEqual(extracted.get("reply"), "Python is a versatile programming language.")

    def test_json_extractor_invalid(self):
        raw = "This is not json at all."
        extracted = self.brain._extract_json(raw)
        self.assertIsNone(extracted)


if __name__ == "__main__":
    unittest.main()
