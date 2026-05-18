import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/workspace/.env')

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")

url = "https://gate.whapi.cloud/messages/interactive"

payload = {
    "to": WHATSAPP_GROUP,
    "type": "button",
    "body": {
        "text": "📝 *Action Item*\n\nPlease review the Whapi integration for sending interactive messages and buttons."
    },
    "action": {
        "buttons": [
            {
                "type": "quick_reply",
                "title": "✅ Mark Done",
                "id": "mark_done_001"
            },
            {
                "type": "quick_reply",
                "title": "⏳ Snooze",
                "id": "snooze_001"
            }
        ]
    }
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {WHAPI_TOKEN}"
}

response = requests.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.text)
