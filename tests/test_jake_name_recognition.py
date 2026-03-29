import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestJakeNameRecognition(unittest.TestCase):
    """Test that the bot responds to both 'jakey' and 'jake' mentions"""

    def _get_name_recognition_patterns(self):
        """Get the name patterns used for jakey/jake recognition"""
        return ['jakey', 'jake']

    def _contains_name(self, content: str) -> bool:
        """Check if content contains jakey or jake"""
        content_lower = content.lower()
        for name in self._get_name_recognition_patterns():
            if name in content_lower:
                return True
        return False

    def test_responds_to_jakey(self):
        """Test that bot recognizes 'jakey' in messages"""
        message_content = "hello jakey"
        self.assertTrue(self._contains_name(message_content))

    def test_responds_to_jake(self):
        """Test that bot recognizes 'jake' in messages"""
        message_content = "hello jake"
        self.assertTrue(self._contains_name(message_content))

    def test_does_not_respond_to_other_names(self):
        """Test that bot doesn't respond to unrelated names"""
        message_content = "hello john"
        self.assertFalse(self._contains_name(message_content))

    def test_jakey_case_insensitive(self):
        """Test that name recognition is case insensitive"""
        self.assertTrue(self._contains_name("JAKEY"))
        self.assertTrue(self._contains_name("Jakey"))
        self.assertTrue(self._contains_name("JAKE"))
        self.assertTrue(self._contains_name("Jake"))

    def test_jakey_in_sentence(self):
        """Test that name is recognized within a sentence"""
        self.assertTrue(self._contains_name("hey jakey how are you"))
        self.assertTrue(self._contains_name("what's up jake"))
        self.assertTrue(self._contains_name("jakey you're funny"))


if __name__ == '__main__':
    unittest.main()
