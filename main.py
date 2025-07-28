from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS: Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Match the frontend key: 'prompt'
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(request: PromptRequest):
    try:
        # Inject AI image section between hero and first section
        full_prompt = (
            f"{request.prompt.strip()}\n\n"
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
