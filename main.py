from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

# Allow frontend requests from Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-pages.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Generate site from prompt using GPT and DALL·E
@app.post("/generate-pure")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # Generate background image from DALL·E 3
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"{prompt}, professional background image, no text, visually clean and accurate to theme.",
        n=1,
        size="1024x1024",
        quality="standard",
        response_format="url"
    )
    image_url = image_response.data[0].url

    # Generate full HTML with embedded image and prompt
    gpt_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You're a web design assistant. Generate a modern HTML5 landing page using the user's prompt and the provided image. Only output raw HTML, fully styled with inline or internal CSS. Do not use external libraries or JavaScript. Include the image as the background or hero section."
            },
            {
                "role": "user",
                "content": f"Prompt: {prompt}\nImage URL: {image_url}"
            }
        ]
    )

    html_code = gpt_response.choices[0].message.content

    return { "html": html_code }
