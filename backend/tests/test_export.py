import unittest
import json
from app import create_app

class ExportSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

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
        self.assertGreater(len(response.data), 100)  # PDF should not be empty

    def test_preview_no_category_selected(self):
        payload = {
            "categories": [],
            "start_date": "2025-11-01",
            "end_date": "2025-11-10"
        }
        response = self.client.post("/api/export/preview", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["total_records"], 0)

    def test_export_json_medications_last_90_days(self):
        payload = {
            "categories": ["medications"],
            "start_date": "2025-08-20",
            "end_date": "2025-11-18",
            "format": "json"
        }
        response = self.client.post("/api/export", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"application/json", response.content_type.encode())
        json_data = json.loads(response.data)
        self.assertIn("data", json_data)
        for record in json_data["data"]:
            self.assertIn("took_medication", record)

if __name__ == "__main__":
    unittest.main()
