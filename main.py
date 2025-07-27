from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Set your OpenAI API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(request: PromptRequest):
    user_prompt = request.prompt

    try:
        # Step 1: Generate image with DALL·E 3
        dalle_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"Website hero banner illustration for: {user_prompt}. Modern, clean and visually engaging.",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = dalle_response.data[0].url

        # Step 2: Generate HTML using GPT-4
        system_prompt = """
You are a professional web developer AI.
Generate a complete HTML page using clean, semantic HTML and inline CSS.
Make it visually appealing, mobile-friendly, and include the provided image at the top of the page as a banner.
Do not include <script> tags.
The content should be based on the user's description.
"""

        response = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Prompt: {user_prompt}\nImage URL: {image_url}"},
            ],
            temperature=0.7,
        )

        html_code = response.choices[0].message.content.strip()
        return {"html": html_code}

    except Exception as e:
        return {"error": str(e)}
