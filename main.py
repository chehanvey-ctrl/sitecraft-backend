from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate", response_class=HTMLResponse)
async def generate_website(request: PromptRequest):
    user_prompt = request.prompt

    # Combine the user prompt with a website layout instruction
    full_prompt = f"""
You are a web design assistant. Generate a professional, clean HTML5 website layout based on the following user description. Include:
- A centered hero section with heading and subheading
- Three feature/service cards
- Clean CSS styling
- A footer with contact or CTA

User prompt: {user_prompt}
Return only valid HTML with inline CSS.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful AI that returns clean HTML websites."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7,
        max_tokens=1800
    )

    html_content = response.choices[0].message.content
    return HTMLResponse(content=html_content)
