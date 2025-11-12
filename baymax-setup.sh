#!/bin/bash

echo "🏥 Setting up Baymax project..."

# Root .gitignore
cat > .gitignore << 'EOF'
.env
.env.local
__pycache__/
*.py[cod]
venv/
node_modules/
build/
dist/
.DS_Store
EOF

# Create folders
mkdir -p frontend backend shared docs
mkdir -p backend/{api,models,services,utils,config,tests}

# ===== FRONTEND SETUP =====
echo "⚛️  Setting up React frontend..."
cd frontend

# Initialize React app (this takes a minute)
npx create-react-app . --silent

# Install dependencies
npm install --silent axios @supabase/supabase-js react-router-dom recharts

# Create folder structure
mkdir -p src/{components/{Auth,Dashboard,HealthLog,Medication,DocumentUpload,Chatbot,Visualization,Export,Shared},pages,services,hooks,context,utils,styles}

# Environment file
cat > .env.local << 'EOF'
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
REACT_APP_API_BASE_URL=http://localhost:5000
EOF

cd ..

# ===== BACKEND SETUP =====
echo "🐍 Setting up Flask backend..."
cd backend

# Create virtual environment
python3 -m venv venv

# Create __init__.py files
touch api/__init__.py models/__init__.py services/__init__.py utils/__init__.py config/__init__.py tests/__init__.py

# Requirements
cat > requirements.txt << 'EOF'
Flask==3.0.0
flask-cors==4.0.0
pymongo==4.6.0
python-dotenv==1.0.0
google-generativeai==0.3.2
PyJWT==2.8.0
gunicorn==21.2.0
EOF

# Install dependencies
source venv/bin/activate && pip install --quiet -r requirements.txt

# Environment file
cat > .env << 'EOF'
MONGODB_URI=your_mongodb_uri
GEMINI_API_KEY=your_gemini_key
SUPABASE_JWT_SECRET=your_jwt_secret
FLASK_SECRET_KEY=super-secret-key-change-this
FLASK_ENV=development
EOF

# Basic Flask app
cat > app.py << 'EOF'
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    
    @app.route('/')
    def index():
        return jsonify({"message": "Baymax API is running!"})
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
EOF

# Vercel config
cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [{"src": "app.py", "use": "@vercel/python"}],
  "routes": [{"src": "/(.*)", "dest": "app.py"}]
}
EOF

cd ..

# ===== ROOT README =====
cat > README.md << 'EOF'
# Baymax Healthcare Dashboard

Full-stack healthcare app with medication reminders, document upload + AI chat, health logging, data visualization, and data export.

## Quick Start

**Frontend:**
```bash
cd frontend
npm start
```

**Backend:**
```bash
cd backend
source venv/bin/activate
python app.py
```

## Tech Stack
React • Flask • MongoDB • Supabase • Gemini API • Vercel

## Setup External Services

1. **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas
2. **Supabase**: https://supabase.com
3. **Google Gemini API**: https://makersuite.google.com/app/apikey

Update the `.env` files with your API keys.
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. cd backend && source venv/bin/activate && python app.py"
echo "  2. Open new terminal: cd frontend && npm start"
echo "  3. Get API keys (MongoDB, Supabase, Gemini) and update .env files"