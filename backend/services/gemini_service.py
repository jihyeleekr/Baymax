import google.generativeai as genai
import os

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        genai.configure(api_key=api_key)
        # Use the LATEST stable text model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def chat(self, message):
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
