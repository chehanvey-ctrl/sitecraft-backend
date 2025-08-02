from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

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
        chat_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert web designer and HTML developer."},
                {"role": "user", "content": f"""
Create a beautiful one-page responsive website using only HTML and embedded CSS. Include a full-width hero image using this image URL: {image_url}.

The site should include:
- An H1 title inspired by this prompt: {prompt}
- A tagline under the title
- At least five clean, modern content sections (e.g., About, Services, Testimonials, Gallery, Contact)
- A footer

Use elegant layout, consistent colors, clean fonts, and spacing. Return only valid HTML. Do not explain anything, just return the code.
"""}
            ],
            temperature=0.7,
            max_tokens=1800
        )
        html_code = chat_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"HTML generation failed: {e}")
        html_code = f"<h1>Failed to generate site.</h1><p>{e}</p>"

    return {"html": html_code}
