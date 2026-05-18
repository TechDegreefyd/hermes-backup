import os
import json
import base64
import requests
import sys

def generate_image(prompt, output_path):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try reading from .env if not in env
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=")[1].strip()
                        break
    
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error: API call failed with status {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    try:
        image_data_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        image_bytes = base64.b64decode(image_data_b64)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return True
    except (KeyError, IndexError) as e:
        print(f"Error: Failed to parse image data from response. {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_gemini_image.py '<prompt>' <output_path>")
    else:
        prompt = sys.argv[1]
        output_path = sys.argv[2]
        if generate_image(prompt, output_path):
            print(f"Image saved to {output_path}")
        else:
            sys.exit(1)
