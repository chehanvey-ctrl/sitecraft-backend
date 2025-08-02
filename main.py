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

    # Full HTML generation prompt
    try:
        html_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert web designer and HTML developer."},
                {"role": "user", "content": f"""
                Create a beautiful, professional one-page responsive website using only HTML and embedded CSS.
                - Use this image as the full-width hero background: {image_url}
                - Include a clean navigation bar at the top
                - Generate an H1 title based on this idea: {prompt}
                - Generate a short tagline under the title
                - Include exactly 5 visually distinct content sections with professional wording
                - Add a clean footer
                - Make sure the layout is modern, spaced, and mobile-friendly
                Return only valid, complete HTML code.
                """}
            ],
            temperature=0.75,
            max_tokens=1800
        )
        html_code = html_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"HTML generation failed: {e}")
        html_code = f"<h1>Failed to generate site.</h1><p>{e}</p>"

    return {"html": html_code}
