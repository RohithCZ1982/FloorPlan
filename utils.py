import google.generativeai as genai
import json
import base64
from io import BytesIO
from PIL import Image
import os
# At the top, after imports
import logging
logging.basicConfig(level=logging.INFO)

def generate_with_gemini(model, prompt, contents=None):
    try:
        if contents is None:
            contents = [prompt]
        else:
            contents = contents + [prompt]
        
        # Safety settings - using dictionary format with enum keys and threshold values
        # BLOCK_NONE allows all content (least restrictive), adjust as needed
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }
        
        response = model.generate_content(
            contents,
            generation_config={
                "response_mime_type": "text/plain",  # Or "image/png" for images
                "temperature": 0.7,
            },
            safety_settings=safety_settings,
        )
        return response
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in generate_with_gemini: {error_msg}")
        # Check for API key referrer blocking error
        if "API_KEY_HTTP_REFERRER_BLOCKED" in error_msg or "referer" in error_msg.lower():
            raise Exception(
                "API Key Configuration Error: Your API key has HTTP referrer restrictions enabled. "
                "HTTP referrer restrictions ONLY work for browser/client-side JavaScript calls. "
                "Your FastAPI server makes server-side API calls which don't send HTTP referrers. "
                "\n\nSOLUTION: In Google Cloud Console (https://console.cloud.google.com/apis/credentials):\n"
                "1. Click on your API key\n"
                "2. Under 'Application restrictions', change from 'HTTP referrers' to 'None'\n"
                "3. Save and wait 2-3 minutes\n"
                "\nNote: HTTP referrer restrictions cannot work for server-side API calls."
            )
        raise

def save_image(bytes_data, filename):
    os.makedirs("static/uploads", exist_ok=True)
    path = f"static/uploads/{filename}"
    with open(path, "wb") as f:
        f.write(bytes_data)
    return path

def estimate_costs(prompt):
    # Simple mock – in prod, chain to Gemini for real estimates
    base_cost = 50000
    return {
        "total": base_cost,
        "breakdown": {
            "Foundation": 10000,
            "Structure": 20000,
            "Finishes": 15000,
            "Eco-features": 5000
        },
        "savings_tips": "Use recycled materials to save 10%."
    }