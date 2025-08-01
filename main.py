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

@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # Default image fallback
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

    # 🎯 Generate dynamic title using GPT
    try:
        title_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a branding expert that creates short, catchy website titles."},
                {"role": "user", "content": f"Write a short and professional website title based on this description:\n{prompt}"}
            ],
            max_tokens=20,
            temperature=0.7
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
            site_name=title,  # Hero heading will use this
            site_tagline="Turning your ideas into reality",
            about_us="This is a custom AI-generated site tailored to your request.",
            services="Custom design, AI content, smart layout",
            value_proposition="Built in seconds, styled to impress.",
            contact_email="hello@sitecraft.ai",
            contact_phone="+44 1234 567890",
            year="2025"
        )
    except FileNotFoundError:
        return { "html": f"<h1>❌ Template Error: {template_name} not found</h1>" }

    return { "html": html_code }
