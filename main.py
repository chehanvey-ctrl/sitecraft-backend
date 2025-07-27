from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from openai import OpenAI

# Define the request body structure
class PromptRequest(BaseModel):
    prompt: str

# Initialize FastAPI app
app = FastAPI()

# Allow frontend requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to specific domain if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the system prompt (forces HTML + Unsplash images + clean design)
SYSTEM_PROMPT = """
You are a professional web designer.

Generate a clean, modern, single-page HTML website based on the user's idea.
- Must include full valid HTML5 structure (doctype, html, head, body)
- Use sleek fonts and mobile-responsive CSS (in a <style> block)
- Insert relevant images using Unsplash like:
  <img src="https://source.unsplash.com/1600x900/?<relevant_keyword>">

Only return the HTML. No explanations or extra text.
"""

@app.post("/generate")
async def generate_site(request: PromptRequest):
    full_prompt = SYSTEM_PROMPT + "\n\nUser prompt: " + request.prompt

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}]
        )
        html_code = response.choices[0].message.content.strip()
        return JSONResponse(content={"html": html_code})
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
