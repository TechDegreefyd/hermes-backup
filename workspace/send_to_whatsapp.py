import os
import base64
import requests
import glob
import time

def send_whatsapp_image(token, group_id, file_path, caption=""):
    if not os.path.exists(file_path):
        return False, "File not found"
        
    with open(file_path, "rb") as f:
        b64_content = base64.b64encode(f.read()).decode('utf-8')
    
    file_name = os.path.basename(file_path)
    # Using the media payload format for WHAPI
    media_payload = f"data:image/jpeg;name={file_name};base64,{b64_content}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json"
    }

    payload = {
        "to": group_id,
        "media": media_payload,
        "caption": caption
    }

    # Use the image endpoint for images
    resp = requests.post("https://gate.whapi.cloud/messages/image", headers=headers, json=payload)
    return resp.status_code in [200, 201], resp.text

def main():
    # Get token from .env
    token = ""
    with open("/workspace/.env", "r") as f:
        for line in f:
            if line.startswith("WHAPI_TOKEN="):
                token = line.split("=")[1].strip()
                break
    
    if not token:
        print("WHAPI_TOKEN not found in /workspace/.env")
        return

    group_id = "120363426619711887@g.us"
    image_pattern = "/workspace/generated_ads/ad_*.jpg"
    image_files = sorted(glob.glob(image_pattern))
    
    print(f"Found {len(image_files)} images to send.")
    
    for i, file_path in enumerate(image_files):
        print(f"Sending image {i+1}/{len(image_files)}: {os.path.basename(file_path)}...")
        success, result = send_whatsapp_image(token, group_id, file_path, caption=f"Generated Ad Creative #{i+1} for DegreeFYD")
        if success:
            print("Success")
        else:
            print(f"Failed: {result}")
        
        # Rate limit safety
        time.sleep(2)

if __name__ == "__main__":
    main()
