from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import uvicorn
import os

# Initialize OpenAI client (will use OPENAI_API_KEY from environment)
client = OpenAI()

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request schema
class PromptRequest(BaseModel):
    prompt: str

# Define system prompt
SYSTEM_PROMPT = (
    "You are a professional web designer. Generate a single clean HTML page with inline CSS. "
    "It should be responsive and visually appealing. Use <img src='https://source.unsplash.com/featured/?bakery'> "
    "or similar to include images. DO NOT include any explanations, markdown, or code fences—return only raw HTML."
)

@app.post("/generate")
async def generate(request: PromptRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.7,
            max_tokens=3000,
        )

        html_code = response.choices[0].message.content.strip()

        if not html_code or "<html" not in html_code:
            return {"error": "No HTML returned."}

        return {"html": html_code}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
