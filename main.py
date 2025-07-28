from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# CORS config (can temporarily use ["*"] for debugging)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("❌ OPENAI_API_KEY environment variable not set!")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        prompt = request.prompt
        if not prompt:
            return JSONResponse(status_code=400, content={"error": "Prompt is missing"})

        print(f"📥 Prompt received: {prompt}")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert web developer. Based on the user's prompt, create a beautiful, modern website. "
                        "Return clean HTML5 with embedded CSS in <style> tags. Use semantic sections like header, hero, about, features, contact. "
                        "Incorporate design elements, subtle animations, and responsive layout. Do not explain anything. Only return the complete code."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        site_code = response["choices"][0]["message"]["content"]
        return {"html": site_code}

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Internal Server Error: {str(e)}"})
