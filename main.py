from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

# API key check
api_key = os.getenv("OPENAI_API_KEY")
print("🔑 API KEY starts with:", api_key[:5] if api_key else "MISSING ❌")
openai.api_key = api_key

app = FastAPI()

# Allow all origins (dev only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_website(prompt_request: PromptRequest):
    try:
        print("🟡 Prompt received:", prompt_request.prompt)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that ONLY returns modern HTML code. Never say anything else. Never explain. Just return full HTML starting with <html> and ending with </html>."
            },
            {
                "role": "user",
                "content": prompt_request.prompt
            }
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        print("🟢 GPT-4o responded")

        content = response.choices[0].message["content"]
        print("🧾 GPT Content:", content[:200])  # print only first part

        if "<html" not in content:
            print("❌ No <html> tag found in response.")
            return {"error": "OpenAI did not return valid HTML."}

        return {"html": content}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": f"Exception: {str(e)}"}
