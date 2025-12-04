from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os
from utils import generate_with_gemini, save_image, estimate_costs

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-001")  # Use 'gemini-1.5-pro' for better quality

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
        floor_img = floor_response.parts[0].file if floor_response.parts and hasattr(floor_response.parts[0], 'file') else None

        # Generate exterior
        with open("prompts/exterior.txt", "r") as f:
            exterior_prompt = f.read().format(user_prompt=prompt)
        exterior_response = generate_with_gemini(model, exterior_prompt, contents)
        exterior_img = exterior_response.parts[0].file if exterior_response.parts and hasattr(exterior_response.parts[0], 'file') else None

        # Cost breakdown
        cost_data = estimate_costs(prompt)

        # Structural check (simple)
        with open("prompts/structural_check.txt", "r") as f:
            check_prompt = f.read().format(user_prompt=prompt)
        check_response = generate_with_gemini(model, check_prompt, contents)

        return templates.TemplateResponse("chat.html", {
            "request": request,
            "floor_img": floor_img,
            "exterior_img": exterior_img,
            "cost_data": cost_data,
            "check": check_response.text,
            "prompt": prompt
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in /dream endpoint: {error_msg}")
        print(f"Traceback: {error_trace}")
        # Return HTML error message that HTMX can display
        return HTMLResponse(
            status_code=500,
            content=f'<div class="bg-red-600 p-4 rounded-lg"><h3 class="font-bold mb-2">Error</h3><p>{error_msg}</p></div>'
        )

@app.get("/viewer")
async def viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})
