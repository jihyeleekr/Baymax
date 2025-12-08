import unittest
import json
from datetime import datetime
from app import create_app


class OnboardingTestCase(unittest.TestCase):
    """
    Tests for user onboarding functionality.
    Covers user profile creation, preferences setup, and initial data validation.
    """

    def setUp(self):
        """Create Flask test client"""
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_create_user_profile_missing_required_fields(self):
        """
        Test that profile creation fails when required fields are missing.
        """
        payload = {
            "user_id": "test_user_456",
            "email": "incomplete@example.com"
            # Missing: full_name, date_of_birth, etc.
        }

        response = self.client.post(
            "/api/onboarding/profile",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("required", data["error"].lower())

    def test_set_health_preferences_success(self):
        """
        Test successful setting of health preferences during onboarding.
        """
        payload = {
            "user_id": "test_user_123",
            "preferences": {
                "medication_reminders": True,
                "reminder_times": ["08:00", "20:00"],
                "health_goals": ["weight_loss", "better_sleep"],
                "notification_enabled": True,
                "data_sharing": False,
                "units": "metric"
            }
        }

        response = self.client.post(
            "/api/onboarding/preferences",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Preferences saved successfully")

    def test_get_onboarding_status_not_started(self):
        """
        Test retrieving onboarding status for a user who hasn't started.
        """
        response = self.client.get("/api/onboarding/status?user_id=new_user_999")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data.get("onboarding_completed"))
        self.assertEqual(data.get("status"), "not_started")

    def test_accept_terms_and_privacy(self):
        """
        Test accepting terms of service and privacy policy.
        """
        payload = {
            "user_id": "test_user_terms",
            "terms_accepted": True,
            "privacy_accepted": True,
            "accepted_at": datetime.now().isoformat(),
            "ip_address": "127.0.0.1"
        }

        response = self.client.post(
            "/api/onboarding/accept-terms",
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertTrue(data.get("terms_accepted"))


if __name__ == "__main__":
    unittest.main()