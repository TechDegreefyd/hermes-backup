import os
import base64
import requests
import time

def send_whatsapp_image(token, group_id, file_path, caption=""):
    with open(file_path, "rb") as f:
        b64_content = base64.b64encode(f.read()).decode('utf-8')
    file_name = os.path.basename(file_path)
    media_payload = f"data:image/jpeg;name={file_name};base64,{b64_content}"
    headers = {"authorization": f"Bearer {token}", "content-type": "application/json"}
    payload = {"to": group_id, "media": media_payload, "caption": caption}
    resp = requests.post("https://gate.whapi.cloud/messages/image", headers=headers, json=payload)
    return resp.status_code in [200, 201], resp.text

# Get token
token = ""
with open("/workspace/.env", "r") as f:
    for line in f:
        if line.startswith("WHAPI_TOKEN="):
            token = line.split("=")[1].strip()
            break

group_id = "120363426619711887@g.us"
for img in ["ad_8.jpg", "ad_9.jpg"]:
    path = f"/workspace/generated_ads/{img}"
    print(f"Sending {img}...")
    success, res = send_whatsapp_image(token, group_id, path, caption=f"Generated Ad Creative: {img}")
    print("Success" if success else f"Failed: {res}")
    time.sleep(2)
