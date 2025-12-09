import io
import unittest
from app import create_app


class UploadPrescriptionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_upload_missing_file_returns_400(self):
        # No 'file' field at all
        resp = self.client.post(
            "/api/prescription/upload",
            data={"user_id": "no-file-user"},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertIn("error", body)

    def test_upload_pdf_success_or_graceful_error(self):
        # Tiny fake PDF
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
        data = {
            "file": (fake_pdf, "test.pdf"),
            "user_id": "pdf-user",
        }
        resp = self.client.post(
            "/api/prescription/upload",
            data=data,
            content_type="multipart/form-data",
        )
        # Should not 500; accept 200 or 400 depending on OCR/parse behavior
        self.assertIn(resp.status_code, (200, 400))
        body = resp.get_json()
        self.assertIsInstance(body, dict)

    def test_upload_image_success_or_graceful_error(self):
        # Tiny fake PNG
        fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\nfakepng")
        data = {
            "file": (fake_png, "test.png"),
            "user_id": "img-user",
        }
        resp = self.client.post(
            "/api/prescription/upload",
            data=data,
            content_type="multipart/form-data",
        )
        self.assertIn(resp.status_code, (200, 400))
        body = resp.get_json()
        self.assertIsInstance(body, dict)

    def test_upload_unsupported_extension(self):
        # Backend should reject unsupported types if you check extension/MIME
        fake_txt = io.BytesIO(b"not a prescription")
        data = {
            "file": (fake_txt, "notes.txt"),
            "user_id": "txt-user",
        }
        resp = self.client.post(
            "/api/prescription/upload",
            data=data,
            content_type="multipart/form-data",
        )
        # Expect a validation error, not 500
        self.assertIn(resp.status_code, (400, 415))
        body = resp.get_json()
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
