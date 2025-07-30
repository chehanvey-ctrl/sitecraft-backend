from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing – restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(request: PromptRequest):
    try:
        user_prompt = request.prompt

        full_prompt = f"""
You are a skilled web designer. Create a modern, clean, responsive HTML5 website layout based on the following idea: {user_prompt}.

Requirements:
- Wrap the layout in proper <html>, <head>, and <body> tags.
- Use modern CSS inline or <style> block inside <head>.
- Ensure mobile responsiveness.
- Add a header with the site name.
- Add a hero section with headline and subheadline.
- Immediately below the hero section, insert a clearly marked placeholder image section for an AI-generated image (e.g. via DALL·E). Style this section to stand out and include alt text like "AI-generated visual representation".
- Continue with at least 1–2 content sections based on the user's prompt.
- Add a clean footer.
- Do NOT include any JavaScript.

Return only valid, clean HTML as a string.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates HTML websites."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1800,
            temperature=0.7,
        )

        html_output = response.choices[0].message["content"]
        return {"html": html_output}

    except Exception as e:
        return {"error": str(e)}
