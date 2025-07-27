from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from openai import OpenAI

# Initialize FastAPI app
app = FastAPI()

# Allow requests from your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request body
class PromptRequest(BaseModel):
    prompt: str

# Setup OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Generate HTML endpoint
@app.post("/generate")
async def generate(request: PromptRequest):
    system_msg = (
        "You are a helpful assistant that generates clean, production-ready HTML websites "
        "based on user prompts. Return only HTML. Do not include explanations."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": request.prompt}
        ]
    )

    html_code = response.choices[0].message.content
    return JSONResponse(content={"html": html_code})
