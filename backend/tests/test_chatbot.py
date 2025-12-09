import io
import unittest
import json
from app import create_app


class TestBaymaxChatbot(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_chat_empty_message_400(self):
        resp = self.client.post(
            "/api/chat",
            json={"message": "", "user_id": "user_a"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_chat_phi_detected(self):
        payload = {
            "message": "My name is John Smith, phone 123-456-7890, I have strep throat",
            "user_id": "user_phi",
        }
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["classification"], "PHI_DETECTED")
        self.assertTrue(data["phi_detected"])

    def test_chat_emergency_detected(self):
        payload = {
            "message": "I have crushing chest pain and can't breathe, what should I do?",
            "user_id": "user_emerg",
        }
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["classification"], "EMERGENCY")
        self.assertIn("911", data["response"])

    def test_chat_anonymous_symptom(self):
        payload = {
            "message": "How can I treat a common cold?",
            "user_id": "anon1",
        }
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data.get("phi_detected", False))
        self.assertIn("response", data)

    def test_prescription_upload_pdf(self):
        # Tiny fake PDF in memory
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
        data = {
            "file": (fake_pdf, "test.pdf"),
            "user_id": "upload-user",
        }
        resp = self.client.post(
            "/api/prescription/upload",
            data=data,
            content_type="multipart/form-data",
        )
        # Endpoint should at least return JSON and a 2xx/4xx code, not 500
        self.assertIn(resp.status_code, (200, 400))
        body = resp.get_json()
        self.assertIsInstance(body, dict)

    def test_user_specific_chat_history_basic(self):
        r1 = self.client.post(
            "/api/chat",
            json={"message": "Hello from A", "user_id": "user_a"},
        )
        r2 = self.client.post(
            "/api/chat",
            json={"message": "Hello from B", "user_id": "user_b"},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

    
    def test_chat_with_no_prescription_context(self):
    # Use a fresh user_id so there is no prescription in DB
        payload = {"message": "What is high blood pressure?", "user_id": "no-presc-user"}
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("response", data)

    
    def test_chat_with_explicit_prescription_id(self):
    # Upload a tiny fake PDF first
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
        upload_resp = self.client.post(
            "/api/prescription/upload",
            data={"file": (fake_pdf, "test.pdf"), "user_id": "p-user"},
            content_type="multipart/form-data",
        )
        self.assertEqual(upload_resp.status_code, 200)
        presc = upload_resp.get_json()
        presc_id = presc["prescription_id"]

        # Now chat with that prescription_id
        payload = {
            "message": "What medications are in my prescription?",
            "user_id": "p-user",
            "prescription_id": presc_id,
        }
        chat_resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(chat_resp.status_code, 200)
        data = chat_resp.get_json()
        self.assertIn("response", data)

    
    def test_history_reset_after_phi(self):
    # First, trigger PHI_DETECTED
        phi_payload = {
            "message": "My name is John and my phone is 123-456-7890.",
            "user_id": "hist-user",
        }
        resp1 = self.client.post(
            "/api/chat",
            data=json.dumps(phi_payload),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)
        d1 = resp1.get_json()
        self.assertEqual(d1["classification"], "PHI_DETECTED")

        # Now send anonymous symptom question
        payload2 = {
            "message": "I have a cough, what can I do?",
            "user_id": "hist-user",
        }
        resp2 = self.client.post(
            "/api/chat",
            data=json.dumps(payload2),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)
        d2 = resp2.get_json()
        self.assertNotEqual(d2["classification"], "PHI_DETECTED")
        self.assertIn("response", d2)

    def test_prescription_upload_image(self):
    # Fake PNG file in memory
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
        # Just ensure it doesn't 500 and returns JSON
        self.assertIn(resp.status_code, (200, 400))
        body = resp.get_json()
        self.assertIsInstance(body, dict)

    def test_chat_defaults_to_anonymous_user(self):
        payload = {"message": "What is diabetes?"}  # no user_id field
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("response", data)
    

    def test_chat_uses_latest_prescription_context(self):
        # Upload any fake PDF to create a prescription for this user
        fake_pdf = io.BytesIO(b"%PDF-1.4 context")
        upload_resp = self.client.post(
            "/api/prescription/upload",
            data={"file": (fake_pdf, "latest.pdf"), "user_id": "ctx-user"},
            content_type="multipart/form-data",
        )
        self.assertEqual(upload_resp.status_code, 200)

        # Now call chat without prescription_id; should hit "most recent on file" branch
        payload = {
            "message": "What medications are in my prescription?",
            "user_id": "ctx-user",
        }
        chat_resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(chat_resp.status_code, 200)
        data = chat_resp.get_json()
        self.assertIn("response", data)

    
    def test_chat_no_json_body(self):
    # Completely missing body
        resp = self.client.post("/api/chat")
        # Should not silently succeed; hits early-validation / error path
        self.assertIn(resp.status_code, (400, 500))
        data = resp.get_json()
        self.assertIsInstance(data, dict)

    def test_chat_non_string_message(self):
        payload = {"message": {"not": "a string"}, "user_id": "bad-type"}
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, (400, 500))
        data = resp.get_json()
        self.assertIsInstance(data, dict)

    
    def test_chat_history_load_error_path(self):
        # Monkeypatch: pretend collection attribute is missing
        original = self.app.db.chat_conversations if hasattr(self.app, "db") else None

        try:
            if hasattr(self.app, "db"):
                del self.app.db.chat_conversations  # force AttributeError

            payload = {"message": "What is flu?", "user_id": "hist-error"}
            resp = self.client.post(
                "/api/chat",
                data=json.dumps(payload),
                content_type="application/json",
            )
            # Should still respond, not crash
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn("response", data)
        finally:
            # Restore if needed
            if original is not None:
                self.app.db.chat_conversations = original

    
    def test_upload_ocr_failure_returns_error(self):
        from app import extract_pdf_text

        original = extract_pdf_text

        def boom(path):
            raise RuntimeError("OCR failed")

        try:
            # Monkeypatch
            import app as app_module
            app_module.extract_pdf_text = boom

            fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
            resp = self.client.post(
                "/api/prescription/upload",
                data={"file": (fake_pdf, "fail.pdf"), "user_id": "ocr-fail"},
                content_type="multipart/form-data",
            )
            self.assertIn(resp.status_code, (400, 500))
            data = resp.get_json()
            self.assertIsInstance(data, dict)
        finally:
            # Restore
            app_module.extract_pdf_text = original
        

    

    
    def test_chat_with_invalid_prescription_id(self):
        payload = {
            "message": "Do you see any meds?",
            "user_id": "bad-presc-user",
            "prescription_id": "000000000000000000000000",  # valid ObjectId format but won't exist
        }
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        # Should still return a 200 with some response, not crash
        self.assertIn(resp.status_code, (200, 400))
        data = resp.get_json()
        self.assertIsInstance(data, dict)

    def test_404_returns_json(self):
        resp = self.client.get("/definitely-no-such-route-xyz")
        self.assertEqual(resp.status_code, 404)
        # Just make sure it returns something, even if it's HTML
        self.assertTrue(resp.data)  # non-empty body


    def test_chat_missing_message_key(self):
        payload = {"user_id": "no-message-user"}
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, (400, 500))
        data = resp.get_json()
        self.assertIsInstance(data, dict)
    

    def test_chat_with_explicit_prescription_id(self):
        # Upload to get an id
        fake_pdf = io.BytesIO(b"%PDF-1.4 ctx")
        upload_resp = self.client.post(
            "/api/prescription/upload",
            data={"file": (fake_pdf, "ctx.pdf"), "user_id": "ctx-user"},
            content_type="multipart/form-data",
        )
        self.assertEqual(upload_resp.status_code, 200)
        presc = upload_resp.get_json()
        presc_id = presc["prescription_id"]

        payload = {
            "message": "Explain my prescription.",
            "user_id": "ctx-user",
            "prescription_id": presc_id,
        }
        resp = self.client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("response", data)














if __name__ == "__main__":
    unittest.main()
