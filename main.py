from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Initialize FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request body model
class PromptRequest(BaseModel):
    prompt: str

# Route for full AI site generation (no templates)
@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt

    # 1. Generate clean, text-free AI image
    clean_image_prompt = prompt + ", no text, no labels, no writing, no words, clean background, professional design"
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=clean_image_prompt,
        n=1,
        size="1024x1024",
        quality="standard",
        response_format="url"
    )
    image_url = image_response.data[0].url

    # 2. Generate site title + tagline
    title_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Create a short, catchy title and one-sentence tagline for a website based on this prompt: '{prompt}'"}]
    )
    title_parts = title_response.choices[0].message.content.strip().split("\n")
    title = title_parts[0].strip()
    tagline = title_parts[1].strip() if len(title_parts) > 1 else ""

    # 3. Generate 5 professional website sections
    sections = ["About", "Services", "Gallery", "Testimonials", "Contact"]
    section_contents = []
    for section in sections:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Write a short, clear, and professional '{section}' section for a website based on this prompt: '{prompt}'."}
            ]
        )
        section_contents.append({
            "title": section,
            "content": response.choices[0].message.content.strip()
        })

    # 4. Combine into HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f8f8f8;
                color: #333;
            }}
            header {{
                text-align: center;
                padding: 3em 1em 1em;
                background-color: #fff;
            }}
            header img {{
                max-width: 100%;
                height: auto;
                margin-bottom: 1em;
            }}
            h1 {{
                font-size: 2em;
                margin-bottom: 0.2em;
            }}
            p.tagline {{
                font-style: italic;
                color: #777;
                margin-bottom: 2em;
            }}
            section {{
                background-color: #fff;
                margin: 1em auto;
                padding: 1.5em;
                max-width: 800px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            }}
            section h2 {{
                font-size: 1.5em;
                margin-bottom: 0.5em;
                color: #444;
            }}
            footer {{
                text-align: center;
                padding: 2em 1em;
                font-size: 0.9em;
                color: #aaa;
            }}
        </style>
    </head>
    <body>
        <header>
            <img src="{image_url}" alt="Website Hero Image">
            <h1>{title}</h1>
            <p class="tagline">{tagline}</p>
        </header>
        {''.join([f"<section><h2>{sec['title']}</h2><p>{sec['content']}</p></section>" for sec in section_contents])}
        <footer>
            &copy; 2025. All rights reserved.
        </footer>
    </body>
    </html>
    """

    return { "html": html_code }
