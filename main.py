from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from jinja2 import Template
import traceback

# Load OpenAI key securely
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize FastAPI
app = FastAPI()

# Allow frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],  # Update if domain changes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        prompt = request.prompt
        print("🟡 Prompt received:", prompt)

        # Generate image from OpenAI DALL·E
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
        print("🟢 DALL·E image URL:", image_url)

        # Pick template file based on prompt
        template_name = "bold_brand_builder.html"
        if "portfolio" in prompt.lower() and "clean" in prompt.lower():
            template_name = "clean_professional_portfolio.html"
        elif "consultant" in prompt.lower():
            template_name = "clean_consultant_portfolio.html"
        elif "startup" in prompt.lower():
            template_name = "modern_startup_launch.html"
        elif "digital creator" in prompt.lower() or "youtube" in prompt.lower():
            template_name = "vibrant_digital_creator.html"

        template_path = f"templates/{template_name}"
        print("📄 Using template:", template_path)

        # Load HTML template
        with open(template_path, "r", encoding="utf-8") as file:
            template = Template(file.read())

        # Render HTML with variables
        html_code = template.render(
            image_url=image_url,
            prompt=prompt,
            site_name="SiteCraft AI",
            site_tagline="We turn your ideas into live websites.",
            about_us="We are passionate about clean, modern design and practical web experiences.",
            services="Custom websites, UX/UI design, SEO optimization, branding and more.",
            value_proposition="We blend technology with creativity to help you stand out online.",
            contact_email="hello@sitecraft.ai",
            contact_phone="+44 1234 567890",
            year="2025"
        )

        return {"html": html_code}

    except Exception as e:
        print("🔥 Error occurred:", str(e))
        traceback.print_exc()
        return {"error": "An error occurred while generating the site."}, 500
