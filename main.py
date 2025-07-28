from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend origin for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        prompt = request.prompt

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior front-end developer. "
                        "Generate a modern, clean, responsive HTML+CSS website. "
                        "Use clear sectioning and great typography. "
                        "Return ONLY valid raw HTML+CSS – no markdown or explanations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        site_code = response["choices"][0]["message"]["content"]
        return {"html": site_code}  # ✅ FIXED key to match frontend

    except Exception as e:
        return {"error": str(e)}
