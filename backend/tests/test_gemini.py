import os
import unittest
from unittest.mock import patch, MagicMock

from services.gemini_service import GeminiService


class GeminiServiceTestCase(unittest.TestCase):
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}, clear=True)
    @patch("services.gemini_service.genai.GenerativeModel")
    def test_chat_returns_text_on_success(self, MockModel):
        # Mock model instance and its generate_content return value
        mock_instance = MockModel.return_value
        mock_response = MagicMock()
        mock_response.text = "hello from gemini"
        mock_instance.generate_content.return_value = mock_response

        svc = GeminiService()
        out = svc.chat("hi")

        MockModel.assert_called_once_with("gemini-2.5-flash")
        mock_instance.generate_content.assert_called_once_with("hi")
        self.assertEqual(out, "hello from gemini")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}, clear=True)
    @patch("services.gemini_service.genai.GenerativeModel")
    def test_chat_handles_exceptions(self, MockModel):
        mock_instance = MockModel.return_value
        mock_instance.generate_content.side_effect = RuntimeError("boom")

        svc = GeminiService()
        out = svc.chat("hi")

        self.assertIn("Error:", out)
        self.assertIn("boom", out)

        
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_raises_without_api_key(self):
        """
        If GEMINI_API_KEY is not set, GeminiService.__init__ should raise ValueError.
        """
        with self.assertRaises(ValueError):
            GeminiService()
