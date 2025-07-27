from fastapi import FastAPI, Request from fastapi.middleware.cors import CORSMiddleware from pydantic import BaseModel from openai import OpenAI, OpenAIError import uvicorn

app = FastAPI()

✅ CORS Middleware

app.add_middleware( CORSMiddleware, allow_origins=[""], allow_credentials=True, allow_methods=[""], allow_headers=["*"], )

client = OpenAI()

class Prompt(BaseModel): prompt: str

@app.post("/generate") async def generate_site(prompt: Prompt): try: # 🧠 Step 1: Generate HTML structure completion = client.chat.completions.create( model="gpt-4o", messages=[ {"role": "system", "content": "You are an expert web designer who creates clean, modern, and beautiful HTML websites. Your HTML must include inline styles and be responsive. Use placeholder image tags like <img src='IMAGE_URL' alt='...'> that I will replace later."}, {"role": "user", "content": prompt.prompt} ] ) html_content = completion.choices[0].message.content.strip()

# 🎨 Step 2: Generate Image with DALL·E (optional, fallback supported)
    try:
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt.prompt,
            n=1,
            size="1024x1024"
        )
        image_url = image_response.data[0].url
        # Replace placeholder with image URL (first occurrence only)
        html_content = html_content.replace("IMAGE_URL", image_url, 1)
    except OpenAIError as e:
        print(f"Image generation failed: {e}")
        # Fallback to a default placeholder
        html_content = html_content.replace("IMAGE_URL", "https://via.placeholder.com/600x400", 1)

    return {"html": html_content}

except Exception as e:
    print(f"Error: {e}")
    return {"html": "", "error": str(e)}

if name == "main": uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

