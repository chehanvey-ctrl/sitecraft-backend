from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from jinja2 import Template

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # Default image
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

    # Title generation
    try:
        title_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a branding expert. Create a short and impactful website title."},
                {"role": "user", "content": f"Create a website title for: {prompt}"}
            ],
            temperature=0.8,
            max_tokens=20
        )
        title = title_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Title generation failed: {e}")
        title = "AI Website – SiteCraft AI"

    # Tagline generation
    try:
        tagline_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a branding expert. Write a one-line tagline for the website."},
                {"role": "user", "content": f"Write a professional tagline for this site:\n{prompt}"}
            ],
            temperature=0.7,
            max_tokens=30
        )
        tagline = tagline_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Tagline generation failed: {e}")
        tagline = "Built with AI brilliance in every pixel."

    # Section content generation
    try:
        sections_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative copywriter. Write 3 website sections with a heading and paragraph each."},
                {"role": "user", "content": f"Generate homepage sections for this prompt:\n{prompt}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        raw_text = sections_response.choices[0].message.content.strip()

        # Basic parsing: expects format like "## Section Title\nParagraph"
        section_lines = raw_text.split("\n")
        section_content = []
        current_section = {}

        for line in section_lines:
            if line.startswith("## "):
                if current_section:
                    section_content.append(current_section)
                current_section = {"heading": line.replace("## ", "").strip(), "body": ""}
            else:
                current_section["body"] += line.strip() + " "
        if current_section:
            section_content.append(current_section)

    except Exception as e:
        print(f"Section generation failed: {e}")
        section_content = [
            {"heading": "About Me", "body": "This is a custom AI-generated site tailored to your request."},
            {"heading": "What I Offer", "body": "Custom design, AI content, smart layout."},
            {"heading": "Why Work With Me", "body": "Built in seconds, styled to impress."}
        ]

    # Template selection
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

    # Load template and render
    try:
        with open(f"templates/{template_name}", "r") as file:
            template = Template(file.read())

        html_code = template.render(
            title=title,
            tagline=tagline,
            image_url=image_url,
            section_content=section_content,
            contact_email="hello@sitecraft.ai",
            contact_phone="+44 1234 567890",
            year="2025"
        )
    except FileNotFoundError:
        return {"html": f"<h1>❌ Template Error: {template_name} not found</h1>"}

    return {"html": html_code}
