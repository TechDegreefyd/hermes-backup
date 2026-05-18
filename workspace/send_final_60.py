import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv("/workspace/.env")

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHATSAPP_GROUP = os.getenv("WHATSAPP_GROUP")
FILE_PATH = "/workspace/Final_Ads_Analysis_60.xlsx"

def main():
    if not os.path.exists(FILE_PATH): return
    with open(FILE_PATH, "rb") as f:
        content = f.read()
    b64 = base64.b64encode(content).decode('utf-8')
    payload = {
        "to": WHATSAPP_GROUP,
        "media": f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;name=Final_Ads_Analysis_60.xlsx;base64,{b64}",
        "caption": "🎯 *Final 60-Ad Competitor Analysis*\n\n✅ Scraped all 6 competitors (CampusDegree, College Vidya, Apna, Hike, LPU, Chandigarh).\n✅ Extracted winning hooks and media URLs.\n✅ Generated high-quality AI Creative Prompts aligned with *DegreeFYD.com* style."
    }
    requests.post("https://gate.whapi.cloud/messages/document", 
                  headers={"Authorization": f"Bearer {WHAPI_TOKEN}", "Content-Type": "application/json"}, 
                  json=payload)

if __name__ == "__main__":
    main()
