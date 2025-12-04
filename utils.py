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
        
        response = model.generate_content(
            contents,
            generation_config={
                "response_mime_type": "text/plain",  # Or "image/png" for images
                "temperature": 0.7,
            },
            safety_settings={
                "HARASSMENT": genai.types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                "HATE_SPEECH": genai.types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                "SEXUALLY_EXPLICIT": genai.types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                "DANGEROUS_CONTENT": genai.types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
            },
        )
        return response
    except Exception as e:
        logging.error(f"Error in generate_with_gemini: {str(e)}")
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