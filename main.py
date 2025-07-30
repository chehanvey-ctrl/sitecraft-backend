from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = "your-api-key-here"  # Replace with your actual key

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(prompt_request: PromptRequest):
    try:
        prompt = prompt_request.prompt.strip()

        full_prompt = (
            f"{prompt}\n\n"
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

        html_code = response.choices[0].message.content.strip()

        # Make sure we return a valid JSON object with a "code" key
        return { "code": html_code }

    except Exception as e:
        return { "error": f"Error generating site: {str(e)}" }
