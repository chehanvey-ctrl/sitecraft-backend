from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Load your OpenAI key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS (adjust frontend URL if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider locking this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body model
class PromptRequest(BaseModel):
    prompt: str

# System prompt to ensure consistent, full HTML
SYSTEM_PROMPT = """
You are a professional web developer. Your job is to take the user’s idea and return a complete, clean, working HTML website.

The HTML should:
- Include a <head> with meta, title, and embedded CSS
- Be fully responsive and styled using internal <style> tags
- Use external image URLs (from Unsplash or Pixabay) instead of local filenames
- Cover sections like hero, about, services, contact, or anything user specifies
- Never include explanations — return only raw HTML
"""

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

        html_output = response.choices[0].message.content.strip()

        # Minimal check to confirm GPT returned HTML
        if "<html" in html_output:
            return {"html": html_output}
        else:
            return {"error": "No valid HTML returned from model."}

    except Exception as e:
        print(f"[ERROR]: {e}")
        return {"error": str(e)}
