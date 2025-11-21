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

    # ----------------- Chat (Gemini) with ANONYMIZATION -----------------
    @app.route("/api/chat", methods=["POST"])
    def chat():
        """Chat endpoint with PHI anonymization and filtering"""
        if gemini_service is None:
            return jsonify({"error": "Gemini API not configured"}), 500

        try:
            data = request.json
            user_message = data.get("message", "")
            user_id = data.get("user_id", "anonymous")

            if not user_message:
                return jsonify({"error": "No message provided"}), 400

            # 1️⃣ ANONYMIZE USER INPUT
            anon_message, phi_map = PHIAnonymizer.anonymize(user_message)
            user_hash = PHIAnonymizer.hash_identifier(user_id)

            # 2️⃣ CHECK FOR EMERGENCY
            if ResponseFilter.is_emergency(user_message):
                emergency_response = {
                    'response': '🚨 EMERGENCY DETECTED\n\nPlease call 911 immediately or go to the nearest emergency room. This is not a substitute for emergency medical care.',
                    'classification': 'EMERGENCY',
                    'anonymized': True,
                    'phi_detected': len(phi_map) > 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log emergency
                log_conversation(db, user_hash, anon_message, emergency_response['response'], 
                               'EMERGENCY', phi_map, True)
                
                return jsonify(emergency_response), 200

            # 3️⃣ CLASSIFY QUERY
            classification = ResponseFilter.classify(anon_message)

            # 4️⃣ GENERATE RESPONSE WITH SAFETY CONTEXT
            context_prompt = f"""You are Baymax, a health information assistant. Follow these rules:

1. NEVER provide medical diagnosis or treatment advice
2. NEVER ask for personal identifying information
3. Always recommend consulting healthcare providers for medical decisions
4. Provide general, educational health information only
5. Be empathetic and supportive

Query Type: {classification}
User Query: "{anon_message}"

Provide a helpful, educational response (2-3 sentences max):"""

            bot_response = gemini_service.chat(context_prompt)

            # 5️⃣ ADD SAFETY DISCLAIMER
            disclaimers = {
                'SYMPTOM': '⚠️ For symptom evaluation, please consult a healthcare provider.\n\n',
                'TEST_RESULT': '⚠️ For test result interpretation, please speak with your doctor.\n\n',
                'MEDICATION': '⚠️ For medication questions, consult your pharmacist or doctor.\n\n',
                'VITAL_SIGNS': '⚠️ For vital sign concerns, contact your healthcare provider.\n\n'
            }
            
            disclaimer = disclaimers.get(classification, '')
            final_response = disclaimer + bot_response

            # 6️⃣ LOG TO DATABASE (ANONYMIZED)
            log_conversation(db, user_hash, anon_message, final_response, classification, phi_map, False)

            return jsonify({
                'response': final_response,
                'classification': classification,
                'anonymized': True,
                'phi_detected': len(phi_map) > 0,
                'timestamp': datetime.now().isoformat()
            }), 200

        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    # ----------------- Health logs API (from MongoDB) -----------------
    @app.route("/api/health-logs", methods=["GET"])
    def get_health_logs():
        """
        Returns health logs from the `health_logs` collection.

        Optional query parameters (matching the React Graph component):
          - start: start date (YYYY-MM-DD)
          - end:   end date   (YYYY-MM-DD)

        Documents in MongoDB use "date" as a string in "MM-DD-YYYY" format.
        This endpoint converts and filters correctly, then returns a plain list.
        """
        try:
            # Query params from frontend (YYYY-MM-DD)
            start_str = request.args.get("start")
            end_str = request.args.get("end")

            # Fetch all logs from MongoDB
            logs = list(db.health_logs.find())

            # Helper: parse "MM-DD-YYYY" into a Python date object
            def parse_mmddyyyy(s: str):
                return datetime.strptime(s, "%m-%d-%Y").date()

            # Parse query params if provided
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

            filtered_logs = []

            for log in logs:
                # Convert ObjectId to string for JSON serialization
                log["_id"] = str(log["_id"])

                date_str = log.get("date")
                if not date_str:
                    # Skip documents without a date
                    continue

                try:
                    log_date = parse_mmddyyyy(date_str)
                except ValueError:
                    # Skip invalid date formats
                    continue

                # Apply optional date range filters
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue

                filtered_logs.append(log)

            # Sort by date ascending using the "MM-DD-YYYY" field
            filtered_logs.sort(
                key=lambda x: datetime.strptime(x["date"], "%m-%d-%Y")
            )

            if start_date and end_date and start_date > end_date:
                return jsonify({"error": "Start date must not be after end date."}), 400

            if not filtered_logs:
                return jsonify({"error": "No health logs found between the selected date range."}), 404
       


            # Frontend expects a plain array here
            return jsonify(filtered_logs), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ----------------- Export data (CSV, PDF, JSON) -----------------
    @app.route("/api/export", methods=["POST"])
    def export_data():
        """Export health data in specified format (CSV, PDF, JSON)"""
        try:
            data = request.json
            categories = data.get("categories", [])
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            export_format = data.get("format", "csv")

            with open("data/health_logs_seed.json", "r") as f:
                health_logs = json.load(f)

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                now = datetime.now()
                if start > now:
                    return jsonify({"error": "Start date cannot be in the future."}), 400

            # Apply date filtering (seed file dates are MM-DD-YYYY)
            if start_date or end_date:
                filtered_logs = []
                for log in health_logs:
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
                health_logs = filtered_logs

            if categories:
                filtered_logs = []
                for log in health_logs:
                    filtered_log = {"date": log["date"]}

                    if "sleep" in categories and log.get("hours_of_sleep") is not None:
                        filtered_log["hours_of_sleep"] = log["hours_of_sleep"]

                    if "symptoms" in categories and log.get("symptom"):
                        filtered_log["symptom"] = log["symptom"]

                    if "mood" in categories and log.get("mood") is not None:
                        filtered_log["mood"] = log["mood"]

                    if "medications" in categories and log.get("took_medication") is not None:
                        filtered_log["took_medication"] = log["took_medication"]

                    if "vital_signs" in categories and log.get("vital_bpm") is not None:
                        filtered_log["vital_bpm"] = log["vital_bpm"]

                    filtered_logs.append(filtered_log)
                health_logs = filtered_logs



            # ---- CSV export ----
            if export_format == "csv":
                output = io.StringIO()

                if health_logs:
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
                    Paragraph(f"<b>Date Range:</b> {start_date} to {end_date}", info_style)
                )
                story.append(
                    Paragraph(f"<b>Categories:</b> {', '.join(categories)}", info_style)
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
                                "start": start_date,
                                "end": end_date,
                            },
                            "categories": categories,
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
            return jsonify({"error": str(e)}), 500

    # ----------------- Export preview -----------------
    @app.route("/api/export/preview", methods=["POST"])
    def preview_export():
        """Preview export data without downloading"""
        try:
            data = request.json
            categories = data.get("categories", [])
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            with open("data/health_logs_seed.json", "r") as f:
                health_logs = json.load(f)

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
                for log in health_logs:
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
                health_logs = filtered_logs

            if categories:
                filtered_logs = []
                for log in health_logs:
                    filtered_log = {"date": log["date"]}

                    if "sleep" in categories and log.get("hours_of_sleep") is not None:
                        filtered_log["hours_of_sleep"] = log["hours_of_sleep"]

                    if "symptoms" in categories and log.get("symptom"):
                        filtered_log["symptom"] = log["symptom"]

                    if "mood" in categories and log.get("mood") is not None:
                        filtered_log["mood"] = log["mood"]

                    if "medications" in categories and log.get("took_medication") is not None:
                        filtered_log["took_medication"] = log["took_medication"]

                    if "vital_signs" in categories and log.get("vital_bpm") is not None:
                        filtered_log["vital_bpm"] = log["vital_bpm"]

                    filtered_logs.append(filtered_log)
                health_logs = filtered_logs

            # If no data after filtering, return error
            if not health_logs:
                return jsonify({"error": "No data found between the selected date range."}), 404

            return jsonify(
                {
                    "preview": health_logs[:10],
                    "total_records": len(health_logs),
                    "categories_included": categories,
                    "date_range": {
                        "start": start_date,
                        "end": end_date,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

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

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)