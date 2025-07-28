from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

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
    user_prompt = request.prompt

    # Generate image using DALL·E
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"Website hero illustration for: {user_prompt}",
        n=1,
        size="1024x1024"
    )

    image_url = image_response['data'][0]['url']

    # Generate website HTML
    html_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert web developer. Create a beautiful, modern, responsive single-page website. "
                    "Use semantic HTML5 and embed CSS in <style> tags. Return only the code. Add a placeholder "
                    "div with the ID 'ai-image' where the AI image will be inserted via frontend."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    site_code = html_response.choices[0].message.content

    return {
        "html": site_code,
        "image_url": image_url
    }
