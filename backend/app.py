from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pymongo import MongoClient
from services.gemini_service import GeminiService
import json
import csv
import io
import re
import hashlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

import PyPDF2
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
UPLOAD_FOLDER = 'uploads/prescriptions'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

load_dotenv()

# Initialize Gemini service
gemini_service = None
try:
    gemini_service = GeminiService()
    print("✅ Gemini API configured")
except ValueError as e:
    print(f"⚠️ Warning: {e}")

# 🔐 PHI PATTERNS (Protected Health Information)
PHI_PATTERNS = {
    'name': r'\b(?:my name is|i am|i\'m|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'phone': r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'dob': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
    'address': r'\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b'
}

class PHIAnonymizer:
    """Anonymize Protected Health Information"""
    
    @staticmethod
    def anonymize(text):
        """Replace PHI with tokens"""
        anonymized = text
        replacements = {}
        
        for category, pattern in PHI_PATTERNS.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for i, match in enumerate(matches):
                original = match.group(0)
                token = f"[{category.upper()}_{i}]"
                anonymized = anonymized.replace(original, token, 1)
                replacements[token] = category
        
        return anonymized, replacements
    
    @staticmethod
    def hash_identifier(text):
        """SHA256 hash for user ID"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

class ResponseFilter:
    """Filter and classify health queries"""
    
    CLASSIFICATIONS = {
        'SYMPTOM': ['pain', 'fever', 'headache', 'nausea', 'cough', 'dizzy', 'tired', 'sore', 'dehydration'],
        'MEDICATION': ['medicine', 'drug', 'prescription', 'pill', 'dosage', 'medication'],
        'TEST_RESULT': ['test', 'result', 'lab', 'blood work', 'scan', 'xray'],
        'VITAL_SIGNS': ['blood pressure', 'heart rate', 'temperature', 'pulse', 'oxygen'],
        'APPOINTMENT': ['appointment', 'schedule', 'doctor visit', 'consultation'],
        'EMERGENCY': ['emergency', 'urgent', 'severe pain', 'chest pain', 'cant breathe', 'difficulty breathing'],
        'GENERAL': []
    }
    
    @staticmethod
    def classify(text):
        """Classify query type"""
        text_lower = text.lower()
        
        for category, keywords in ResponseFilter.CLASSIFICATIONS.items():
            if category == 'GENERAL':
                continue
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'GENERAL'
    
    @staticmethod
    def is_emergency(text):
        """Detect emergency situations"""
        emergency_terms = ['emergency', 'cant breathe', "can't breathe", 'chest pain', 
                          'severe bleeding', 'unconscious', 'overdose', 'suicide']
        return any(term in text.lower() for term in emergency_terms)

def create_app():
    app = Flask(__name__)
    CORS(app)


    # MongoDB connection
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["baymax"]

    try:
        client.admin.command("ping")
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

    # Create TTL index for auto-delete after 90 days (HIPAA compliance)
    try:
        db.chat_conversations.create_index("timestamp", expireAfterSeconds=7776000)
        print("✅ TTL index created for chat conversations")
    except Exception as e:
        print(f"⚠️ TTL index warning: {e}")

    # ----------------- Health check -----------------
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "database": "connected"})

    # ----------------- Chat (Gemini) with ANONYMIZATION AND PRESCRIPTION CONTEXT -----------------
    @app.route("/api/chat", methods=["POST"])
    def chat():
        """Chat endpoint with PHI anonymization, filtering, prescription context, and conversation history."""
        if gemini_service is None:
            return jsonify({"error": "Gemini API not configured"}), 500

        try:
            data = request.json
            user_message = data.get("message", "")
            user_id = data.get("user_id", "anonymous")
            prescription_id = data.get("prescription_id")

            if not user_message:
                return jsonify({"error": "No message provided"}), 400

            # 1️⃣ ANONYMIZE USER INPUT
            anon_message, phi_map = PHIAnonymizer.anonymize(user_message)
            user_hash = PHIAnonymizer.hash_identifier(user_id)

            # 2️⃣ CHECK FOR EMERGENCY
            if ResponseFilter.is_emergency(user_message):
                emergency_response = {
                    "response": "🚨 EMERGENCY DETECTED\n\nPlease call 911 immediately or go to the nearest emergency room.",
                    "classification": "EMERGENCY",
                    "anonymized": True,
                    "phi_detected": len(phi_map) > 0,
                    "timestamp": datetime.now().isoformat()
                }

                log_conversation(
                    db,
                    user_hash,
                    anon_message,
                    emergency_response["response"],
                    "EMERGENCY",
                    phi_map,
                    True
                )

                return jsonify(emergency_response), 200

            # 3️⃣ IF PHI DETECTED, REFUSE TO ANSWER
            if len(phi_map) > 0:
                phi_response = (
                    "⚠️ I've detected personal health information in your message. "
                    "For your privacy and safety, I cannot provide personalized medical advice. "
                    "Please consult a healthcare provider directly for questions about your specific situation."
                )

                log_conversation(
                    db,
                    user_hash,
                    anon_message,
                    phi_response,
                    "PHI_DETECTED",
                    phi_map,
                    True
                )

                return jsonify({
                    "response": phi_response,
                    "classification": "PHI_DETECTED",
                    "anonymized": True,
                    "phi_detected": True,
                    "timestamp": datetime.now().isoformat()
                }), 200

            # 4️⃣ NO PHI → ANSWER NORMALLY
            classification = ResponseFilter.classify(anon_message)

            # 5️⃣ LOAD CONVERSATION HISTORY (last 30 messages)
            history_text = ""
            try:
                history_cursor = db.chat_conversations.find(
                    {"user_id_hash": user_hash}
                ).sort("timestamp", -1).limit(30)

                history = list(history_cursor)[::-1]  # oldest → newest

                if history:
                    history_lines = []
                    for h in history:
                        history_lines.append(f"User: {h.get('user_message', '')}")
                        history_lines.append(f"Baymax: {h.get('bot_response', '')}")

                    history_text = "\n".join(history_lines[-60:])  # cap at 60 lines
            except Exception as e:
                print(f"Error loading conversation history: {e}")
                history_text = ""


            try:
                last_conv = db.chat_conversations.find_one(
                    {"user_id_hash": user_hash},
                    sort=[("timestamp", -1)]
                )
                if last_conv and last_conv.get("classification") == "PHI_DETECTED":
                    history_text = ""
            except Exception as e:
                print(f"Error checking last conversation: {e}")


            # 6️⃣ LOAD PRESCRIPTION CONTEXT
            prescription_context = ""

            # Try explicit prescription_id first
            if prescription_id:
                from bson.objectid import ObjectId
                try:
                    prescription = db.prescriptions.find_one({"_id": ObjectId(prescription_id)})
                    if prescription:
                        meds = prescription.get("medications", [])
                        med_list = "\n".join([f"- {m['name']} {m['dosage']}" for m in meds])

                        warnings = prescription.get("warnings", [])
                        warning_list = "\n".join([f"- {w}" for w in warnings])

                        allergies = prescription.get("allergies", [])
                        allergy_list = "\n".join([f"- {a}" for a in allergies])

                        excerpt = (prescription.get("extracted_text", "") or "")[:500]

                        prescription_context = f"""
    PRESCRIPTION CONTEXT:
    The user has uploaded a prescription with:

    Medications:
    {med_list or '- None detected'}

    Warnings:
    {warning_list or '- None detected'}

    Allergies:
    {allergy_list or '- None listed'}

    Prescription excerpt:
    {excerpt}
    """
                except Exception as e:
                    print(f"Error loading prescription by ID: {e}")

            # Fallback: most recent prescription for this user
            if not prescription_context:
                try:
                    latest_prescription = db.prescriptions.find_one(
                        {"user_id_hash": user_hash},
                        sort=[("uploaded_at", -1)]
                    )

                    if latest_prescription:
                        meds = latest_prescription.get("medications", [])
                        med_list = "\n".join([f"- {m['name']} {m['dosage']}" for m in meds])

                        warnings = latest_prescription.get("warnings", [])
                        warning_list = "\n".join([f"- {w}" for w in warnings])

                        allergies = latest_prescription.get("allergies", [])
                        allergy_list = "\n".join([f"- {a}" for a in allergies])

                        excerpt = (latest_prescription.get("extracted_text", "") or "")[:500]

                        prescription_context = f"""
    PRESCRIPTION CONTEXT (most recent on file):
    The user has a prescription with:

    Medications:
    {med_list or '- None detected'}

    Warnings:
    {warning_list or '- None detected'}

    Allergies:
    {allergy_list or '- None listed'}

    Prescription excerpt:
    {excerpt}
    """
                    else:
                        prescription_context = ""
                except Exception as e:
                    print(f"Error loading latest prescription: {e}")
                    prescription_context = ""

            # 7️⃣ GENERATE RESPONSE WITH FULL CONTEXT
            context_prompt = f"""You are Baymax, a health information assistant.

    Rules:
    1. Provide general, educational health information.
    2. You may mention common over‑the‑counter options and self‑care steps that are usually safe for most adults, but do NOT customize doses or make decisions for the user.
    3. Do NOT diagnose specific conditions or tell the user exactly what they personally should do.
    4. Always suggest talking to a healthcare provider for diagnosis or treatment decisions.

    {f"CONVERSATION HISTORY (last 30 exchanges):\n{history_text}\n" if history_text else ""}

    {prescription_context}

    Query Type: {classification}
    User Question: "{anon_message}"

    Answer in 2–3 sentences with practical, general information:
    """

            bot_response = gemini_service.chat(context_prompt)
            final_response = bot_response

            # 8️⃣ LOG AND RETURN
            log_conversation(db, user_hash, anon_message, final_response, classification, phi_map, False)

            return jsonify({
                "response": final_response,
                "classification": classification,
                "anonymized": True,
                "phi_detected": False,
                "timestamp": datetime.now().isoformat()
            }), 200

        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
            return jsonify({"error": str(e)}), 500



        # ----------------- Health logs API (from MongoDB) -----------------
    @app.route("/api/health-logs", methods=["GET"])
    def get_health_logs():
            """
            Returns health logs from the `health_logs` collection.

            Optional query parameters:
            - start: start date (YYYY-MM-DD)
            - end:   end date   (YYYY-MM-DD)
            - user_id: Supabase user ID; defaults to "anonymous" for tests / logged-out
            """
            try:
                # Default user_id for tests / anonymous usage
                user_id = request.args.get("user_id") or "anonymous"

                start_str = request.args.get("start")
                end_str = request.args.get("end")

                # Fetch only this user's logs
                logs = list(db.health_logs.find({"user_id": user_id}))

                def parse_mmddyyyy(s: str):
                    return datetime.strptime(s, "%m-%d-%Y").date()

                start_date = (
                    datetime.strptime(start_str, "%Y-%m-%d").date()
                    if start_str
                    else None
                )
                end_date = (
                    datetime.strptime(end_str, "%Y-%m-%d").date()
                    if end_str
                    else None
                )

                if start_date and end_date and start_date > end_date:
                    return jsonify({"error": "Start date must not be after end date."}), 400

                filtered_logs = []

                for log in logs:
                    log["_id"] = str(log["_id"])

                    date_str = log.get("date")
                    if not date_str:
                        continue

                    try:
                        log_date = parse_mmddyyyy(date_str)
                    except ValueError:
                        continue

                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue

                    filtered_logs.append(log)

                # Sort by date ascending
                filtered_logs.sort(
                    key=lambda x: datetime.strptime(x["date"], "%m-%d-%Y")
                )

                if not filtered_logs:
                    # This is what your graph tests expect in the "no data" case
                    return jsonify({"error": "No health logs found between the selected date range."}), 404

                # Normal success path
                return jsonify(filtered_logs), 200

            except Exception as e:
                print("❌ get_health_logs error:", e)
                return jsonify({"error": str(e)}), 500



    # ----------------- Export data (CSV, PDF, JSON) -----------------
    @app.route("/api/export", methods=["POST"])
    def export_data():
        """Export health data in specified format (CSV, PDF, JSON)"""
        try:
            data = request.json

            user_id = data.get("user_id") or "anonymous"

            categories = data.get("categories", [])
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            export_format = data.get("format", "csv")

            if not user_id:  # ✅ ADD
                return jsonify({"error": "user_id is required"}), 400

            logs = list(db.health_logs.find({"user_id": user_id}))

            # Fetch from MongoDB instead of seed file
            #logs = list(db.health_logs.find())
            
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                now = datetime.now()
                if start > now:
                    return jsonify({"error": "Start date cannot be in the future."}), 400

            # Apply date filtering (MongoDB dates are MM-DD-YYYY)
            if start_date or end_date:
                filtered_logs = []
                for log in logs:
                    try:
                        # Parse MM-DD-YYYY format from MongoDB
                        log_date = datetime.strptime(log["date"], "%m-%d-%Y")

                        if start_date:
                            start = datetime.strptime(start_date, "%Y-%m-%d")
                            if log_date < start:
                                continue

                        if end_date:
                            end = datetime.strptime(end_date, "%Y-%m-%d")
                            if log_date > end:
                                continue

                        filtered_logs.append(log)
                    except (ValueError, KeyError):
                        continue
                logs = filtered_logs

            # Filter by categories
            if categories:
                filtered_logs = []
                for log in logs:
                    filtered_log = {"date": log["date"]}

                    if "sleep" in categories and log.get("sleepHours") is not None:
                        filtered_log["sleepHours"] = log["sleepHours"]

                    if "symptoms" in categories and log.get("symptom"):
                        filtered_log["symptom"] = log["symptom"]

                    if "mood" in categories and log.get("mood") is not None:
                        filtered_log["mood"] = log["mood"]

                    if "medications" in categories and log.get("tookMedication") is not None:
                        filtered_log["tookMedication"] = log["tookMedication"]

                    if "vital_signs" in categories and log.get("vital_bpm") is not None:
                        filtered_log["vital_bpm"] = log["vital_bpm"]
                    
                    # Include note if it exists
                    if log.get("note"):
                        filtered_log["note"] = log["note"]

                    filtered_logs.append(filtered_log)
                logs = filtered_logs

            # Convert ObjectId to string for JSON serialization
            health_logs = []
            for log in logs:
                log_copy = log.copy()
                if "_id" in log_copy:
                    log_copy["_id"] = str(log_copy["_id"])
                # Remove MongoDB-specific fields
                log_copy.pop("created_at", None)
                log_copy.pop("updated_at", None)
                health_logs.append(log_copy)



            # ---- CSV export ----
            if export_format == "csv":
                if not health_logs:
                    return jsonify({"error": "No data found between the selected date range."}), 404
                
                output = io.StringIO()
                fieldnames = list(health_logs[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(health_logs)

                output.seek(0)
                file_output = io.BytesIO()
                file_output.write(output.getvalue().encode("utf-8"))
                file_output.seek(0)

                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mimetype="text/csv",
                )

            # PDF export
            elif export_format == "pdf":
                file_output = io.BytesIO()
                doc = SimpleDocTemplate(file_output, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                title_style = ParagraphStyle(
                    "CustomTitle",
                    parent=styles["Heading1"],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=1,
                )
                story.append(Paragraph("Baymax Health Data Export", title_style))

                info_style = styles["Normal"]
                story.append(
                    Paragraph(
                        f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                        info_style,
                    )
                )
                story.append(
                    Paragraph(f"<b>Date Range:</b> {start_date or 'All'} to {end_date or 'All'}", info_style)
                )
                story.append(
                    Paragraph(f"<b>Categories:</b> {', '.join(categories) if categories else 'All'}", info_style)
                )
                story.append(
                    Paragraph(f"<b>Total Records:</b> {len(health_logs)}", info_style)
                )
                story.append(Spacer(1, 20))

                if health_logs:
                    fieldnames = list(health_logs[0].keys())
                    headers = [name.replace("_", " ").title() for name in fieldnames]
                    table_data = [headers]

                    for log in health_logs:
                        row = []
                        for field in fieldnames:
                            value = log.get(field, "N/A")
                            if value is None:
                                value = "N/A"
                            elif isinstance(value, bool):
                                value = "Yes" if value else "No"
                            row.append(str(value))
                        table_data.append(row)

                    table = Table(table_data)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, 0), 10),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 1), (-1, -1), 8),
                                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ]
                        )
                    )

                    story.append(table)
                else:
                    story.append(
                        Paragraph(
                            "No data found for the selected criteria.",
                            styles["Normal"],
                        )
                    )

                doc.build(story)
                file_output.seek(0)

                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mimetype="application/pdf",
                )

            # JSON export
            elif export_format == "json":
                output = json.dumps(
                    {
                        "export_info": {
                            "generated_at": datetime.now().isoformat(),
                            "date_range": {
                                "start": start_date or "All",
                                "end": end_date or "All",
                            },
                            "categories": categories if categories else "All",
                            "total_records": len(health_logs),
                        },
                        "data": health_logs,
                    },
                    indent=2,
                )

                file_output = io.BytesIO()
                file_output.write(output.encode("utf-8"))
                file_output.seek(0)

                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f"health_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mimetype="application/json",
                )

            else:
                return jsonify({"error": "Unsupported export format"}), 400

        except Exception as e:
            print(f"❌ Export error: {str(e)}")
            return jsonify({"error": str(e)}), 500


     # ----------------- Prescription Upload -----------------


    @app.route("/api/prescription/upload", methods=["POST"])
    def upload_prescription():
        """Upload and process prescription file"""
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files['file']
            user_id = request.form.get('user_id', 'anonymous')
            
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if not allowed_file(file.filename):
                return jsonify({"error": "Invalid file type. Use PDF, PNG, or JPG"}), 400
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset
            
            if size > MAX_FILE_SIZE:
                return jsonify({"error": "File too large. Max 5MB"}), 400
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            user_hash = PHIAnonymizer.hash_identifier(user_id)
            unique_filename = f"{user_hash}_{timestamp}_{filename}"
            
            # Save file
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            # Extract text based on file type
            extracted_text = ""
           
            if filename.lower().endswith('.pdf'):
                extracted_text = extract_pdf_text(filepath)
            else:
                extracted_text = extract_image_text(filepath)

            # Parse prescription data
            prescription_data = parse_prescription(extracted_text)

            # Generate AI explanation
            explanation = generate_prescription_explanation(extracted_text)

            # Store in MongoDB
            doc = {
                'user_id_hash': user_hash,
                'filename': unique_filename,
                'filepath': filepath,
                'extracted_text': extracted_text,
                'medications': prescription_data['medications'],
                'warnings': prescription_data['warnings'],
                'allergies': prescription_data.get('allergies', []),  # ✅ Changed from parsed_data to prescription_data
                'diagnoses': prescription_data.get('diagnoses', []),  # ✅ Changed from parsed_data to prescription_data
                'ai_explanation': explanation,
                'uploaded_at': datetime.now()
            }

            result = db.prescriptions.insert_one(doc)
            doc['_id'] = str(result.inserted_id)

            return jsonify({
                'success': True,
                'prescription_id': str(result.inserted_id),
                'extracted_text': extracted_text,
                'medications': prescription_data['medications'],
                'warnings': prescription_data['warnings'],
                'allergies': prescription_data.get('allergies', []),  # ✅ Include in response
                'diagnoses': prescription_data.get('diagnoses', []),  # ✅ Include in response
                'explanation': explanation
            }), 200

        except Exception as e:
                print(f"❌ Upload error: {str(e)}")
                return jsonify({"error": str(e)}), 500

            #-------------------------------------------------------------------

    @app.route("/api/prescription/<prescription_id>", methods=["GET"])
    def get_prescription(prescription_id):
        """Retrieve prescription by ID"""
        try:
            from bson.objectid import ObjectId
            
            doc = db.prescriptions.find_one({'_id': ObjectId(prescription_id)})
            if not doc:
                return jsonify({"error": "Prescription not found"}), 404
            
            doc['_id'] = str(doc['_id'])
            return jsonify(doc), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ----------------- Single day log (for calendar form) -----------------
    @app.route("/api/logs/one", methods=["GET"])
    def get_single_log():
        """
        React:
        GET /api/logs/one?date=2025-12-02&user_id=xxx
        Returns a single health log for the specified date and user.
        """
        try:
            date_iso = request.args.get("date")
            user_id = request.args.get("user_id") or "anonymous"
            
            if not date_iso:
                return jsonify({"error": "date query param is required"}), 400
            
            if not user_id:  # ✅ ADD
                return jsonify({"error": "user_id is required"}), 400

            try:
                dt = datetime.strptime(date_iso[:10], "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format"}), 400

            date_str = dt.strftime("%m-%d-%Y")

            # ✅ FILTER by both date AND user_id
            doc = db.health_logs.find_one({"date": date_str, "user_id": user_id})
            
            if not doc:
                return jsonify({}), 200

            doc["_id"] = str(doc["_id"])

            resp = {
                "date": date_iso,
                "tookMedication": doc.get("tookMedication", False),
                "sleepHours": doc.get("sleepHours"),
                "vital_bpm": doc.get("vital_bpm"),
                "mood": doc.get("mood"),
                "symptom": doc.get("symptom"),
                "note": doc.get("note", ""),
            }
            return jsonify(resp), 200

        except Exception as e:
            print("❌ get_single_log error:", e)
            return jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------------
    @app.route("/api/logs", methods=["POST"])
    def upsert_log():
        """
        React:
        POST /api/logs
        {
            "user_id": "xxx",  // ✅ REQUIRED
            "date": "2025-12-02",
            "tookMedication": true,
            "sleepHours": 7,
            "vital_bpm": 80,
            "mood": 4,
            "symptom": "fever",
            "note": "..."
        }
        """
        try:
            data = request.json or {}
            date_iso = data.get("date")
            user_id = data.get("user_id") or "anonymous"
            # still keep the date validation as before
            if not date_iso:
                return jsonify({"error": "date is required"}), 400


            try:
                dt = datetime.strptime(date_iso[:10], "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format"}), 400

            date_str = dt.strftime("%m-%d-%Y")

            doc = {
                "user_id": user_id,  # ✅ ADD
                "date": date_str,
                "tookMedication": bool(data.get("tookMedication", False)),
                "sleepHours": data.get("sleepHours"),
                "vital_bpm": data.get("vital_bpm"),
                "mood": data.get("mood"),
                "symptom": data.get("symptom"),
                "note": data.get("note", ""),
                "updated_at": datetime.now(),
            }

            # ✅ FILTER update by BOTH date AND user_id
            db.health_logs.update_one(
                {"date": date_str, "user_id": user_id},
                {"$set": doc},
                upsert=True,
            )

            return jsonify({"ok": True}), 200

        except Exception as e:
            print("❌ upsert_log error:", e)
            return jsonify({"error": str(e)}), 500


    # ----------------- Export preview -----------------
    @app.route("/api/export/preview", methods=["POST"])
    def preview_export():
        """Preview export data without downloading"""
        try:
            data = request.json

            user_id = data.get("user_id") or "anonymous" # ✅ ADD

            categories = data.get("categories", [])
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            if not user_id:  # ✅ ADD
                return jsonify({"error": "user_id is required"}), 400

            logs = list(db.health_logs.find({"user_id": user_id}))

            # Fetch from MongoDB instead of seed file
            #logs = list(db.health_logs.find())

            # Validate custom date range
            if start_date and end_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                now = datetime.now()
                if start > now:
                    return jsonify({"error": "Start date cannot be in the future."}), 400
                if start > end:
                    return jsonify({"error": "Start date must not be after end date."}), 400

            if start_date or end_date:
                filtered_logs = []
                for log in logs:
                    try:
                        log_date = datetime.strptime(log["date"], "%m-%d-%Y")

                        if start_date:
                            start = datetime.strptime(start_date, "%Y-%m-%d")
                            if log_date < start:
                                continue

                        if end_date:
                            end = datetime.strptime(end_date, "%Y-%m-%d")
                            if log_date > end:
                                continue

                        filtered_logs.append(log)
                    except (ValueError, KeyError):
                        continue
                logs = filtered_logs

            if categories:
                filtered_logs = []
                for log in logs:
                    filtered_log = {"date": log["date"]}

                    if "sleep" in categories and log.get("sleepHours") is not None:
                        filtered_log["sleepHours"] = log["sleepHours"]

                    if "symptoms" in categories and log.get("symptom"):
                        filtered_log["symptom"] = log["symptom"]

                    if "mood" in categories and log.get("mood") is not None:
                        filtered_log["mood"] = log["mood"]

                    if "medications" in categories and log.get("tookMedication") is not None:
                        filtered_log["tookMedication"] = log["tookMedication"]

                    if "vital_signs" in categories and log.get("vital_bpm") is not None:
                        filtered_log["vital_bpm"] = log["vital_bpm"]
                    
                    if log.get("note"):
                        filtered_log["note"] = log["note"]

                    filtered_logs.append(filtered_log)
                logs = filtered_logs

            # Convert ObjectId to string and remove MongoDB-specific fields
            health_logs = []
            for log in logs:
                log_copy = log.copy()
                if "_id" in log_copy:
                    log_copy["_id"] = str(log_copy["_id"])
                log_copy.pop("created_at", None)
                log_copy.pop("updated_at", None)
                health_logs.append(log_copy)

            # If no data after filtering, return error
            if not health_logs:
                return jsonify({"error": "No data found between the selected date range."}), 404

            return jsonify(
                {
                    "preview": health_logs[:10],
                    "total_records": len(health_logs),
                    "categories_included": categories if categories else ["all"],
                    "date_range": {
                        "start": start_date or "All",
                        "end": end_date or "All",
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            print(f"❌ Preview error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    # ========== Onboarding Endpoints ==========
    
    @app.route("/api/onboarding/profile", methods=["POST"])
    def create_user_profile():
        """Create user profile during onboarding"""
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ["user_id", "email", "full_name", "date_of_birth"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"{field} is required"}), 400
            
            # Validate email format
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, data["email"]):
                return jsonify({"error": "Invalid email format"}), 400
            
            # Validate date of birth (not in future)
            dob = datetime.strptime(data["date_of_birth"], "%Y-%m-%d")
            if dob > datetime.now():
                return jsonify({"error": "Date of birth cannot be in the future"}), 400
            
            # Check for duplicate user_id
            existing = db.user_profiles.find_one({"user_id": data["user_id"]})
            if existing:
                return jsonify({"error": "User already exists"}), 409
            
            # Create profile
            profile_data = {
                "user_id": data["user_id"],
                "email": data["email"],
                "full_name": data["full_name"],
                "date_of_birth": data["date_of_birth"],
                "gender": data.get("gender"),
                "height_cm": data.get("height_cm"),
                "weight_kg": data.get("weight_kg"),
                "blood_type": data.get("blood_type"),
                "emergency_contact": data.get("emergency_contact"),
                "created_at": datetime.now()
            }
            
            db.user_profiles.insert_one(profile_data)
            
            return jsonify({
                "message": "Profile created successfully",
                "user_id": data["user_id"]
            }), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/onboarding/preferences", methods=["POST"])
    def set_health_preferences():
        """Set user health preferences"""
        try:
            data = request.json
            
            if "user_id" not in data:
                return jsonify({"error": "user_id is required"}), 400
            
            # Validate reminder times if provided
            if "preferences" in data and "reminder_times" in data["preferences"]:
                time_regex = r'^([01]\d|2[0-3]):([0-5]\d)$'
                for time_str in data["preferences"]["reminder_times"]:
                    if not re.match(time_regex, time_str):
                        return jsonify({"error": "Invalid time format"}), 400
            
            # Save preferences
            db.user_preferences.update_one(
                {"user_id": data["user_id"]},
                {"$set": {
                    "preferences": data.get("preferences", {}),
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            
            return jsonify({"message": "Preferences saved successfully"}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/onboarding/complete", methods=["POST"])
    def complete_onboarding():
        """Mark onboarding as complete"""
        try:
            data = request.json
            
            db.user_profiles.update_one(
                {"user_id": data["user_id"]},
                {"$set": {
                    "onboarding_completed": True,
                    "onboarding_completed_at": datetime.now()
                }}
            )
            
            return jsonify({
                "message": "Onboarding completed",
                "onboarding_completed": True
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/onboarding/status", methods=["GET"])
    def get_onboarding_status():
        """Get onboarding status for a user"""
        try:
            user_id = request.args.get("user_id")
            
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400
            
            profile = db.user_profiles.find_one({"user_id": user_id})
            preferences = db.user_preferences.find_one({"user_id": user_id})
            
            if not profile:
                return jsonify({
                    "onboarding_completed": False,
                    "status": "not_started"
                }), 200
            
            onboarding_complete = profile.get("onboarding_completed", False)
            
            return jsonify({
                "onboarding_completed": onboarding_complete,
                "status": "completed" if onboarding_complete else "in_progress",
                "profile_completed": True,
                "preferences_completed": preferences is not None
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/onboarding/medical-history", methods=["POST"])
    def add_medical_history():
        """Add medical history during onboarding"""
        try:
            data = request.json
            
            if data.get("skipped"):
                return jsonify({
                    "message": "Medical history skipped",
                    "skipped": True
                }), 200
            
            db.medical_history.update_one(
                {"user_id": data["user_id"]},
                {"$set": {
                    "medical_history": data.get("medical_history", {}),
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            
            return jsonify({"message": "Medical history saved successfully"}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/onboarding/accept-terms", methods=["POST"])
    def accept_terms():
        """Accept terms and privacy policy"""
        try:
            data = request.json
            
            if not data.get("terms_accepted"):
                return jsonify({"error": "Must accept terms of service"}), 400
            
            db.user_profiles.update_one(
                {"user_id": data["user_id"]},
                {"$set": {
                    "terms_accepted": True,
                    "privacy_accepted": data.get("privacy_accepted", False),
                    "terms_accepted_at": datetime.now(),
                    "acceptance_ip": data.get("ip_address")
                }}
            )
            
            return jsonify({
                "message": "Terms accepted",
                "terms_accepted": True
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

def log_conversation(db, user_hash, user_msg, bot_response, classification, phi_map, is_emergency):
    """Log anonymized conversation to MongoDB"""
    try:
        doc = {
            'user_id_hash': user_hash,
            'user_message': user_msg,  # Already anonymized
            'bot_response': bot_response,
            'classification': classification,
            'phi_detected': len(phi_map) > 0,
            'phi_categories': list(phi_map.values()),
            'is_emergency': is_emergency,
            'timestamp': datetime.now()
        }
        
        db.chat_conversations.insert_one(doc)
        print(f"✅ Logged conversation for user {user_hash[:8]}...")
        
    except Exception as e:
        print(f"❌ Failed to log: {str(e)}")



#helpers for the upload function

def extract_pdf_text(filepath):
    """Extract text from PDF"""
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return text


def extract_image_text(filepath):
    """Extract text from image using OCR"""
    try:
        image = Image.open(filepath)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def parse_prescription(text):
    """Parse medications, warnings, allergies, and diagnoses from text."""
    medications = []
    warnings = []
    allergies = []
    diagnoses = []

    # Regex for common medication formats, e.g. "Metformin 1000 mg"
    med_pattern = r'([A-Z][a-z]+(?:ide|cin|ol|pril|stat|form|mine|cillin))\s+(\d+\s*mg)'
    matches = re.findall(med_pattern, text, re.IGNORECASE)

    for name, dosage in matches:
        medications.append({
            'name': name,
            'dosage': dosage
        })

    # Extract warnings (simple heuristics)
    if 'BLACK BOX WARNING' in text.upper():
        warnings.append('BLACK BOX WARNING present')
    if 'contraindication' in text.lower():
        warnings.append('Contraindications noted')

    # 🔹 Allergies section (heuristic for your PDF format)
    # Looks for lines under an "ALLERGIES" heading
    allergy_section_match = re.search(r'ALLERGIES(.*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
    if allergy_section_match:
        allergy_block = allergy_section_match.group(1)
        # Split on newlines / bullets and keep non-empty lines
        for line in allergy_block.splitlines():
            line = line.strip(" \u2022-•\t")
            if line:
                allergies.append(line)

    # 🔹 Diagnoses section
    diag_section_match = re.search(r'DIAGNOSES(.*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
    if diag_section_match:
        diag_block = diag_section_match.group(1)
        for line in diag_block.splitlines():
            line = line.strip(" \u2022-•\t")
            if line:
                diagnoses.append(line)

    return {
        'medications': medications,
        'warnings': warnings,
        'allergies': allergies,
        'diagnoses': diagnoses
    }


def generate_prescription_explanation(text):
    """Generate patient-friendly explanation using Gemini"""
    if gemini_service is None:
        return "Unable to generate explanation - AI service unavailable"
    
    prompt = f"""You are a helpful health assistant. A patient has uploaded their prescription. 
Explain it in simple, patient-friendly language.

PRESCRIPTION TEXT:
{text[:1000]}

Provide a brief summary (3-4 sentences) covering:
1. What medications are prescribed and what they treat
2. Key warnings or side effects to watch for
3. Important instructions

DO NOT provide medical advice or suggest changes to treatment."""
    
    try:
        return gemini_service.chat(prompt)
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Unable to generate explanation"

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)