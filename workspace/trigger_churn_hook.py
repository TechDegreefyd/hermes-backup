import os
import requests
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHAPI_URL = "https://gate.whapi.cloud/messages/interactive"

def trigger_hook(target_phone):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}"
    }
    
    hook_text = (
        "🌟 *Success Story*\n\n"
        "Mohit Kapoor recently secured a top internship at *Degreefyd* with a profile just like yours! 🚀\n\n"
        "To help us find your fit, what is your *Area of Interest*?\n\n"
        "1️⃣ Tech / IT\n"
        "2️⃣ Mgmt / MBA\n"
        "3️⃣ Others"
    )
    
    payload = {
        "to": target_phone,
        "type": "button",
        "body": {"text": hook_text},
        "action": {
            "buttons": [
                {"type": "quick_reply", "title": "Tech", "id": "int_tech"},
                {"type": "quick_reply", "title": "Management", "id": "int_mgmt"},
                {"type": "quick_reply", "title": "Others", "id": "int_other"}
            ]
        }
    }
    
    response = requests.post(WHAPI_URL, json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    # You can change this to your personal number for testing
    test_number = "120363426619711887@g.us" 
    print(f"Triggering Hook to {test_number}...")
    res = trigger_hook(test_number)
    print(res)
