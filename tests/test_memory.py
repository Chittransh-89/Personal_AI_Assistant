"""
Unit tests for SQLite persistent memory manager.
"""

import unittest
import tempfile
from pathlib import Path
from core.memory import MemoryManager


class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_memory.db"
        self.memory = MemoryManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_messages(self):
        session_id = "test-session-1"
        self.memory.save_message(session_id, "user", "Hello assistant")
        self.memory.save_message(session_id, "assistant", "Hello! How can I help you?")

        history = self.memory.get_session_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello assistant")
        self.assertEqual(history[1]["role"], "assistant")

    def test_clear_session(self):
        session_id = "test-session-2"
        self.memory.save_message(session_id, "user", "Message to delete")
        self.memory.clear_session(session_id)
        history = self.memory.get_session_history(session_id)
        self.assertEqual(len(history), 0)

    def test_long_term_facts(self):
        self.memory.set_fact("user_name", "Developer")
        self.memory.set_fact("favorite_editor", "VS Code")

        self.assertEqual(self.memory.get_fact("user_name"), "Developer")
        self.assertEqual(self.memory.get_fact("favorite_editor"), "VS Code")

        all_facts = self.memory.get_all_facts()
        self.assertIn("user_name", all_facts)
        self.assertIn("favorite_editor", all_facts)


if __name__ == "__main__":
    unittest.main()
