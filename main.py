from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from openai import OpenAI

# Create FastAPI app
app = FastAPI()

# Allow frontend to access this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or set to your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 👇 SYSTEM PROMPT DEFINED HERE
SYSTEM_PROMPT = """
You are a professional web designer.

Generate a clean, mobile-responsive HTML5 website based on the user's idea.
- Return full HTML (with doctype, head, and body)
- Style with embedded <style> block (modern, readable fonts)
- Use <img> tags with Unsplash images like:
  <img src="https://source.unsplash.com/1600x900/?gym-equipment">

IMPORTANT:
- Replace all spaces in Unsplash keywords with dashes
- Do NOT include any broken or local image paths
- Use at least one relevant Unsplash image in the design

Return only valid HTML. No markdown, no explanations.
"""

# Request model
class PromptRequest(BaseModel):
    prompt: str

# POST route for generating HTML
@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    html_code = response.choices[0].message.content
    return JSONResponse(content={"html": html_code})
