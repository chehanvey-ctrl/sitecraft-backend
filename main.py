from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import openai

# Set OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Generate image using DALL·E 3
async def generate_image(prompt: str) -> str:
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print("Image generation error:", e)
        return "https://via.placeholder.com/512x512.png?text=Image+Unavailable"

# Generate site HTML with injected images
@app.post("/generate")
async def generate_site(request: PromptRequest):
    user_prompt = request.prompt

    system_prompt = (
        "You are a website generator AI. Generate a full HTML page styled with responsive CSS "
        "based on the user's description. Also list 2–3 image prompts that DALL-E should generate. "
        "Return ONLY valid JSON in this format: "
        "{'html': '<!DOCTYPE html>...', 'image_prompts': ['image of...', 'graphic of...']}"
    )

    try:
        completion = openai.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format="json"
        )

        content = completion.choices[0].message.content
        response_json = eval(content) if isinstance(content, str) else content

        html_code = response_json["html"]
        image_prompts = response_json.get("image_prompts", [])

        for i, image_prompt in enumerate(image_prompts):
            image_url = await generate_image(image_prompt)
            placeholder = f"{{{{image{i+1}}}}}"
            html_code = html_code.replace(placeholder, image_url)

        return {"html": html_code}

    except Exception as e:
        print("Error in generation:", e)
        return {"html": None, "error": str(e)}
