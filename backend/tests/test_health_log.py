import os
import unittest
import json
from datetime import datetime
from pymongo import MongoClient

from app import create_app


class HealthLogsApiTestCase(unittest.TestCase):
    def setUp(self):
        """
        Create a Flask test client and connect to MongoDB.
        We DO NOT wipe the existing data so that user data remains intact.
        """
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is not set for tests")

        self.mongo_client = MongoClient(uri)
        self.db = self.mongo_client["baymax"]

    # ---------- /api/logs (POST) ----------

    def test_upsert_log_missing_date(self):
        """
        If `date` is missing in the payload, the API should return
        400 with error 'date is required'.
        """
        payload = {
            "tookMedication": True,
            "sleepHours": 7.5,
        }
        resp = self.client.post(
            "/api/logs",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "date is required")

    def test_upsert_log_invalid_date_format(self):
        """
        If `date` is not in YYYY-MM-DD format, the API should return
        400 with error 'Invalid date format'.
        """
        payload = {
            "date": "2025/12/02",  # invalid format
            "tookMedication": True,
        }
        resp = self.client.post(
            "/api/logs",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid date format")

    def test_upsert_log_creates_or_updates_document(self):
        """
        For a valid payload, the API should return 200 and upsert
        a document into the `health_logs` collection for that date.
        """
        date_iso = "2030-01-02"  # pick a date unlikely to be used by real users
        payload = {
            "date": date_iso,
            "tookMedication": True,
            "sleepHours": 7.2,
            "vital_bpm": 80,
            "mood": 4,
            "symptom": "headache",
            "note": "Test note from unit test",
        }

        # First save
        resp1 = self.client.post(
            "/api/logs",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = json.loads(resp1.data)
        self.assertTrue(data1.get("ok"))

        # Check the document in MongoDB (date stored as MM-DD-YYYY)
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        date_str = dt.strftime("%m-%d-%Y")
        doc = self.db.health_logs.find_one({"date": date_str})
        self.assertIsNotNone(doc)
        self.assertTrue(doc.get("tookMedication"))
        self.assertEqual(doc.get("sleepHours"), 7.2)
        self.assertEqual(doc.get("vital_bpm"), 80)
        self.assertEqual(doc.get("mood"), 4)
        self.assertEqual(doc.get("symptom"), "headache")
        self.assertEqual(doc.get("note"), "Test note from unit test")

        # Second save to test "update" behavior
        payload_update = {
            **payload,
            "sleepHours": 5.0,
        }
        resp2 = self.client.post(
            "/api/logs",
            data=json.dumps(payload_update),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)

        doc2 = self.db.health_logs.find_one({"date": date_str})
        self.assertIsNotNone(doc2)
        self.assertEqual(doc2.get("sleepHours"), 5.0)  # updated value

    # ---------- /api/logs/one (GET) ----------

    def test_get_single_log_missing_date_param(self):
        """
        If the `date` query parameter is missing, the API should return
        400 with error 'date query param is required'.
        """
        resp = self.client.get("/api/logs/one")
        self.assertEqual(resp.status_code, 400)

        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "date query param is required")

    def test_get_single_log_invalid_date_format(self):
        """
        If the `date` query parameter is not in YYYY-MM-DD format,
        the API should return 400 with error 'Invalid date format'.
        """
        resp = self.client.get("/api/logs/one?date=12/02/2030")
        self.assertEqual(resp.status_code, 400)

        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid date format")

    def test_get_single_log_not_found_returns_empty_object(self):
        """
        If there is no log for the specified date, the API should
        return 200 and an empty JSON object {}.
        """
        # Pick a very old date that should not exist in real data
        resp = self.client.get("/api/logs/one?date=1970-01-01")
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data)
        self.assertIsInstance(data, dict)
        self.assertEqual(len(data), 0)

    def test_get_single_log_returns_existing_log(self):
        """
        After inserting a log via /api/logs, a GET /api/logs/one
        with the same date should return the stored values with
        the correct field mapping.
        """
        date_iso = "2030-01-03"
        payload = {
            "date": date_iso,
            "tookMedication": True,
            "sleepHours": 6.5,
            "vital_bpm": 78,
            "mood": 3,
            "symptom": "nausea",
            "note": "Nausea after lunch (unit test)",
        }

        # Upsert first
        resp_post = self.client.post(
            "/api/logs",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp_post.status_code, 200)

        # Then fetch
        resp_get = self.client.get(f"/api/logs/one?date={date_iso}")
        self.assertEqual(resp_get.status_code, 200)

        data = json.loads(resp_get.data)
        self.assertEqual(data["date"], date_iso)
        self.assertTrue(data["tookMedication"])
        self.assertEqual(data["sleepHours"], 6.5)
        # Note: current backend uses key 'vital_pbm' (typo).
        # If you fix the typo in the backend, change this assertion to 'vital_bpm'.
        self.assertEqual(data["vital_bpm"], 78)
        self.assertEqual(data["mood"], 3)
        self.assertEqual(data["symptom"], "nausea")
        self.assertEqual(data["note"], "Nausea after lunch (unit test)")


if __name__ == "__main__":
    unittest.main()
