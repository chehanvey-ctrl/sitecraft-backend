from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(request: PromptRequest):
    prompt = request.prompt.strip()
    print("🟡 Prompt received:", prompt)

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a web developer. Generate a beautiful, modern, responsive HTML5 website with Tailwind CSS. "
                        "Do NOT explain anything—only return full HTML code. Add an <img> section directly under the hero "
                        "with a placeholder for AI-generated images. Do not include stock images or external URLs."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1800,
        )

        content = response.choices[0].message.content
        print("🧾 GPT Content:", content[:200], "..." if len(content) > 200 else "")

        if "<html" not in content:
            print("❌ No <html> tag found in response.")
            return {"error": "OpenAI did not return valid HTML."}

        return {"html": content}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": str(e)}
