import os
import base64
import requests
from dotenv import load_dotenv

# Load environment
ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")
FILE_PATH = "/workspace/Competitor_Ads_Tracker.xlsx"

def main():
    if not WHAPI_TOKEN or not WHATSAPP_GROUP:
        print(f"Missing WHAPI credentials. Checked {ENV_PATH}")
        return
        
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return
        
    with open(FILE_PATH, "rb") as f:
        file_content = f.read()
        
    b64_content = base64.b64encode(file_content).decode('utf-8')
    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    media_payload = f"data:{mime_type};name=Competitor_Ads_Tracker.xlsx;base64,{b64_content}"
    
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}",
        "content-type": "application/json"
    }
    
    payload = {
        "to": WHATSAPP_GROUP,
        "media": media_payload,
        "caption": "📊 *Competitor Ads Tracker (Excel)*\n\nHere is the detailed scraping report for CampusDegree and College Vidya (1,050 ads processed)."
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
