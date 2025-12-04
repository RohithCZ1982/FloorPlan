from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os
from utils import generate_with_gemini, save_image, estimate_costs

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")  # Use 'gemini-1.5-pro' for better quality

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
        floor_prompt = open("prompts/floorplan.txt").read().format(user_prompt=prompt)
        floor_response = generate_with_gemini(model, floor_prompt, contents)
        floor_img = floor_response.parts[0].file if floor_response.parts else None

        # Generate exterior
        exterior_prompt = open("prompts/exterior.txt").read().format(user_prompt=prompt)
        exterior_response = generate_with_gemini(model, exterior_prompt, contents)
        exterior_img = exterior_response.parts[0].file if exterior_response.parts else None

        # Cost breakdown
        cost_data = estimate_costs(prompt)

        # Structural check (simple)
        check_prompt = open("prompts/structural_check.txt").read().format(user_prompt=prompt)
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
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/viewer")
async def viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})
