# Baymax Setup Guide

This guide will help you get the Baymax project running on your local machine.

## Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.9 or higher)
- **Git**
- **MongoDB Atlas account access** (get password from teammate)

## Step 1: Clone the Repository

```bash
git clone https://github.com/jihyeleekr/Baymax.git
cd Baymax
```

## Step 2: Backend Setup

### Install Python Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Create Environment Variables

Create a file called `backend/.env`:

```bash
MONGODB_URI=mongodb+srv://jh020211_db_user:YOUR_PASSWORD_HERE@baymax.b816vg3.mongodb.net/baymax?retryWrites=true&w=majority&appName=Baymax
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
FLASK_SECRET_KEY=super-secret-key-change-this
FLASK_ENV=development
```

**Important:** Replace `YOUR_PASSWORD_HERE` with the MongoDB password (ask teammate who set it up).

### Start Backend Server

```bash
python app.py
```

You should see:
```
✅ Connected to MongoDB successfully!
* Running on http://127.0.0.1:5001
```

## Step 3: Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm start
```

Browser should open automatically at http://localhost:3000

## Step 4: Verify Everything Works

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5001
- **Health Check**: http://localhost:5001/health

The health check should show `"database": "connected"`

## Git Workflow

Always work on feature branches:

```bash
# Create feature branch
git checkout main
git pull origin main
git checkout -b feature/yourname-feature

# Work on your code
git add .
git commit -m "Description of changes"
git push origin feature/yourname-feature

# Create Pull Request on GitHub for review
```

## Troubleshooting

### MongoDB Connection Error
- Make sure you have the correct password in `.env`
- Verify your IP is whitelisted in MongoDB Atlas

### Port Already in Use
- Backend: Change port in `app.py` (default: 5001)
- Frontend: Change port with `PORT=3001 npm start`

### Module Not Found
- Backend: Make sure venv is activated, run `pip install -r requirements.txt`
- Frontend: Run `npm install`

## Need Help?

Ask in the team chat!