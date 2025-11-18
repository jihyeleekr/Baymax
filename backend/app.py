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

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # MongoDB connection
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['baymax']
    
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    
    # Routes
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy', 'database': 'connected'})
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Chat endpoint for Gemini integration"""
        if gemini_service is None:
            return jsonify({'error': 'Gemini API not configured'}), 500
        
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        try:
            response = gemini_service.chat(message)
            return jsonify({
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
<<<<<<< HEAD
    
    @app.route('/api/health-logs', methods=['GET'])
    def get_health_logs():
        """Get health logs with optional date filtering"""
        try:
            # Get query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            categories = request.args.getlist('categories')
            
            # Load data from seed file for now (in production, this would come from MongoDB)
            with open('data/health_logs_seed.json', 'r') as f:
                health_logs = json.load(f)
            
            # Filter by date range if provided
            if start_date or end_date:
                filtered_logs = []
                for log in health_logs:
                    log_date = datetime.strptime(log['date'], '%m-%d-%Y')
                    
                    if start_date:
                        start = datetime.strptime(start_date, '%Y-%m-%d')
                        if log_date < start:
                            continue
                    
                    if end_date:
                        end = datetime.strptime(end_date, '%Y-%m-%d')
                        if log_date > end:
                            continue
                    
                    filtered_logs.append(log)
                health_logs = filtered_logs
            
            # Filter by categories if provided
            if categories:
                filtered_logs = []
                for log in health_logs:
                    filtered_log = {'date': log['date']}
                    
                    if 'sleep' in categories and 'hours_of_sleep' in log:
                        filtered_log['hours_of_sleep'] = log['hours_of_sleep']
                    
                    if 'symptoms' in categories and 'symptom' in log:
                        filtered_log['symptom'] = log['symptom']
                    
                    if 'mood' in categories and 'mood' in log:
                        filtered_log['mood'] = log['mood']
                    
                    if 'medications' in categories and 'took_medication' in log:
                        filtered_log['took_medication'] = log['took_medication']
                    
                    if 'vital_signs' in categories and 'vital_bpm' in log:
                        filtered_log['vital_bpm'] = log['vital_bpm']
                    
                    filtered_logs.append(filtered_log)
                health_logs = filtered_logs
            
            return jsonify({
                'data': health_logs,
                'count': len(health_logs),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export', methods=['POST'])
    def export_data():
        """Export health data in specified format"""
        try:
            data = request.json
            categories = data.get('categories', [])
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            export_format = data.get('format', 'csv')  # csv, pdf, or json
            
            # Get filtered data
            with open('data/health_logs_seed.json', 'r') as f:
                health_logs = json.load(f)
            
            # Apply date filtering
            if start_date or end_date:
                filtered_logs = []
                for log in health_logs:
                    log_date = datetime.strptime(log['date'], '%m-%d-%Y')
                    
                    if start_date:
                        start = datetime.strptime(start_date, '%Y-%m-%d')
                        if log_date < start:
                            continue
                    
                    if end_date:
                        end = datetime.strptime(end_date, '%Y-%m-%d')
                        if log_date > end:
                            continue
                    
                    filtered_logs.append(log)
                health_logs = filtered_logs
            
            # Apply category filtering
            if categories:
                filtered_logs = []
                for log in health_logs:
                    filtered_log = {'date': log['date']}
                    
                    if 'sleep' in categories and log.get('hours_of_sleep') is not None:
                        filtered_log['hours_of_sleep'] = log['hours_of_sleep']
                    
                    if 'symptoms' in categories and log.get('symptom'):
                        filtered_log['symptom'] = log['symptom']
                    
                    if 'mood' in categories and log.get('mood') is not None:
                        filtered_log['mood'] = log['mood']
                    
                    if 'medications' in categories and log.get('took_medication') is not None:
                        filtered_log['took_medication'] = log['took_medication']
                    
                    if 'vital_signs' in categories and log.get('vital_bpm') is not None:
                        filtered_log['vital_bpm'] = log['vital_bpm']
                    
                    filtered_logs.append(filtered_log)
                health_logs = filtered_logs
            
            # Create export file
            if export_format == 'csv':
                output = io.StringIO()
                
                if health_logs:
                    fieldnames = list(health_logs[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(health_logs)
                
                output.seek(0)
                
                # Create file-like object for sending
                file_output = io.BytesIO()
                file_output.write(output.getvalue().encode('utf-8'))
                file_output.seek(0)
                
                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f'health_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mimetype='text/csv'
                )
            
            elif export_format == 'pdf':
                # Create PDF
                file_output = io.BytesIO()
                doc = SimpleDocTemplate(file_output, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=1  # Center alignment
                )
                story.append(Paragraph("Baymax Health Data Export", title_style))
                
                # Export info
                info_style = styles['Normal']
                story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
                story.append(Paragraph(f"<b>Date Range:</b> {start_date} to {end_date}", info_style))
                story.append(Paragraph(f"<b>Categories:</b> {', '.join(categories)}", info_style))
                story.append(Paragraph(f"<b>Total Records:</b> {len(health_logs)}", info_style))
                story.append(Spacer(1, 20))
                
                if health_logs:
                    # Create table data
                    fieldnames = list(health_logs[0].keys())
                    
                    # Format headers
                    headers = [name.replace('_', ' ').title() for name in fieldnames]
                    table_data = [headers]
                    
                    # Add data rows
                    for log in health_logs:
                        row = []
                        for field in fieldnames:
                            value = log.get(field, 'N/A')
                            if value is None:
                                value = 'N/A'
                            elif isinstance(value, bool):
                                value = 'Yes' if value else 'No'
                            row.append(str(value))
                        table_data.append(row)
                    
                    # Create table
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(table)
                else:
                    story.append(Paragraph("No data found for the selected criteria.", styles['Normal']))
                
                # Build PDF
                doc.build(story)
                file_output.seek(0)
                
                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f'health_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    mimetype='application/pdf'
                )
            
            elif export_format == 'json':
                output = json.dumps({
                    'export_info': {
                        'generated_at': datetime.now().isoformat(),
                        'date_range': {
                            'start': start_date,
                            'end': end_date
                        },
                        'categories': categories,
                        'total_records': len(health_logs)
                    },
                    'data': health_logs
                }, indent=2)
                
                file_output = io.BytesIO()
                file_output.write(output.encode('utf-8'))
                file_output.seek(0)
                
                return send_file(
                    file_output,
                    as_attachment=True,
                    download_name=f'health_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    mimetype='application/json'
                )
            
            else:
                return jsonify({'error': 'Unsupported export format'}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/preview', methods=['POST'])
    def preview_export():
        """Preview export data without downloading"""
        try:
            data = request.json
            categories = data.get('categories', [])
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            # Get filtered data (same logic as export but return as JSON)
            with open('data/health_logs_seed.json', 'r') as f:
                health_logs = json.load(f)
            
            # Apply date filtering
            if start_date or end_date:
                filtered_logs = []
                for log in health_logs:
                    log_date = datetime.strptime(log['date'], '%m-%d-%Y')
                    
                    if start_date:
                        start = datetime.strptime(start_date, '%Y-%m-%d')
                        if log_date < start:
                            continue
                    
                    if end_date:
                        end = datetime.strptime(end_date, '%Y-%m-%d')
                        if log_date > end:
                            continue
                    
                    filtered_logs.append(log)
                health_logs = filtered_logs
            
            # Apply category filtering
            if categories:
                filtered_logs = []
                for log in health_logs:
                    filtered_log = {'date': log['date']}
                    
                    if 'sleep' in categories and log.get('hours_of_sleep') is not None:
                        filtered_log['hours_of_sleep'] = log['hours_of_sleep']
                    
                    if 'symptoms' in categories and log.get('symptom'):
                        filtered_log['symptom'] = log['symptom']
                    
                    if 'mood' in categories and log.get('mood') is not None:
                        filtered_log['mood'] = log['mood']
                    
                    if 'medications' in categories and log.get('took_medication') is not None:
                        filtered_log['took_medication'] = log['took_medication']
                    
                    if 'vital_signs' in categories and log.get('vital_bpm') is not None:
                        filtered_log['vital_bpm'] = log['vital_bpm']
                    
                    filtered_logs.append(filtered_log)
                health_logs = filtered_logs
            
            return jsonify({
                'preview': health_logs[:10],  # Show first 10 records
                'total_records': len(health_logs),
                'categories_included': categories,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
=======
        
    @app.route("/api/health-logs", methods=["GET"])
    def get_health_logs():
        """
        Returns health logs from the `health_logs` collection.
        Optional query parameters:
          - from: start date (MM-DD-YYYY)
          - to:   end date   (MM-DD-YYYY)
        If no dates are provided, all logs are returned.
        """
        try:
            start_str = request.args.get("from")
            end_str = request.args.get("to")

            # Fetch all logs from Mongo
            logs = list(db.health_logs.find())

            # Helper: parse "MM-DD-YYYY" into a Python date
            def parse_date_mmddyyyy(s: str):
                return datetime.strptime(s, "%m-%d-%Y").date()

            # Convert and optionally filter by date range
            filtered_logs = []
            start_date = parse_date_mmddyyyy(start_str) if start_str else None
            end_date = parse_date_mmddyyyy(end_str) if end_str else None

            for log in logs:
                # Convert ObjectId to string
                log["_id"] = str(log["_id"])

                # If date is missing or invalid, skip this log
                date_str = log.get("date")
                if not date_str:
                    continue

                try:
                    log_date = parse_date_mmddyyyy(date_str)
                except ValueError:
                    continue

                # Apply filters if provided
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue

                filtered_logs.append(log)

            # Sort by date ascending
            filtered_logs.sort(
                key=lambda x: datetime.strptime(x["date"], "%m-%d-%Y")
            )

            return jsonify(filtered_logs), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

>>>>>>> c41ed77 (Connect backend to MongoDB and add health logs API)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
