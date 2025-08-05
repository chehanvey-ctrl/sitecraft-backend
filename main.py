from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import requests

# === Setup ===
app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-pages.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === OpenAI Key ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Request Model ===
class PromptRequest(BaseModel):
    prompt: str

# === Generate Full AI Site ===
@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt

    # === 1. Generate AI Image ===
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    image_url = image_response.data[0].url

    # === 2. Generate HTML Content ===
    html_prompt = f"""
    You are a web designer AI. Write a modern, mobile-friendly HTML page for the following topic:
    "{prompt}". Use a clean layout, include a hero section, a short tagline, 2 sections of content,
    and embed this image at the top: {image_url}. Keep styles inline or basic classes.
    Do not include any scripts or forms.

    Return only raw HTML. No explanations.
    """
    html_completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": html_prompt}],
        temperature=0.7
    )
    html_code = html_completion.choices[0].message.content.strip()

    # === 3. Deploy to Vercel ===
    vercel_token = os.getenv("VERCEL_API_TOKEN")
    project_name = f"sitecraft-{str(hash(prompt))[1:9]}"  # Unique-ish project name

    files = [{
        "file": "index.html",
        "data": html_code
    }]

    deploy_payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {
            "framework": "other"
        }
    }

    headers = {
        "Authorization": f"Bearer {vercel_token}",
        "Content-Type": "application/json"
    }

    deploy_response = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers=headers,
        json=deploy_payload
    )

    if deploy_response.status_code != 200:
        return {"error": "Deployment to Vercel failed", "details": deploy_response.text}

    deploy_data = deploy_response.json()
    live_url = deploy_data.get("url", "")

    print("🚀 Vercel Live URL:", live_url)

    return {
        "html": html_code,
        "site_url": live_url
    }
