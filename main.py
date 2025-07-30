from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI, OpenAIError
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your OpenAI key safely
openai_api_key = os.getenv("OPENAI_API_KEY")  # Must be set in Render dashboard

client = OpenAI(api_key=openai_api_key)

# Define the expected structure of the request
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        if not request.prompt.strip():
            return {"html": "<p>Error: Prompt cannot be empty.</p>"}

        full_prompt = f"""Generate a full modern, clean HTML5 website based on this prompt:
        
        {request.prompt}

        Ensure it includes styling and looks visually professional.
        Only return valid HTML, no explanations or markdown."""
        
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional web designer."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        html_response = completion.choices[0].message.content.strip()

        if not html_response.startswith("<!DOCTYPE html"):
            html_response = f"<!DOCTYPE html><html><body><pre>{html_response}</pre></body></html>"

        return {"html": html_response}

    except OpenAIError as e:
        return {"html": f"<p>OpenAI error: {str(e)}</p>"}
    except Exception as e:
        return {"html": f"<p>Server error: {str(e)}</p>"}
