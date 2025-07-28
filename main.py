from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(req: PromptRequest):
    user_prompt = req.prompt
    print(f"🛠️ Prompt received: {user_prompt}")

    try:
        system_prompt = (
            "You are a professional web designer and developer. Generate a complete, modern, beautiful HTML5 one-page personal website "
            "based on the user's prompt. Include appropriate sections like Hero, About, Portfolio, Contact, etc., with clean semantic HTML and inline CSS. "
            "Use modern UI patterns such as cards, gradients, bold typography, responsive layouts, and add subtle animations where relevant. "
            "The design should look sleek and premium, like a site built with Webflow or Framer."
        )

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        html_code = response.choices[0].message.content
        print("✅ HTML code successfully generated.")
        return {"html": html_code}

    except Exception as e:
        print(f"❌ Error during site generation: {e}")
        return {"error": str(e)}
