import unittest
from app import create_app

class TestBaymaxChatbot(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_ui_access_authenticated(self):
        # Simulate UI access — for API, always available
        # You might check /health endpoint for liveness
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)

    def test_submit_health_question(self):
        # Valid health question, expected normal response
        resp = self.client.post('/api/chat', json={"message":"What are symptoms of dehydration?", "user_id":"user_a"})
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("dehydration", data["response"].lower())
        self.assertEqual(data["classification"], "SYMPTOM")

    def test_follow_up_question(self):
        # Valid follow-up, classification could be different
        resp = self.client.post('/api/chat', json={"message":"What foods should I avoid?", "user_id":"user_a"})
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(isinstance(data["response"], str))

    def test_block_empty_query(self):
        # Empty message, expect error
        resp = self.client.post('/api/chat', json={"message":"", "user_id":"user_a"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_anonymous_conversation_logging(self):
        # Valid query, should generate a response and trigger logging
        resp = self.client.post('/api/chat', json={"message":"How do I treat a cold?", "user_id":"user_a"})
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("response", data)
        # For deeper checks, query MongoDB or mock it

    def test_user_specific_chat_history(self):
        # Send messages as two users, check endpoints work (history tested in DB)
        r1 = self.client.post('/api/chat', json={"message":"Hello from A", "user_id":"user_a"})
        r2 = self.client.post('/api/chat', json={"message":"Hello from B", "user_id":"user_b"})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        # To truly assert separation, inspect the MongoDB backend or mock log_conversation

if __name__ == '__main__':
    unittest.main()
