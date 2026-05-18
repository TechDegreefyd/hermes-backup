import os
import json
import base64
import requests
import pandas as pd
from PIL import Image
import io
import time

def generate_gemini_image(prompt, output_path, model="gemini-3.1-flash-image-preview"):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try reading from .hermes/.env
        try:
            with open(os.path.expanduser("~/.hermes/.env"), "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=")[1].strip()
                        break
        except:
            pass
    
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract Base64 data from response
        # The skill says it's in inlineData/data
        # Note: Actual structure might vary, checking common patterns
        try:
            image_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        except (KeyError, IndexError):
            print(f"Error: Unexpected response structure for prompt: {prompt[:50]}...")
            print(json.dumps(data, indent=2))
            return False
            
        image_bytes = base64.b64decode(image_b64)
        
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return True
    except Exception as e:
        print(f"Error generating image: {e}")
        return False

def overlay_logo(image_path, logo_path, output_path):
    try:
        base_img = Image.open(image_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")
        
        # Resize logo to be 15% of the base image width
        base_w, base_h = base_img.size
        logo_w, logo_h = logo.size
        
        new_logo_w = int(base_w * 0.15)
        new_logo_h = int(logo_h * (new_logo_w / logo_w))
        logo = logo.resize((new_logo_w, new_logo_h), Image.LANCZOS)
        
        # Position: bottom right with padding
        padding = 20
        position = (base_w - new_logo_w - padding, base_h - new_logo_h - padding)
        
        # Create a new transparent layer for the logo
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        overlay.paste(logo, position)
        
        # Combine
        combined = Image.alpha_composite(base_img, overlay)
        combined.convert("RGB").save(output_path, "JPEG")
        return True
    except Exception as e:
        print(f"Error overlaying logo: {e}")
        return False

def main():
    excel_path = "/workspace/Final_Ads_Analysis_60.xlsx"
    logo_path = "/workspace/New_logo_Degrefyd.png"
    output_dir = "/workspace/generated_ads"
    
    df = pd.read_excel(excel_path)
    prompts = df['Ad Creative Prompt'].dropna().unique().tolist()
    
    # Limit to 15 images
    prompts = prompts[:15]
    
    for i, raw_prompt in enumerate(prompts):
        print(f"Processing image {i+1}/15...")
        
        # Clean prompt: AI models work better with descriptive but focused prompts
        # The raw prompt includes "DegreeFYD professional ad visual. Style: Premium blue/white theme. Content: ... Visual: ..."
        # I'll keep it as is since it's already structured for the model.
        
        temp_img = os.path.join(output_dir, f"temp_{i}.png")
        final_img = os.path.join(output_dir, f"ad_{i+1}.jpg")
        
        success = generate_gemini_image(raw_prompt, temp_img)
        if success:
            overlay_logo(temp_img, logo_path, final_img)
            os.remove(temp_img)
            print(f"Saved: {final_img}")
        else:
            print(f"Failed to generate image for prompt {i+1}")
        
        # Small delay to avoid rate limits
        time.sleep(1)

if __name__ == "__main__":
    main()
