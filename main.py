from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from openai import OpenAI

# Request body model
class PromptRequest(BaseModel):
    prompt: str

# FastAPI app setup
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt to guide HTML generation
SYSTEM_PROMPT = """
You are a professional web developer. When given a prompt, return only complete and clean HTML code for a landing page-style website.

The website must:
- Look modern and well-designed
- Use relevant royalty-free images from Unsplash (use full direct links like https://source.unsplash.com/1600x900/?bakery)
- Be fully responsive and mobile-friendly
- Include header, main content, and footer
- Style everything using inline CSS (keep it readable)
- Do NOT include external scripts or fonts
- Do NOT include explanations — just return the HTML only
"""

@app.post("/generate")
async def generate(request: PromptRequest):
    user_prompt = request.prompt

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    html_code = response.choices[0].message.content.strip()
    return JSONResponse(content={"html": html_code})

# Optional for local testing
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
