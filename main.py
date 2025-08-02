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
Create a beautiful one-page responsive website using only HTML and embedded CSS.

The site should include:
- A full-width hero image using this image URL: {image_url}
- A bold and catchy H1 website title inspired by: "{prompt}"
- A professional tagline under the title
- 5 visually distinct, well-structured content sections (e.g. About, Services, Features, Testimonials, Contact)
- A clean footer with copyright
Use elegant formatting, soft section background colors, good spacing, and smooth layout. Return only valid HTML, nothing else.
                """}
            ],
            temperature=0.7,
            max_tokens=1800
        )
        html_code = html_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"HTML generation failed: {e}")
        html_code = f"<h1>Failed to generate site.</h1><p>{e}</p>"

    return {"html": html_code}


# Only needed for local testing or deployment on platforms like Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
