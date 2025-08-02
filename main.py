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

    # Step 1: Generate background image with DALL·E (no overlay text)
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, cinematic, professional website background, no text",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}")

    # Step 2: Generate full HTML layout with GPT-4
    try:
        html_response = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.75,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a highly creative and talented web designer. Create a modern, responsive one-page HTML site with the following features:\n"
                        "- Full-width hero section with the provided background image (no overlay text)\n"
                        "- Clean and elegant H1 title below the hero\n"
                        "- Five well-structured content sections relevant to the users prompt, with good spacing and clarity\n"
                        "- Visually distinct section backgrounds (soft colors or light gradients)\n"
                        "- Subtle borders or shadows between sections\n"
                        "- Clear mobile-friendly layout using HTML + embedded CSS only\n"
                        "- Add a simple footer\n"
                        "Do NOT use lorem ipsum. Use plain placeholder headings and meaningful filler content relevant to the prompt.\n"
                        "Return only valid HTML."
                    )
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\n\nUse this image for the hero background: {image_url}"
                }
            ]
        )
        html_code = html_response.choices[0].message.content.strip()

    except Exception as e:
        print(f"HTML generation failed: {e}")
        html_code = f"<h1>SiteCraft Error</h1><p>{e}</p>"

    return { "html": html_code }
