from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
import datetime
import openai
import os

# ✅ Initialize FastAPI app
app = FastAPI()

# ✅ CORS: Only allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Jinja2 Template Loader (points to /templates folder)
env = Environment(loader=FileSystemLoader("templates"))

# ✅ Load OpenAI API key securely from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Define input schema for prompt request
class WebsiteRequest(BaseModel):
    prompt: str

# ✅ Template selector based on keywords in prompt
def select_template(prompt: str):
    prompt = prompt.lower()
    if any(kw in prompt for kw in ["startup", "launch", "tech", "modern"]):
        return "modern_startup_launchpad.html"
    elif any(kw in prompt for kw in ["bold", "brand", "marketing", "agency"]):
        return "bold_brand_builder.html"
    elif any(kw in prompt for kw in ["freelance", "consultant", "portfolio"]):
        return "clean_consultant_portfolio.html"
    elif any(kw in prompt for kw in ["creator", "youtuber", "influencer", "vibrant"]):
        return "vibrant_digital_creator.html"
    else:
        return "clean_professional_portfolio.html"

# ✅ DALL·E Image Generation using OpenAI SDK
def generate_dalle_image(prompt: str):
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        return response.data[0].url
    except Exception as e:
        print("❌ DALL·E error:", e)
        return ""  # Return empty string if DALL·E fails

# ✅ Website generator endpoint
@app.post("/generate", response_class=HTMLResponse)
async def generate_website(data: WebsiteRequest):
    try:
        user_prompt = data.prompt
        template_name = select_template(user_prompt)
        template = env.get_template(template_name)

        # ✅ Generate AI image
        ai_image_url = generate_dalle_image(user_prompt)

        # ✅ Fill template with variables
        html_content = template.render(
            site_name="SiteCraft",
            site_tagline="Your personal website generator using AI.",
            about_us="We use AI to make stunning websites in seconds.",
            services="Custom design, instant publishing, smart layouts.",
            value_proposition="No coding. No hassle. Just beautiful results.",
            contact_email="info@sitecraft.ai",
            contact_phone="+123456789",
            year=datetime.datetime.now().year,
            ai_image_url=ai_image_url
        )

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(content=f"<h1>Error generating website: {e}</h1>", status_code=500)
