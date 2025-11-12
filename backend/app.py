from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    
    # Connect to MongoDB
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(
            mongodb_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=10000
        )
        # Test the connection
        client.admin.command('ping')
        app.db = client['baymax']
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        app.db = None
    
    @app.route('/')
    def index():
        return jsonify({"message": "Baymax API is running!"})
    
    @app.route('/health')
    def health():
        db_status = "disconnected"
        if app.db is not None:
            try:
                app.db.client.admin.command('ping')
                db_status = "connected"
            except:
                pass
        
        return jsonify({
            "status": "healthy",
            "database": db_status
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
