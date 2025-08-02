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
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"

    try:
        image_response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = image_response['data'][0]['url']
    except Exception as e:
        print(f"Image generation failed: {e}")

    # GPT Title
    try:
        title_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a branding expert. Create a short, catchy website title."},
                {"role": "user", "content": f"Description: {prompt}"}
            ],
            max_tokens=20,
            temperature=0.7
        )
        title = title_response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Title generation failed: {e}")
        title = "AI Website – SiteCraft AI"

    # GPT Additional Content
    try:
        sections_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're an expert copywriter for websites. Based on the description, write:\n1. A short catchy tagline\n2. A 2–3 sentence About Us\n3. A bullet list of services (no more than 5)\n4. A strong value proposition paragraph"},
                {"role": "user", "content": prompt}
            ],
            temperature: 0.8
        )
        content = sections_response['choices'][0]['message']['content']

        # Quick parsing using line splits
        lines = content.split('\n')
        tagline = lines[0].strip()
        about_us = "\n".join(lines[1:3]).strip()
        services = "\n".join(lines[4:9]).strip()
        value = "\n".join(lines[10:]).strip()
    except Exception as e:
        print(f"Section generation failed: {e}")
        tagline = "Turning your ideas into reality"
        about_us = "This is a custom AI-generated site tailored to your request."
        services = "- Custom design\n- AI content\n- Smart layout"
        value = "Built in seconds, styled to impress."

    # Template matching
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

    # Template rendering
    try:
        with open(f"templates/{template_name}", "r") as file:
            template = Template(file.read())

        html_code = template.render(
            title=title,
            prompt=prompt,
            image_url=image_url,
            site_name=title,
            site_tagline=tagline,
            about_us=about_us,
            services=services,
            value_proposition=value,
            contact_email="hello@sitecraft.ai",
            contact_phone="+44 1234 567890",
            year="2025"
        )
    except FileNotFoundError:
        return { "html": f"<h1>❌ Template Error: {template_name} not found</h1>" }

    return { "html": html_code }
