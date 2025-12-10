# Baymax Healthcare Dashboard

Full-stack healthcare app with document upload + AI chat, health logging, data visualization, and data export.

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

## Environment Configuration

### Backend Environment Variables

Create a [`backend/.env`](backend/.env) file with the following variables:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/baymax?retryWrites=true&w=majority
MONGODB_NAME=baymax

# Google Gemini API (for AI chatbot)
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Authentication
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Flask Configuration
FLASK_SECRET_KEY=super-secret-key-change-this
FLASK_ENV=development
```

**How to get these keys:**

1. **MongoDB URI**: 
   - Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a cluster and database user
   - Get connection string from "Connect" → "Connect your application"
   - Replace `<password>` with your database user password
   - Whitelist your IP address in Network Access

2. **Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with Google account
   - Click "Get API Key" → "Create API key"

3. **Supabase JWT Secret**:
   - Go to your [Supabase project](https://supabase.com/dashboard)
   - Navigate to Settings → API
   - Copy the JWT Secret value

### Frontend Environment Variables

Create a [`frontend/.env.local`](frontend/.env.local) file with:

```bash
# Supabase Configuration (for user authentication)
REACT_APP_SUPABASE_URL=your_supabase_project_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API URL
REACT_APP_API_BASE_URL=http://localhost:5001
```

**How to get these keys:**

1. **Supabase URL & Anon Key**:
   - Create a project at [Supabase](https://supabase.com)
   - Go to Settings → API
   - Copy "Project URL" → use as `REACT_APP_SUPABASE_URL`
   - Copy "anon public" key → use as `REACT_APP_SUPABASE_ANON_KEY`

2. **API Base URL**:
   - For local development: `http://localhost:5001`
   - For production: Your deployed backend URL

## Setup External Services

### 1. MongoDB Atlas Setup
- Create account at https://www.mongodb.com/cloud/atlas
- Create a new cluster (free tier available)
- Create database user with password
- Whitelist your IP address (0.0.0.0/0 for development)
- Get connection string and add to [`backend/.env`](backend/.env)

### 2. Supabase Setup
- Create account at https://supabase.com
- Create new project
- Enable Google OAuth:
  - Go to Authentication → Providers
  - Enable Google provider
  - Add authorized redirect URLs
- Copy API credentials to both [`backend/.env`](backend/.env) and [`frontend/.env.local`](frontend/.env.local)

### 3. Google Gemini API Setup
- Visit https://makersuite.google.com/app/apikey
- Create API key for Gemini 2.5 Flash model
- Add key to [`backend/.env`](backend/.env)

## Installation

See [`SETUP.md`](SETUP.md) for detailed installation instructions.

## Features

- **AI Chat**: Talk to Baymax about your health using Gemini AI
- **Document Upload**: Upload medical documents (PDF/images) with OCR processing
  - **Note**: Prescription uploads are not permitted. Other medical documents (lab reports, medical records, etc.) are accepted.
- **Health Logging**: Track medications, sleep, vitals, mood, and symptoms
- **Data Visualization**: View trends with interactive graphs (Recharts)
- **Data Export**: Export health data in CSV, PDF, or JSON formats
- **User Authentication**: Secure login with Google OAuth via Supabase

## Security Notes

- Never commit `.env` files to version control
- Keep your API keys and secrets confidential
- Use strong, unique passwords for database users
- Enable IP whitelisting for MongoDB in production
- Rotate API keys regularly
- Use environment-specific configurations (development vs. production)

## Troubleshooting

**MongoDB Connection Issues:**
- Verify your IP is whitelisted in MongoDB Atlas
- Check that password in connection string is correct
- Ensure network connectivity

**Supabase Authentication Issues:**
- Verify redirect URLs are correctly configured
- Check that API keys match your Supabase project
- Ensure OAuth provider is enabled

**Gemini API Issues:**
- Confirm API key is active and has quota
- Check for any billing requirements
- Verify API key has correct permissions

For more help, see [`SETUP.md`](SETUP.md) or contact the team.