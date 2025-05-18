import unittest
import sqlite3
from datetime import datetime
from database_related import (
    init_database, load_chat_history, save_chat_message, 
    clear_chat_history, view_chat_history, update_daily_experience,
    set_db_file, print_database_content
)
from utils import (
    init_daily_experiences, get_todays_experience, 
    update_todays_experience, check_for_new_experience
)
from unittest.mock import patch, MagicMock

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Initialize test database
        self.test_db = "test_chat_history.db"
        set_db_file(self.test_db)
        from utils import set_db_file as set_utils_db_file
        set_utils_db_file(self.test_db)
        
        # Initialize all required tables first
        init_database()
        init_daily_experiences()
        
        # Then create the connection
        self.conn = sqlite3.connect(self.test_db)
        self.cursor = self.conn.cursor()

        # Insert initial daily experience
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('INSERT OR REPLACE INTO daily_experiences (date, experience) VALUES (?, ?)',
                          (today, "Initial test experience"))
        self.conn.commit()

    def tearDown(self):
        # Clean up after tests
        self.conn.close()
        import os
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_chat_history(self):
        # Test saving and loading chat messages
        test_message = "Hello, this is a test message"
        save_chat_message("user", test_message)
        save_chat_message("assistant", "Test response")

        history = load_chat_history("test system prompt")
        self.assertEqual(len(history), 3)  # system prompt + 2 messages
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[1]["content"], test_message)
        self.assertEqual(history[2]["role"], "assistant")
        self.assertEqual(history[2]["content"], "Test response")

    @patch('utils.client.chat.completions.create')
    def test_daily_experiences(self, mock_create):
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.arguments = '{"new_experiences": ["I went to the park today and had a great time!"]}'
        mock_create.return_value = mock_response

        # Test daily experience functionality
        today = datetime.now().strftime('%Y-%m-%d')
        test_experience = "Today was a test day"

        # Test updating experience
        update_daily_experience(test_experience)

        # Verify the experience was saved
        self.cursor.execute("SELECT experience FROM daily_experiences WHERE date = ?", (today,))
        saved_experience = self.cursor.fetchone()
        self.assertIsNotNone(saved_experience)
        self.assertEqual(saved_experience[0], test_experience)

        # Test getting today's experience
        experience = get_todays_experience()
        self.assertEqual(experience, test_experience)

        # Test experience update through check_for_new_experience
        new_experience = "I went to the park today and had a great time!"
        updated = check_for_new_experience(new_experience, experience)
        self.assertIsInstance(updated, str)
        self.assertIn("I went to the park today and had a great time!", updated)

    @patch('builtins.input', return_value='y')
    def test_clear_chat_history(self, mock_input):
        # Test clearing chat history
        save_chat_message("user", "Test message")
        save_chat_message("assistant", "Test response")

        # Verify messages were saved
        history = load_chat_history("test system prompt")
        self.assertEqual(len(history), 3)

        # Clear history and verify
        clear_chat_history()
        history = load_chat_history("test system prompt")
        self.assertEqual(len(history), 1)  # Only system prompt remains

if __name__ == '__main__':
    unittest.main()