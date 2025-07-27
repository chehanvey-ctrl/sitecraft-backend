from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

# Load environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domain for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class PromptRequest(BaseModel):
    prompt: str

# GPT client
client = OpenAI(api_key=OPENAI_API_KEY)

# Route
@app.post("/generate")
async def generate_website(req: PromptRequest):
    prompt = req.prompt.strip()

    system_prompt = """
You are a professional web designer AI. Based on a user's idea or request, you must return a full HTML5 + CSS website layout styled for modern mobile + desktop viewing.

Requirements:
- Embed royalty-free, AI-generated image placeholders using <img src="https://via.placeholder.com/600x300?text=Image+Placeholder"> as needed.
- Layout must be clean: no overlapping elements, use proper spacing, mobile responsiveness, font hierarchy.
- Wrap content inside <main>, <header>, <section>, <footer> appropriately.
- Always use inline CSS (inside <style> tag in <head>).
- Ensure all <img> tags have alt text matching the description.
- Start with <!DOCTYPE html> and provide complete HTML output only.
"""

    user_prompt = f"""
Create a full website based on this user request:

\"\"\"{prompt}\"\"\"

Output only valid HTML/CSS.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000,
        )

        html_output = response.choices[0].message.content.strip()

        if "<html" not in html_output.lower():
            return {"error": "No HTML returned."}

        return {"html": html_output}

    except Exception as e:
        return {"error": str(e)}
