import unittest
import json
from app import create_app

class ExportSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    # Test exporting all categories as CSV for the last 30 days
    def test_export_csv_all_categories_last_30_days(self):
        payload = {
            "categories": ["sleep", "symptoms", "mood", "medications", "vital_signs"],
            "start_date": "2025-10-19",
            "end_date": "2025-11-18",
            "format": "csv"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"text/csv", response.content_type.encode())
        self.assertIn(b"date", response.data)

    # Test previewing export data with invalid custom date range (start date after end date)
    def test_preview_invalid_custom_date_range(self):
        payload = {
            "categories": [],
            "start_date": "2025-11-10",
            "end_date": "2025-11-01"
        }
        response = self.client.post("/api/export/preview", json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Start date must not be after end date.")

    # Test previewing export data when no data exists between start and end date
    def test_preview_no_data_in_range(self):
        payload = {
            "categories": ["sleep", "mood"],
            "start_date": "2000-01-01",
            "end_date": "2000-01-31"
        }
        response = self.client.post("/api/export/preview", json=payload)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "No data found between the selected date range.")

    # Test exporting only mood and symptoms as PDF for a custom date range
    def test_export_pdf_mood_symptoms_custom_range(self):
        payload = {
            "categories": ["mood", "symptoms"],
            "start_date": "2025-11-01",
            "end_date": "2025-11-10",
            "format": "pdf"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"application/pdf", response.content_type.encode())


    # Test exporting with start date in the future
    def test_export_start_date_in_future(self):
        payload = {
            "categories": ["sleep", "mood"],
            "start_date": "2100-01-01",
            "end_date": "2100-01-10",
            "format": "csv"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Start date cannot be in the future.")

if __name__ == "__main__":
    unittest.main()
