import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load env for WHAPI
load_dotenv("/workspace/.env")

def create_competitor_excel(json_data_path, output_path):
    """
    json_data_path: Path to Apify results JSON
    output_path: Path to save the Excel file
    """
    if not os.path.exists(json_data_path):
        print(f"File {json_data_path} not found.")
        return

    with open(json_data_path, 'r') as f:
        raw_data = json.load(f)

    rows = []
    # raw_data structure depends on how apify_scraper.py saves it.
    # Assuming: { "CompetitorName": [ {ad_obj}, ... ] }
    for competitor, ads in raw_data.items():
        for ad in ads:
            rows.append({
                "Competitor": competitor,
                "Ad ID": ad.get("adId") or ad.get("id"),
                "Status": ad.get("status", "ACTIVE"),
                "Creation Date": ad.get("adCreationTime"),
                "Original Text": ad.get("adTitle") or ad.get("body", {}).get("text", ""),
                "Image URL": ad.get("adSnapshotUrl") or ad.get("images", [{}])[0].get("url", ""),
                "Platforms": ", ".join(ad.get("publisherPlatforms", [])),
                "Total Ads Count": ad.get("totalAdsCount", "N/A")
            })

    df = pd.DataFrame(rows)
    
    # Placeholder for the Gemini/AI generated prompt/photo logic
    df["AI Generation Prompt"] = df["Original Text"].apply(lambda x: f"Professional education ad in minimalist style: {x[:100]}..." if x else "")
    
    df.to_excel(output_path, index=False)
    print(f"Excel file created at {output_path}")

if __name__ == "__main__":
    # Example paths
    INPUT = "/workspace/apify_results.json"
    OUTPUT = f"/workspace/Competitor_Tracker_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    # Note: This requires apify_results.json to exist first.
    if os.path.exists(INPUT):
        create_competitor_excel(INPUT, OUTPUT)
    else:
        print("Waiting for Apify results to generate Excel...")
