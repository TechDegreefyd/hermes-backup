import os
import base64
import requests
from dotenv import load_dotenv

# Use absolute path for persistence
ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")
FILE_PATH = "/workspace/Facebook_Ads_In_Depth_Report_V2.pdf"

def main():
    if not WHAPI_TOKEN or not WHATSAPP_GROUP:
        print(f"Missing WHAPI credentials. Checked {ENV_PATH}")
        return
        
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return
        
    with open(FILE_PATH, "rb") as f:
        pdf_content = f.read()
        
    b64_content = base64.b64encode(pdf_content).decode('utf-8')
    mime_type = "application/pdf"
    media_payload = f"data:{mime_type};name=Facebook_Ads_In_Depth_Report_V2.pdf;base64,{b64_content}"
    
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}",
        "content-type": "application/json"
    }
    
    payload = {
        "to": WHATSAPP_GROUP,
        "media": media_payload,
        "caption": "📊 *Facebook Ads Report*\n\nAs requested, here is the latest Facebook Ads in-depth report."
    }
    
    print(f"Sending {FILE_PATH} to {WHATSAPP_GROUP}...")
    resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except:
        print("Response:", resp.text)

if __name__ == "__main__":
    main()
