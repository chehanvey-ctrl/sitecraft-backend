from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Initialize FastAPI app
app = FastAPI()

# Allow only your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenAI with secure API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request body model
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # Generate AI image with DALL·E 3
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="standard",
        response_format="url"
    )
    image_url = image_response.data[0].url

    # Generate website HTML + CSS from GPT
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional web developer. Return a full modern HTML5 website with embedded CSS in <style> tags. "
                    "Use clean, responsive design with distinct sections (hero, about, features, contact). "
                    "Leave a section below the hero titled 'Featured Visual' and insert this image URL into an <img> tag: "
                    f"{image_url} — don't modify it. Do not add explanations. Return only raw code."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    html_code = completion.choices[0].message.content
    return { "html": html_code }
