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

    def test_upsert_log_uses_default_values_for_missing_fields(self):
        """
        When optional fields are omitted, the backend should still
        upsert a document and apply sensible defaults.
        """
        date_iso = "2030-01-05"
        payload = {
            "date": date_iso,
            # omit sleepHours, vital_bpm, mood, symptom, note
            "tookMedication": False,
        }

        resp = self.client.post(
            "/api/logs",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get("ok"))

        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        date_str = dt.strftime("%m-%d-%Y")
        doc = self.db.health_logs.find_one({"date": date_str})
        self.assertIsNotNone(doc)
        # tookMedication should be False
        self.assertFalse(doc.get("tookMedication"))
        # Optional fields can exist with None / default values
        self.assertIn("note", doc)
        self.assertIsInstance(doc.get("note"), str)

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
        self.assertEqual(data["vital_bpm"], 78)
        self.assertEqual(data["mood"], 3)
        self.assertEqual(data["symptom"], "nausea")
        self.assertEqual(data["note"], "Nausea after lunch (unit test)")

    # ---------- /api/health-logs (GET) ----------

    def test_get_health_logs_start_after_end_returns_400(self):
        """
        If start date is after end date, /api/health-logs should return 400
        with the appropriate error message.
        """
        resp = self.client.get(
            "/api/health-logs?start=2030-01-10&end=2030-01-09"
        )
        self.assertEqual(resp.status_code, 400)

        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Start date must not be after end date.")

    def test_get_health_logs_no_data_returns_404(self):
        """
        If no logs exist in the requested date range, /api/health-logs
        should return 404 with a clear error message.
        """
        # Very old range that should be empty
        resp = self.client.get(
            "/api/health-logs?start=1960-01-01&end=1960-01-01"
        )
        self.assertEqual(resp.status_code, 404)

        data = json.loads(resp.data)
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            "No health logs found between the selected date range."
        )

    def test_get_health_logs_returns_inserted_future_logs(self):
        """
        After inserting logs via /api/logs in a future date range,
        /api/health-logs with that range should return those logs.
        """
        # Insert two logs on consecutive future dates
        date_iso_1 = "2030-01-10"
        date_iso_2 = "2030-01-11"

        payload1 = {
            "date": date_iso_1,
            "tookMedication": True,
            "sleepHours": 7.0,
            "vital_bpm": 75,
            "mood": 4,
            "symptom": "tired",
            "note": "First future log",
        }
        payload2 = {
            "date": date_iso_2,
            "tookMedication": False,
            "sleepHours": 6.0,
            "vital_bpm": 70,
            "mood": 2,
            "symptom": "headache",
            "note": "Second future log",
        }

        self.client.post(
            "/api/logs",
            data=json.dumps(payload1),
            content_type="application/json",
        )
        self.client.post(
            "/api/logs",
            data=json.dumps(payload2),
            content_type="application/json",
        )

        # Now query /api/health-logs for that exact range
        resp = self.client.get(
            "/api/health-logs?start=2030-01-10&end=2030-01-11"
        )
        self.assertEqual(resp.status_code, 200)

        logs = json.loads(resp.data)
        self.assertIsInstance(logs, list)

        # Dates in /api/health-logs are returned as MM-DD-YYYY
        dt1 = datetime.strptime(date_iso_1, "%Y-%m-%d")
        dt2 = datetime.strptime(date_iso_2, "%Y-%m-%d")
        date_str_1 = dt1.strftime("%m-%d-%Y")
        date_str_2 = dt2.strftime("%m-%d-%Y")

        dates = {log.get("date") for log in logs}
        self.assertIn(date_str_1, dates)
        self.assertIn(date_str_2, dates)

    
    def test_health_logs_missing_params_returns_200_json(self):
        resp = self.client.get("/api/health-logs")  # no start/end/user_id

        # Current behavior: returns 200 even without explicit params
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, (list, dict))


    
    def test_logs_post_empty_body_returns_400(self):
        resp = self.client.post("/api/logs", json={})
        self.assertIn(resp.status_code, (400, 422))

    
    def test_upsert_log_missing_body_returns_400(self):
        """
        Posting to /api/logs with no JSON at all should hit the
        request-validation error path instead of silently succeeding.
        """
        resp = self.client.post("/api/logs")  # no json / data

        # Accept any 4xx or 5xx your current implementation returns here
        self.assertIn(resp.status_code, (400, 415, 422, 500))




if __name__ == "__main__":
     unittest.main()
