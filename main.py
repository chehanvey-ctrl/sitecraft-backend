from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS settings
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://sitecraft-frontend.onrender.com",  # Frontend hosted here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System prompt with better image handling and visual layout
SYSTEM_PROMPT = """
You are an expert web developer tasked with building clean, modern, responsive HTML websites.

Rules:
- Return ONLY valid HTML with inline CSS (no explanation).
- All images MUST be full external Unsplash links. Example: <img src='https://source.unsplash.com/800x600/?cakes,bakery'>
- Use sections, cards, modern colors, spacing, and styling.
- No Lorem Ipsum. Use realistic text that matches the user’s prompt.
- Make sure buttons, headers, and layout look visually appealing.
- Add a large, attractive hero section.
- Avoid broken image links. Do not use ./images or internal file paths.
- Always ensure it looks great on mobile.

The user will provide a short business idea. Generate a stunning preview website in response.
"""

# Define input format
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(request: PromptRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        website_html = response.choices[0].message.content
        return {"html": website_html}

    except Exception as e:
        return {"error": str(e)}
