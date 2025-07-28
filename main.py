from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from openai import OpenAI

# Init OpenAI client (new SDK style)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Init FastAPI app
app = FastAPI()

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for incoming JSON
class PromptRequest(BaseModel):
    prompt: str

# Define system prompt
system_prompt = {
    "role": "system",
    "content": (
        "You are a professional web designer. Return clean, semantic HTML for a business landing page. "
        "Do NOT include any <img> tags. Ensure strong headings, call-to-action buttons, and clearly labeled "
        "sections like hero, services, about, and contact. Use a single-column, mobile-first layout with basic inline styles. "
        "Avoid lorem ipsum and placeholder gibberish. Use <section> tags for layout. The HTML should be readable and attractive."
    )
}

# POST endpoint to generate website HTML
@app.post("/generate")
async def generate_website(prompt_request: PromptRequest):
    user_prompt = {"role": "user", "content": prompt_request.prompt}
    
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[system_prompt, user_prompt],
            temperature=0.7,
        )
        html_content = chat_response.choices[0].message.content
        return {"html": html_content}
    except Exception as e:
        return {"error": str(e)}
