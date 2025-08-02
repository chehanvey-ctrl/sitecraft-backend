from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from jinja2 import Template

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request body model
class PromptRequest(BaseModel):
    prompt: str

# 🧠 Route 1: Template-based AI site generation
@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # Default fallback image
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"

    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}")

    # 🎯 Generate AI title
    try:
        title_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a branding expert that creates short, catchy website titles."},
                {"role": "user", "content": f"Write a short and professional website title based on this description:\n{prompt}"}
            ],
            temperature=0.8,
            max_tokens=20
        )
        title = title_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Title generation failed: {e}")
        title = "AI Website – SiteCraft AI"

    # Match prompt to correct template
    prompt_lower = prompt.lower()
    if "business" in prompt_lower:
        template_name = "modern_startup_launchpad.html"
    elif "portfolio" in prompt_lower:
        template_name = "clean_consultant_portfolio.html"
    elif "blog" in prompt_lower:
        template_name = "vibrant_digital_creator.html"
    elif "ecommerce" in prompt_lower:
        template_name = "bold_brand_builder.html"
    else:
        template_name = "clean_professional_portfolio.html"

    # Load and render template
    try:
        with open(f"templates/{template_name}", "r") as file:
            template = Template(file.read())

        html_code = template.render(
            title=title,
            prompt=prompt,
            image_url=image_url,
            site_name=title,
            about_us="This is a custom AI-generated site tailored to your request.",
            services="Custom design, AI content, smart layout",
            value_proposition="Built in seconds, styled to impress.",
            contact_email="hello@sitecraft.ai",
            contact_phone="+44 1234 567890",
            year="2025"
        )
    except FileNotFoundError:
        return {"html": f"<h1>❌ Template Error: {template_name} not found</h1>"}

    return {"html": html_code}

# 🆕 Route 2: Pure AI site generation (no templates)
@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt

    # Default fallback image
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"

    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}")

    try:
        content_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional web copywriter and HTML/CSS developer. "
                        "Generate a complete modern HTML page including a full-width hero image section, "
                        "a title section, tagline section, and at least three styled content sections. "
                        "Use only inline CSS or minimal embedded styles. No JavaScript. Use the image URL provided."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
Prompt: {prompt}
Image URL to include as hero: {image_url}
Generate full HTML below:
"""
                }
            ],
            temperature=0.7,
            max_tokens=1200
        )
        html_code = content_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI HTML generation failed: {e}")
        html_code = "<h1>Sorry, something went wrong generating your AI site.</h1>"

    return {"html": html_code}
