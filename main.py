from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Initialize the app
app = FastAPI()

# ✅ CORS: Temporarily allow all origins for testing (you can lock this later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or replace with your frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Define the request body model
class PromptRequest(BaseModel):
    prompt: str

# ✅ Define the endpoint to generate website code
@app.post("/generate")
async def generate_site(request: PromptRequest):
    try:
        prompt = request.prompt

        # Call OpenAI to generate HTML+CSS from prompt
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior front-end developer. "
                        "Generate a stunning, mobile-friendly, modern HTML+CSS website layout based on the user's prompt. "
                        "Include clear sectioning, good visual hierarchy, and beautiful typography. "
                        "Return only valid raw HTML+CSS – no explanation or markdown formatting."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract and return just the generated HTML code
        site_code = response["choices"][0]["message"]["content"]
        return {"html": site_code}

    except Exception as e:
        # Return an error message if something goes wrong
        return {"error": str(e)}
