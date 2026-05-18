import os
import re
import pandas as pd
import zipfile

def create_zip(zip_name, pattern):
    workspace = "/workspace/workspace"
    with zipfile.ZipFile(os.path.join(workspace, zip_name), 'w') as zipf:
        for i in range(1, 61):
            filename = f"final_ad_{i:02d}.jpg"
            file_path = os.path.join(workspace, filename)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=filename)

def parse_ads_to_excel(md_path, excel_path):
    with open(md_path, "r") as f:
        content = f.read()
    
    sections = re.split(r'## \d+\.', content)[1:]
    comp_names = ["College Vidya", "LPU Online", "Chandigarh University Online", "Hike Education", "CampusDegree", "apna advantage"]
    
    data = []
    ad_idx = 1
    for i, section in enumerate(sections):
        comp = comp_names[i]
        headlines = re.findall(r'\*\*Headline:\*\* (.*?)\n', section)
        bodies = re.findall(r'\*\*Body:\*\* (.*?)\n', section)
        
        if not bodies:
            bodies = re.findall(r'\*\*Body:\*\* (.*?)$', section, re.MULTILINE)

        for head, body in zip(headlines, bodies):
            data.append({
                "Ad ID": f"AD_{ad_idx:02d}",
                "Filename": f"final_ad_{ad_idx:02d}.jpg",
                "Competitor": comp,
                "Headline": head.strip(),
                "Primary Text (Body)": body.strip(),
                "Targeting": "Interest: Education, MBA, Online Learning",
                "Call to Action": "Apply Now"
            })
            ad_idx += 1
    
    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)

def main():
    workspace = "/workspace/workspace"
    md_path = os.path.join(workspace, "competitor_ads_report.md")
    excel_path = os.path.join(workspace, "DegreeFYD_Ad_Creative_Tracker.xlsx")
    zip_path = "DegreeFYD_60_Ads_Bundle.zip"
    
    print("Creating Excel Tracker...")
    parse_ads_to_excel(md_path, excel_path)
    print(f"Excel created: {excel_path}")
    
    print("Creating Zip Bundle...")
    create_zip(zip_path, "final_ad_*.jpg")
    print(f"Zip created: {os.path.join(workspace, zip_path)}")

if __name__ == "__main__":
    main()
