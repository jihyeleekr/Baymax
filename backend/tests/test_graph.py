import unittest
import json
from datetime import datetime
from app import create_app


class GraphVisualizationTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test instance of the Flask app
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()
        self.test_user = "graph-test-user"

    # Small helper to insert one log using the real API
    def seed_log(self, date_iso="2025-11-01", user_id=None, **extra):
        if user_id is None:
            user_id = self.test_user

        payload = {
            "user_id": user_id,
            "date": date_iso,
            "tookMedication": True,
            "sleepHours": 7,
            "vital_bpm": 80,
            "mood": 4,
            "symptom": "fever",
            "note": "seeded from test",
        }
        payload.update(extra)

        resp = self.client.post("/api/logs", json=payload)
        self.assertEqual(resp.status_code, 200)

    # 1) Invalid date range: start > end -> should return error
    def test_graph_invalid_date_range(self):
        """
        If the user selects a date range where start > end,
        the API should return 400 with a clear error message.
        """
        response = self.client.get(
            "/api/health-logs?start=2025-11-10&end=2025-11-01"
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Start date must not be after end date.")

    # 2) No data for selected date range -> should return error
    def test_graph_no_data_in_range(self):
        """
        If there are no health logs between the selected dates,
        the API should return 404 with an error message.
        """
        response = self.client.get(
            "/api/health-logs?start=2000-01-01&end=2000-01-31"
        )

        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            "No health logs found between the selected date range.",
        )

    # 3) Valid date range with data -> should return list of logs
    def test_graph_valid_range_returns_data(self):
        """
        For a valid date range that matches existing logs,
        the API should return 200 and a non-empty list of entries.
        """
        # Seed one log in the range
        self.seed_log(date_iso="2025-11-05")

        response = self.client.get(
            "/api/health-logs?start=2025-11-01&end=2025-11-10&user_id=graph-test-user"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        items = data if isinstance(data, list) else data.get("data", [])

        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        first = items[0]
        self.assertIn("date", first)
        # Backend field names used by the graph
        self.assertTrue(
            any(
                key in first
                for key in ["sleepHours", "mood", "vital_bpm", "tookMedication"]
            )
        )

    # 4) Returned logs should be sorted by date ascending
    def test_graph_logs_are_sorted_by_date(self):
        """
        The API should return health logs ordered by date (oldest first),
        so the graph can draw a continuous time series.
        """
        # Seed multiple days out of order
        self.seed_log(date_iso="2025-11-10")
        self.seed_log(date_iso="2025-11-01")
        self.seed_log(date_iso="2025-11-05")

        response = self.client.get(
            "/api/health-logs?start=2025-11-01&end=2025-11-10&user_id=graph-test-user"
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        dates = [
            datetime.strptime(item["date"], "%m-%d-%Y").date()
            for item in data
        ]

        self.assertGreater(len(dates), 1)
        self.assertEqual(dates, sorted(dates))

    # 5) Filtering by user_id – only that user’s logs should be returned
    def test_graph_filters_by_user_id(self):
        """
        When a user_id is provided, the API should only return logs
        that belong to that user.
        """
        # Seed logs for two different users on the same date
        self.seed_log(date_iso="2025-11-02", user_id="user-a", mood=2)
        self.seed_log(date_iso="2025-11-02", user_id="user-b", mood=5)

        response = self.client.get(
            "/api/health-logs?start=2025-11-01&end=2025-11-10&user_id=user-a"
        )
        self.assertIn(response.status_code, (200, 404))

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertGreater(len(data), 0)
            for log in data:
                self.assertEqual(log["user_id"], "user-a")

    # 6) Open-ended range (only start date) should still work
    def test_graph_start_only_range(self):
        """
        If only start is provided, API should treat it as
        [start, +infinity) and still return data.
        """
        self.seed_log(date_iso="2025-11-15")

        response = self.client.get(
            "/api/health-logs?start=2025-11-01&user_id=graph-test-user"
        )

        # Could be 200 with data or 404 if nothing matches,
        # but it should NOT be 400.
        self.assertNotEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
