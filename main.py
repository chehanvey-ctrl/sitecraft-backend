from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # ← Add this
from pydantic import BaseModel
import uvicorn
import os
from openai import OpenAI

# Pydantic model for request body
class PromptRequest(BaseModel):
    prompt: str

# Initialize FastAPI app
app = FastAPI()

# Allow frontend domain for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],  # Update to match your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate")
async def generate(request: PromptRequest):
    # Extract prompt
    prompt = request.prompt

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    html_code = response.choices[0].message.content
    return JSONResponse(content={"html": html_code})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
