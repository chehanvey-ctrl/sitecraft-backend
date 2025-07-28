from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Prompt(BaseModel):
    text: str

@app.post("/generate")  # ✅ THIS IS NOW /generate again
async def generate_website(prompt: Prompt):
    try:
        # Inject AI Image section just under the hero
        full_prompt = (
            f"{prompt.text.strip()}\n\n"
            "Add a full-width section directly under the hero and above the About section, "
            "dedicated to showcasing an AI-generated image. This section should have a centered image "
            "with a caption that says 'Crafted by AI'. Use a modern style and include a comment marker in the HTML for easy identification."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes HTML/CSS code for stylish websites."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7
        )

        html_code = response['choices'][0]['message']['content'].strip()
        return {"code": html_code}

    except Exception as e:
        return {"error": f"Generation failed: {str(e)}"}
