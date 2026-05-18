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
        try:
            with open(os.path.expanduser("~/.hermes/.env"), "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=")[1].strip()
                        break
        except:
            pass
    
    if not api_key:
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Search all parts for inlineData
        image_b64 = None
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                image_b64 = part["inlineData"]["data"]
                break
        
        if not image_b64:
            print(f"No image found in response for prompt: {prompt[:30]}")
            return False
            
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def overlay_logo(image_path, logo_path, output_path):
    try:
        base_img = Image.open(image_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")
        base_w, base_h = base_img.size
        logo_w, logo_h = logo.size
        new_logo_w = int(base_w * 0.15)
        new_logo_h = int(logo_h * (new_logo_w / logo_w))
        logo = logo.resize((new_logo_w, new_logo_h), Image.LANCZOS)
        padding = 20
        position = (base_w - new_logo_w - padding, base_h - new_logo_h - padding)
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        overlay.paste(logo, position)
        combined = Image.alpha_composite(base_img, overlay)
        combined.convert("RGB").save(output_path, "JPEG")
        return True
    except:
        return False

def main():
    excel_path = "/workspace/Final_Ads_Analysis_60.xlsx"
    logo_path = "/workspace/New_logo_Degrefyd.png"
    output_dir = "/workspace/generated_ads"
    
    df = pd.read_excel(excel_path)
    prompts = df['Ad Creative Prompt'].dropna().unique().tolist()
    
    missing_indices = [3, 10, 11, 13]
    
    for i in missing_indices:
        if i >= len(prompts): continue
        raw_prompt = prompts[i]
        print(f"Fixing image {i+1}...")
        temp_img = os.path.join(output_dir, f"temp_{i}.png")
        final_img = os.path.join(output_dir, f"ad_{i+1}.jpg")
        if generate_gemini_image(raw_prompt, temp_img):
            overlay_logo(temp_img, logo_path, final_img)
            if os.path.exists(temp_img): os.remove(temp_img)
            print(f"Saved: {final_img}")
        time.sleep(2)

if __name__ == "__main__":
    main()
