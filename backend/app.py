from dotenv import load_dotenv
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from services.gemini_service import GeminiService

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
        
        data = request.json  # NOW THIS IS INSIDE A ROUTE - IT WORKS!
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)