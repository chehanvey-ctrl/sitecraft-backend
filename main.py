from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# Allow only your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request schema
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt.strip()

    if not prompt:
        return {"html": "<p>Error: Prompt was empty.</p>"}

    try:
        # Ask GPT to build a beautiful HTML site
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert web developer. Create a stunning, modern, responsive website based on the user's prompt. "
                        "Return valid HTML5 with inline CSS using <style> tags. Structure the site with header, hero, AI image section, content sections, and footer. "
                        "Add smooth transitions, clean design, and include a section just below the hero with a <div> clearly marked for AI-generated image content. "
                        "Do not include explanations — only return the raw complete HTML file."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        html_code = response["choices"][0]["message"]["content"].strip()

        # Ensure we actually got some HTML back
        if not html_code or "<html" not in html_code.lower():
            return {"html": "<p>Error: No valid HTML returned by GPT.</p>"}

        return {"html": html_code}

    except Exception as e:
        return {"html": f"<p>Internal server error: {str(e)}</p>"}
