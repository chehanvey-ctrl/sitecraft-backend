from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# CORS: Allow only your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

# Input schema
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        print("🟢 Prompt received:", request.prompt)

        response = openai.chat.completions.create(
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
                    "content": request.prompt
                }
            ]
        )

        site_code = response.choices[0].message.content
        return {"html": site_code}

    except Exception as e:
        print("🔥 ERROR in /generate:", e)
        return {"error": str(e)}
