import os
import json
import base64
import requests
import sys

def generate_image(prompt, output_path):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=")[1].strip()
                        break
    if not api_key:
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        return False
    data = response.json()
    try:
        image_data_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        image_bytes = base64.b64decode(image_data_b64)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return True
    except:
        return False

logo_desc = "Logo inclusion: A navy blue icon of a person with a graduation cap reaching for an orange star with an orange swoosh. Text 'DegreeFYD' in navy blue bold font."

ads = [
    {"comp": "CampusDegree", "head": "Find the Best Online Degree for Your Profile.", "sub": "Simplify your search for the perfect online university with CampusDegree."},
    {"comp": "CampusDegree", "head": "Admissions Made Simple & Fast.", "sub": "Apply to top-tier universities directly through our verified portal."},
    {"comp": "College Vidya", "head": "Stop Guessing. Start Comparing.", "sub": "Compare 100+ UGC-DEB approved universities in just 2 minutes."},
    {"comp": "College Vidya", "head": "Verified Degrees, Transparent Decisions.", "sub": "Get expert counseling and find the right online MBA/MCA today."},
    {"comp": "LPU Online", "head": "World-Class Degree, At Your Own Pace.", "sub": "Flexible online learning. UGC-DEB approved and NAAC A++ accredited."},
    {"comp": "LPU Online", "head": "Online Degree with 100% Placement Support.", "sub": "Don't just study; get hired. Access our massive recruitment network."},
    {"comp": "CU Online", "head": "NAAC A+ Degree to Power Your Career.", "sub": "Experience world-class online education from Chandigarh University."},
    {"comp": "CU Online", "head": "Industry-Integrated Online MCA/MBA.", "sub": "Learn skills that employers want with our advanced LMS."},
    {"comp": "Hike Education", "head": "Hike Your Career with Top University Degrees.", "sub": "Personalized mentorship and expert guidance for working professionals."},
    {"comp": "Hike Education", "head": "Your Bridge to Top-Tier Universities.", "sub": "Premium degrees from NMIMS, Manipal, and more via Hike Education."},
    {"comp": "apna advantage", "head": "Get the 'apna' Advantage in Your Career.", "sub": "Smart online degrees for the modern Indian professional."},
    {"comp": "apna advantage", "head": "Balance Work, Life, and Study.", "sub": "Flexible programs designed for busy professionals. Study while you earn."}
]

for i, ad in enumerate(ads):
    filename = f"/workspace/final_ad_{i+1:02d}.jpg"
    if os.path.exists(filename):
        print(f"Skipping {filename} (already exists)")
        continue
    prompt = f"Professional Facebook ad visual for {ad['comp']}. Background: Successful Indian student or professional in a modern setting. Premium blue and white theme. Big Headline: '{ad['head']}'. Subtext: '{ad['sub']}'. {logo_desc}"
    print(f"Generating {filename}...")
    if generate_image(prompt, filename):
        print(f"Success: {filename}")
    else:
        print(f"Failed: {filename}")
