import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment
ENV_PATH = "/workspace/.env"
load_dotenv(ENV_PATH)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
RESULTS_FILE = "/workspace/apify_results.json"

def scrape_with_apify(competitor_name):
    client = ApifyClient(APIFY_TOKEN)
    
    # Constructing a Meta Ads Library URL for the search term
    # This fulfills the 'startUrls' requirement
    search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q={competitor_name.replace(' ', '%20')}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&search_type=keyword_unordered&media_type=all"
    
    run_input = {
        "startUrls": [{"url": search_url}],
        "maxAds": 10,
        "activeStatus": "active",
        "country": "IN"
    }

    print(f"🚀 Triggering Apify Scraper for: {competitor_name}")
    print(f"🔗 Search URL: {search_url}")
    
    try:
        # Using the ID of the official scraper
        run = client.actor("JJghSZmShuco4j9gJ").call(run_input=run_input)
        
        print(f"✅ Run finished: {run['status']}")
        
        # Fetch results from the dataset
        dataset_items = client.dataset(run['defaultDatasetId']).list_items().items
        return dataset_items
    except Exception as e:
        print(f"❌ Error scraping {competitor_name}: {e}")
        return None

def main():
    competitors = [
        "CampusDegree", 
        "College Vidya", 
        "apna advantage", 
        "Hike Education", 
        "LPU Online", 
        "Chandigarh University Online"
    ]
    
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                all_results = json.load(f)
        except:
            all_results = {}
    else:
        all_results = {}

    for comp in competitors:
        if comp in all_results and all_results[comp] and len(all_results[comp]) > 0:
            print(f"⏭️ Skipping {comp}, already scraped.")
            continue
            
        data = scrape_with_apify(comp)
        if data:
            all_results[comp] = data
            with open(RESULTS_FILE, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"💾 Saved {len(data)} ads for {comp}")
        else:
            print(f"⚠️ No data returned for {comp}")
            
    print(f"🏁 All tasks finished. Final results in {RESULTS_FILE}")

if __name__ == "__main__":
    main()
