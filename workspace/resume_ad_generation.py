import os
import re
import json
import base64
import requests
import time

def generate_image(prompt, output_path, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return False
        data = response.json()
        image_data_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        image_bytes = base64.b64decode(image_data_b64)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def parse_ads(md_path):
    with open(md_path, "r") as f:
        content = f.read()
    
    sections = re.split(r'## \d+\.', content)[1:]
    comp_names = ["College Vidya", "LPU Online", "Chandigarh University Online", "Hike Education", "CampusDegree", "apna advantage"]
    
    all_ads = []
    for i, section in enumerate(sections):
        comp = comp_names[i]
        # Match "Headline: ...\n   Body: ..."
        headlines = re.findall(r'\*\*Headline:\*\* (.*?)\n', section)
        bodies = re.findall(r'\*\*Body:\*\* (.*?)\n', section)
        
        # Adjust for cases where Body might be the last line in a section
        if not bodies:
            bodies = re.findall(r'\*\*Body:\*\* (.*?)$', section, re.MULTILINE)

        for head, body in zip(headlines, bodies):
            all_ads.append({"comp": comp, "head": head.strip(), "sub": body.strip()})
    
    return all_ads

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found in environment.")
        return

    workspace = "/workspace/workspace"
    md_path = os.path.join(workspace, "competitor_ads_report.md")
    ads = parse_ads(md_path)
    
    logo_desc = "Logo inclusion: A navy blue icon of a person with a graduation cap reaching for an orange star with an orange swoosh. Text 'DegreeFYD' in navy blue bold font."
    
    print(f"Found {len(ads)} ads in report.")
    
    for i, ad in enumerate(ads):
        ad_num = i + 1
        output_path = os.path.join(workspace, f"final_ad_{ad_num:02d}.jpg")
        
        if os.path.exists(output_path):
            print(f"[{ad_num}/60] Skipping: {output_path} (exists)")
            continue
        
        prompt = f"Professional Facebook ad visual for {ad['comp']}. Background: Successful Indian student or professional in a modern setting. Premium blue and white theme. Big Headline: '{ad['head']}'. Subtext: '{ad['sub']}'. {logo_desc}"
        
        print(f"[{ad_num}/60] Generating for {ad['comp']}...")
        success = False
        for attempt in range(3):
            if generate_image(prompt, output_path, api_key):
                print(f"Success: {output_path}")
                success = True
                break
            else:
                print(f"Attempt {attempt+1} failed. Retrying in 5s...")
                time.sleep(5)
        
        if not success:
            print(f"Failed to generate {output_path} after 3 attempts.")
            # Stop to avoid burning credits/rate limits if something is fundamentally wrong
            break
        
        # Moderate sleep to avoid rate limiting
        time.sleep(2)

if __name__ == "__main__":
    main()
