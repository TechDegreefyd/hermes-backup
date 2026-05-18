import os
import base64
import requests
import time
from dotenv import load_dotenv

ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

file_path = "/workspace/Degreefyd_Final_Report.html"

with open(file_path, "rb") as f:
    b64_content = base64.b64encode(f.read()).decode('utf-8')

media_payload = f"data:text/html;name=Degreefyd_Final_Report.html;base64,{b64_content}"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}",
    "content-type": "application/json"
}

payload = {
    "to": WHATSAPP_GROUP,
    "media": media_payload,
    "caption": "📊 Degreefyd Final Dashboard (Static Images)\n\n✅ 100% WhatsApp Compliant\n✅ Exact graphs as requested (CPL Panel vs LMS, Leads Panel vs LMS, Brand, Meta, DSA)\n✅ Opens perfectly inside WhatsApp Mobile (no JS required)."
}

for _ in range(3):
    try:
        resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload, timeout=10)
        print("Sent:", resp.status_code == 200, resp.text)
        break
    except Exception as e:
        print("Failed, retrying...", e)
        time.sleep(2)
