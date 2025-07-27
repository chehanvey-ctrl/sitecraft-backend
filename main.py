from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for your frontend if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prompt model
class PromptRequest(BaseModel):
    prompt: str

SYSTEM_PROMPT = """
You are a professional web developer. When given a request, return a complete, clean, working website in HTML only.

Only return the HTML code, with:
- <html>, <head>, <body>
- Full internal CSS styling using <style> tags
- External image URLs from Unsplash, Pexels, or Pixabay
Do not include Markdown, explanations, or text outside HTML.
"""

@app.post("/generate")
async def generate_website(request: PromptRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        full_content = response.choices[0].message.content.strip()

        print("\n[DEBUG] GPT Response:\n", full_content[:1000])  # print only first 1000 chars

        if "<html" in full_content:
            return {"html": full_content}
        else:
            return {
                "html": "",
                "debug": full_content,
                "error": "Model did not return valid HTML."
            }

    except Exception as e:
        print(f"[ERROR]: {e}")
        return {"error": str(e)}
