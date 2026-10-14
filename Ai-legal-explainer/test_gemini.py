"""
Gemini API Test Script

This script tests the Google Gemini API with your API key.
It will help verify if your API key is working correctly.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini_api():
    """Test the Gemini API with the provided API key."""
    try:
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ Error: GOOGLE_API_KEY not found in .env file")
            print("Please add your API key to the .env file like this:")
            print("GOOGLE_API_KEY=your_api_key_here")
            return
            
        print("🔑 Found API key in .env file")
        print("🔄 Testing connection to Gemini API...")
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test with a simple prompt
        prompt = "Hello! Please respond with 'API is working!' if you can read this."
        
        print("\n📤 Sending test request to Gemini...")
        response = model.generate_content(prompt)
        
        print("\n✅ Success! Gemini API is working correctly!")
        print("\n📝 Response from Gemini:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
    except Exception as e:
        print("\n❌ Error occurred while testing the API:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        
        # Provide specific guidance for common errors
        if "API key not valid" in str(e):
            print("\n🔑 The API key appears to be invalid or has been revoked.")
            print("Please generate a new API key from Google AI Studio:")
            print("https://aistudio.google.com/app/apikey")
        elif "quota" in str(e).lower():
            print("\n⚠️  You may have exceeded your API quota.")
            print("Check your usage and quota in Google Cloud Console:")
            print("https://console.cloud.google.com/apis/")
        elif "location" in str(e).lower():
            print("\n🌍 Make sure your API key has the correct location settings.")
            print("Check your API restrictions in Google Cloud Console.")

if __name__ == "__main__":
    print("🔍 Gemini API Tester")
    print("=" * 50)
    test_gemini_api()
