import os
import base64
import requests

def send_whatsapp_document(token, group_id, file_path, caption=""):
    if not os.path.exists(file_path):
        return False, "File not found"
        
    with open(file_path, "rb") as f:
        b64_content = base64.b64encode(f.read()).decode('utf-8')
    
    file_name = os.path.basename(file_path)
    # text/html is standard for HTML files
    media_payload = f"data:text/html;name={file_name};base64,{b64_content}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json"
    }

    payload = {
        "to": group_id,
        "media": media_payload,
        "caption": caption
    }

    # Use the document endpoint for HTML files
    resp = requests.post("https://gate.whapi.cloud/messages/document", headers=headers, json=payload)
    return resp.status_code in [200, 201], resp.text

def main():
    # Get token from .env
    token = ""
    with open("/workspace/.env", "r") as f:
        for line in f:
            if line.startswith("WHAPI_TOKEN="):
                token = line.split("=")[1].strip()
                break
                
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]
    
    if not token:
        print("WHAPI_TOKEN not found in /workspace/.env")
        return

    group_id = "120363426619711887@g.us"
    file_path = "/workspace/almost_final_report.html"
    
    print(f"Sending {file_path} to {group_id}...")
    success, result = send_whatsapp_document(
        token, 
        group_id, 
        file_path, 
        caption="📊 Degreefyd Master Report (Fixed Top/Left Sticky Columns & Graphs)"
    )
    if success:
        print("Success!")
    else:
        print(f"Failed: {result}")

if __name__ == "__main__":
    main()
