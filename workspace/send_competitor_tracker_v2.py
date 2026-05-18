import os
import base64
import requests
from dotenv import load_dotenv

# Load environment
ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")
FILE_PATH = "/workspace/Competitor_Ads_Tracker_v2.xlsx"

def main():
    if not WHAPI_TOKEN or not WHATSAPP_GROUP:
        return
        
    if not os.path.exists(FILE_PATH):
        return
        
    with open(FILE_PATH, "rb") as f:
        file_content = f.read()
        
    b64_content = base64.b64encode(file_content).decode('utf-8')
    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    media_payload = f"data:{mime_type};name=Competitor_Ads_Tracker_PRO.xlsx;base64,{b64_content}"
    
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}",
        "content-type": "application/json"
    }
    
    payload = {
        "to": WHATSAPP_GROUP,
        "media": media_payload,
        "caption": "🔥 *Competitor Ads Tracker PRO (V2)*\n\nI fixed the data mapping. This version now correctly includes:\n✅ *Correct Ad Text*\n✅ *Direct Media URLs* (Photos/Videos)\n✅ *Days Active* (Winner identification)\n✅ *AI Creative Prompts* based on actual ad content."
    }
    
    requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)

if __name__ == "__main__":
    main()
