import os
import base64
import requests
from dotenv import load_dotenv

BASE_DIR = os.environ.get('WORKSPACE_DIR', '/workspace')
load_dotenv(os.path.join(BASE_DIR, '.env'))

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

excel_path = os.path.join(BASE_DIR, "Daily_Online_LMS_Reports_V2.xlsx")

print(f"Preparing to send {excel_path} via WHAPI...")
with open(excel_path, "rb") as f:
    b64_content = base64.b64encode(f.read()).decode('utf-8')
    
mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
media_payload = f"data:{mime_type};name=Daily_Online_LMS_Reports.xlsx;base64,{b64_content}"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}",
    "content-type": "application/json"
}

payload = {
    "to": WHATSAPP_GROUP,
    "media": media_payload,
    "caption": "📊 *Daily Online LMS Reports*\n\nHere are the latest targets vs fee collected, FTD metrics, and achieved/target ratios for today."
}

resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
print("Status:", resp.status_code)
try:
    print("Response:", resp.json())
except:
    print("Response:", resp.text)
