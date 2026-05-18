import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment
ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)

# NEW TOKEN PROVIDED BY USER
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
RESULTS_FILE = "/workspace/competitor_ads_60.json"

def scrape_competitor(competitor_name, limit=10):
    client = ApifyClient(APIFY_TOKEN)
    
    search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q={competitor_name.replace(' ', '%20')}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&search_type=keyword_unordered&media_type=all"
    
    run_input = {
        "startUrls": [{"url": search_url}],
        "maxAds": limit,
        "activeStatus": "active",
        "country": "IN"
    }

    print(f"🚀 Scraping 10 ads for: {competitor_name}")
    try:
        # Using the official Meta Ads Scraper ID
        run = client.actor("JJghSZmShuco4j9gJ").call(run_input=run_input)
        items = client.dataset(run['defaultDatasetId']).list_items().items
        return items
    except Exception as e:
        print(f"❌ Error for {competitor_name}: {e}")
        return []

def main():
    competitors = [
        "CampusDegree", 
        "College Vidya", 
        "apna advantage", 
        "Hike Education", 
        "LPU Online", 
        "Chandigarh University Online"
    ]
    
    all_data = {}
    for comp in competitors:
        ads = scrape_competitor(comp)
        all_data[comp] = ads
        # Save incrementally
        with open(RESULTS_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
            
    print(f"🏁 Finished. Data saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
