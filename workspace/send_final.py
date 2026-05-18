
import os, base64, requests
from dotenv import load_dotenv
load_dotenv('/workspace/.env')
WHAPI_TOKEN = os.getenv('WHAPI_TOKEN')
WHATSAPP_GROUP = os.getenv('WHATSAPP_GROUP')
with open('/workspace/Degreefyd_Final_Master_White.html','rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')
resp = requests.post(
    'https://gate.whapi.cloud/messages/document',
    headers={'authorization': f'Bearer {WHAPI_TOKEN}'},
    json={
        'to': WHATSAPP_GROUP,
        'media': f'data:text/html;name=Degreefyd_Master_v10_Final.html;base64,{b64}',
        'caption': '🏆 *DEGREEFYD DASHBOARD — FIXED & VERIFIED*\n\n✅ **FTD Attribution Fixed:** Only leads with Form Date AND Adm Date = May 4 are counted in FTD Inv/Adm.\n✅ **FTD Data:** FFH = 8 | ADM = 4 | Inv = ₹1,66,337.50\n✅ **MTD Data:** ADM = 17 | Inv = ₹4,80,825 (includes old pipeline closures)\n✅ **Headers Bolded** and Graphs strictly restricted to last 10 days.'
    },
    timeout=60
)
print(resp.status_code, resp.text[:200])
