# Baymax Setup Guide

Complete installation and configuration guide for the Baymax Healthcare Dashboard.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Repository](#clone-the-repository)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [External Services Configuration](#external-services-configuration)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have the following installed on your system:

- **Node.js** (v16 or higher) and npm
- **Python** (v3.9 or higher)
- **Git**
- **MongoDB Compass** (optional, for database management)
- **Code editor** (VS Code recommended)

### Verify installations:

```bash
node --version
npm --version
python3 --version
git --version
```

---

## Clone the Repository

```bash
git clone https://github.com/jihyeleekr/Baymax.git
cd Baymax
```

---

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Python Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

Create a file named `.env` in the `backend` directory:

```bash
touch .env
```

Add the following content (replace with your actual values):

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/baymax?retryWrites=true&w=majority
MONGODB_NAME=baymax

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Authentication
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Flask Configuration
FLASK_SECRET_KEY=your_super_secret_key_change_this
FLASK_ENV=development
REACT_APP_API_BASE_URL=http://127.0.0.1:5001

# Optional: For Supabase integration
REACT_APP_SUPABASE_URL=your_supabase_project_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 5. Verify Backend Installation

```bash
python app.py
```

You should see:
```
✅ Gemini API configured
✅ Connected to MongoDB successfully!
✅ TTL index created for chat conversations
 * Running on http://127.0.0.1:5001
```

Press `Ctrl+C` to stop the server.

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd ../frontend
```

### 2. Install Node Dependencies

```bash
npm install
```

### 3. Create Environment File

Create a file named `.env.local` in the `frontend` directory:

```bash
touch .env.local
```

Add the following content:

```bash
# Supabase Configuration
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API URL
REACT_APP_API_BASE_URL=http://localhost:5001
```

### 4. Verify Frontend Installation

```bash
npm start
```

The app should open in your browser at `http://localhost:3000`.

Press `Ctrl+C` to stop the development server.

---

## External Services Configuration

### MongoDB Atlas Setup

1. **Create Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for a free account

2. **Create a Cluster**
   - Click "Build a Database"
   - Select "Free" tier (M0)
   - Choose a cloud provider and region closest to you
   - Click "Create Cluster"

3. **Create Database User**
   - Go to "Database Access" (left sidebar)
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `baymax_user` (or your choice)
   - Password: Create a strong password (save it!)
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access" (left sidebar)
   - Click "Add IP Address"
   - For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
   - For production: Add your specific IP address
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" (left sidebar)
   - Click "Connect" on your cluster
   - Select "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Add to your `backend/.env` as `MONGODB_URI`

### Google Gemini API Setup

1. **Get API Key**
   - Visit https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Get API Key"
   - Click "Create API key in new project" (or use existing)
   - Copy the API key

2. **Add to Environment**
   - Add the key to `backend/.env` as `GEMINI_API_KEY`

3. **Verify Quota**
   - Check https://ai.google.dev/pricing
   - Free tier includes 15 requests per minute
   - Monitor usage in Google AI Studio

### Supabase Setup

1. **Create Account**
   - Go to https://supabase.com
   - Sign up for a free account

2. **Create New Project**
   - Click "New Project"
   - Choose organization (or create new)
   - Project name: `baymax`
   - Database Password: Create strong password (save it!)
   - Region: Choose closest to you
   - Click "Create new project" (takes ~2 minutes)

3. **Get API Credentials**
   - Go to Settings → API
   - Copy "Project URL" → Use as `REACT_APP_SUPABASE_URL`
   - Copy "anon public" key → Use as `REACT_APP_SUPABASE_ANON_KEY`
   - Copy "service_role" key → Use as `SUPABASE_JWT_SECRET`

4. **Enable Google OAuth**
   - Go to Authentication → Providers
   - Click on "Google"
   - Toggle "Enable Google provider"
   - Enter Google OAuth credentials:
     - Go to https://console.cloud.google.com/
     - Create OAuth 2.0 Client ID
     - Add authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`
   - Save configuration

5. **Configure Redirect URLs**
   - Go to Authentication → URL Configuration
   - Add Site URL: `http://localhost:3000` (development)
   - Add Redirect URLs: 
     - `http://localhost:3000/**`
     - Your production URL (if deployed)

---

## Database Setup

### Verify Database Connection

You can use MongoDB Compass to view your data:

1. Open MongoDB Compass
2. Connect using your `MONGODB_URI`
3. Navigate to `baymax` database
4. View collections: `health_logs`, `user_profiles`, `chat_conversations`, etc.

---

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:5001
- Health Check: http://localhost:5001/health

---

## Testing

### Run Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests.test_export -v
python -m unittest tests.test_onboarding -v
python -m unittest tests.test_health_log -v

# Run with coverage
pip install coverage
coverage run -m unittest discover tests/
coverage report -m
coverage html  # Generate HTML report
open htmlcov/index.html  # View coverage report
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

---

## Troubleshooting

### Backend Issues

**MongoDB Connection Error:**
```
❌ MongoDB connection failed: ...
```

**Solutions:**
- Verify `MONGODB_URI` is correct in `.env`
- Check IP is whitelisted in MongoDB Atlas Network Access
- Ensure database user password is correct (no special characters that need encoding)
- Test connection using MongoDB Compass

**Gemini API Error:**
```
⚠️ Warning: GEMINI_API_KEY not found
```

**Solutions:**
- Verify `GEMINI_API_KEY` is in `backend/.env`
- Check API key is valid at https://makersuite.google.com/app/apikey
- Ensure you haven't exceeded rate limits (15 requests/min on free tier)

**Import Errors:**
```
ModuleNotFoundError: No module named '...'
```

**Solutions:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**Supabase Authentication Not Working:**

**Solutions:**
- Verify `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` in `.env.local`
- Check redirect URLs are configured in Supabase dashboard
- Ensure Google OAuth is enabled in Supabase
- Clear browser cache and cookies

**API Connection Error:**
```
Failed to fetch from http://localhost:5001
```

**Solutions:**
- Ensure backend is running on port 5001
- Check `REACT_APP_API_BASE_URL` in `.env.local`
- Verify CORS is enabled in `backend/app.py`
- Check browser console for detailed error messages

**Environment Variables Not Loading:**

**Solutions:**
- File must be named `.env.local` (not `.env`)
- Restart the development server after changing `.env.local`
- Verify variables start with `REACT_APP_`

### Port Already in Use

**Backend (Port 5001):**
```bash
# macOS/Linux
lsof -ti:5001 | xargs kill -9

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

**Frontend (Port 3000):**
```bash
# macOS/Linux
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Test Failures

**Database-related test failures:**
- Ensure MongoDB is running and accessible
- Run seed script to populate test data: `python scripts/seed_health_logs.py`
- Check database has correct collections

**Import errors in tests:**
```bash
# Must run tests from backend directory
cd backend
python -m unittest tests.test_export -v
```

---

## Production Deployment

### Environment Variables for Production

**Backend `.env`:**
- Set `FLASK_ENV=production`
- Use production MongoDB URI
- Use production Supabase credentials
- Generate strong `FLASK_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`

**Frontend `.env.production`:**
- Update `REACT_APP_API_BASE_URL` to production backend URL
- Use production Supabase URL and keys

### Security Checklist

- ✅ Never commit `.env` files
- ✅ Use environment-specific configurations
- ✅ Enable MongoDB IP whitelisting in production
- ✅ Rotate API keys regularly
- ✅ Use HTTPS for all production URLs
- ✅ Enable rate limiting on backend
- ✅ Set strong database passwords
- ✅ Review Supabase Row Level Security policies

---

## Additional Resources

- **MongoDB Atlas Documentation**: https://docs.atlas.mongodb.com/
- **Supabase Documentation**: https://supabase.com/docs
- **Google Gemini API Docs**: https://ai.google.dev/docs
- **React Documentation**: https://react.dev
- **Flask Documentation**: https://flask.palletsprojects.com/

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [README.md](README.md) for quick reference
2. Review error messages carefully
3. Check browser console and backend terminal for detailed errors
4. Verify all environment variables are set correctly
5. Ensure all external services are properly configured
6. Contact the development team for support