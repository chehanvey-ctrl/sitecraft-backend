from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# ✅ TEMP: Allow all origins (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change back to specific domain once verified
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


class PromptRequest(BaseModel):
    prompt: str


@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a web developer that creates beautiful websites from simple prompts. Return the result as clean HTML+CSS layout with clear sections, consistent formatting, and visually appealing content. Only return raw code, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    site_code = response["choices"][0]["message"]["content"]
    return {"site_code": site_code}  # ✅ Keep this for now – Fix #2 will change this
