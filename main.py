@app.post("/generate")
async def generate_website(request: PromptRequest):
    try:
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

        if not html_code:
            return {"error": "Empty HTML returned by OpenAI."}

        return {"code": html_code}

    except Exception as e:
        return {"error": f"Generation failed: {str(e)}"}
