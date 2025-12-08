import unittest
import json
from app import create_app

class GraphVisualizationTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test instance of the Flask app
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

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
        # Adjust this string to match your actual backend message
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
        # Adjust this string to match your actual backend message
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
        # Use a range that you know exists in your seed / DB data
        response = self.client.get(
            "/api/health-logs?start=2025-11-01&end=2025-11-10"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        items = data if isinstance(data, list) else data.get("data", [])

        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Check that each item has at least a date field
        first = items[0]
        self.assertIn("date", first)
        # Optionally check some metric fields used by the graph
        # (sleep / mood / vital, etc.)
        self.assertTrue(
            any(
                key in first
                for key in ["hours_of_sleep", "mood", "vital_bpm", "took_medication"]
            )
        )

if __name__ == "__main__":
    unittest.main()