from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(prompt: Prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a website generator. Respond ONLY with valid HTML and inline CSS. No explanations."
                },
                {
                    "role": "user",
                    "content": prompt.prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        html = response.choices[0].message.content.strip()
        return {"html": html}

    except Exception as e:
        return {"error": str(e)}
