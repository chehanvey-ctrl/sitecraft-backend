from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Load your OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# Allow frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request structure
class PromptRequest(BaseModel):
    prompt: str

# System prompt to control GPT behavior
system_prompt = {
    "role": "system",
    "content": (
        "You are a professional web designer. Return clean, semantic HTML for a business landing page. "
        "Do NOT include any <img> tags. Ensure strong headings, call-to-action buttons, and clearly labeled "
        "sections like hero, services, about, and contact. Use a single-column, mobile-first layout with basic inline styles. "
        "Avoid lorem ipsum and placeholder gibberish. Use <section> tags for layout. The HTML should be readable and attractive."
    )
}

# Main endpoint
@app.post("/generate")
async def generate_website(prompt_request: PromptRequest):
    user_prompt = {"role": "user", "content": prompt_request.prompt}

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[system_prompt, user_prompt],
            temperature=0.7
        )
        website_code = response.choices[0].message.content
        return {"html": website_code}
    except Exception as e:
        return {"error": str(e)}
