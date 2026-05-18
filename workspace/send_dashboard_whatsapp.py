import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

file_path = "/workspace/daily_dashboard.html"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

print(f"Preparing to send {file_path} via WHAPI...")
with open(file_path, "rb") as f:
    b64_content = base64.b64encode(f.read()).decode('utf-8')
    
mime_type = "text/html"
media_payload = f"data:{mime_type};name=daily_dashboard.html;base64,{b64_content}"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}",
    "content-type": "application/json"
}

payload = {
    "to": WHATSAPP_GROUP,
    "media": media_payload,
    "caption": "✨ *DegreeFYD Daily Performance Dashboard*\n\nHere is the aesthetic summary for today (April 30, 2026). Open this file to see the visual report."
}

resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
print("Status:", resp.status_code)
try:
    print("Response:", resp.json())
except:
    print("Response:", resp.text)
