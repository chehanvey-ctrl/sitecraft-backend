from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from github import Github

# Initialize FastAPI app
app = FastAPI()

# ✅ CORSMiddleware – allow Vercel frontend (including OPTIONS for preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://t-pages.vercel.app"],  # your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],      # ✅ include OPTIONS
    allow_headers=["*"],
)

# ✅ Load API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")

# ✅ Request model
class PromptRequest(BaseModel):
    prompt: str

# ✅ /generate-pure – returns raw HTML preview
@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"

    # 🔹 Step 1: AI Image
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, professional background image, no
