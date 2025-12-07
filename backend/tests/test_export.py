import unittest
import json
from app import create_app

class ExportSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

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

    # Test exporting with no categories selected returns all data
    def test_export_no_categories_selected(self):
        payload = {
            "categories": [],
            "start_date": "2025-11-01",
            "end_date": "2025-11-10",
            "format": "csv"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 200)  # Should succeed with all data
        self.assertIn(b"text/csv", response.content_type.encode())

    # Test exporting as JSON format with vital signs category
    def test_export_json_vital_signs(self):
        payload = {
            "categories": ["vital_signs"],
            "start_date": "2025-10-01",
            "end_date": "2025-11-30",
            "format": "json"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"application/json", response.content_type.encode())

if __name__ == "__main__":
    unittest.main()