from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os
import html
from utils import generate_with_gemini, save_image, estimate_costs

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
genai.configure(api_key=api_key)
# Try gemini-1.5-flash first (faster, cheaper), fallback to gemini-1.5-pro if needed
try:
    model = genai.GenerativeModel("gemini-2.0-flash-001)
except Exception as e:
    print(f"Warning: Could not load gemini-1.5-flash, trying gemini-1.5-pro: {e}")
    model = genai.GenerativeModel("gemini-2.5-pro")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/dream")
async def generate_dream(
    prompt: str = Form(...),
    images: list[UploadFile] = File(None),
    request: Request = None
):
    try:
        contents = [prompt]
        image_paths = []
        for img in images or []:
            bytes_data = await img.read()
            path = save_image(bytes_data, img.filename)
            contents.append(genai.upload_file(path))
            image_paths.append(path)

        # Generate floor plan
        with open("prompts/floorplan.txt", "r") as f:
            floor_prompt = f.read().format(user_prompt=prompt)
        floor_response = generate_with_gemini(model, floor_prompt, contents)
        floor_img = None
        if floor_response.parts:
            for part in floor_response.parts:
                if hasattr(part, 'file') and part.file:
                    floor_img = part.file
                    break

        # Generate exterior
        with open("prompts/exterior.txt", "r") as f:
            exterior_prompt = f.read().format(user_prompt=prompt)
        exterior_response = generate_with_gemini(model, exterior_prompt, contents)
        exterior_img = None
        if exterior_response.parts:
            for part in exterior_response.parts:
                if hasattr(part, 'file') and part.file:
                    exterior_img = part.file
                    break

        # Cost breakdown
        cost_data = estimate_costs(prompt)

        # Structural check (simple)
        with open("prompts/structural_check.txt", "r") as f:
            check_prompt = f.read().format(user_prompt=prompt)
        check_response = generate_with_gemini(model, check_prompt, contents)
        
        # Safely extract text from response
        check_text = ""
        if check_response and check_response.parts:
            for part in check_response.parts:
                if hasattr(part, 'text') and part.text:
                    check_text = part.text
                    break
        if not check_text:
            check_text = "Structural analysis completed."

        return templates.TemplateResponse("chat.html", {
            "request": request,
            "floor_img": floor_img,
            "exterior_img": exterior_img,
            "cost_data": cost_data,
            "check": check_text,
            "prompt": prompt
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in /dream endpoint: {error_msg}")
        print(f"Traceback: {error_trace}")
        # Return HTML error message that HTMX can display with more details
        # Escape HTML to prevent XSS
        error_msg_escaped = html.escape(error_msg)
        error_trace_escaped = html.escape(error_trace)
        error_html = f'''
        <div class="bg-red-600 p-4 rounded-lg">
            <h3 class="font-bold mb-2 text-xl">Error</h3>
            <p class="mb-2"><strong>Error Message:</strong> {error_msg_escaped}</p>
            <details class="mt-2">
                <summary class="cursor-pointer text-sm underline">Show technical details</summary>
                <pre class="mt-2 text-xs bg-red-700 p-2 rounded overflow-auto max-h-40">{error_trace_escaped}</pre>
            </details>
        </div>
        '''
        return HTMLResponse(
            status_code=500,
            content=error_html
        )

@app.get("/viewer")
async def viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})

@app.get("/test-api")
async def test_api():
    """Simple endpoint to test if the Gemini API is working"""
    try:
        test_response = model.generate_content("Say 'API is working' if you can read this.")
        return JSONResponse({
            "status": "success",
            "message": test_response.text if hasattr(test_response, 'text') else str(test_response),
            "api_key_set": bool(api_key)
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "api_key_set": bool(api_key)
            }
        )
