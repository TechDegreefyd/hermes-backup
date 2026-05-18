import requests

TOKEN = ""

url = "https://graph.facebook.com/v19.0/ads_archive"
params = {
    'search_terms': 'University Admit',
    'ad_type': 'ALL',
    'ad_reached_countries': '["IN"]',
    'fields': 'page_id,page_name,ad_snapshot_url,ad_creative_bodies',
    'access_token': TOKEN,
    'limit': 10
}

resp = requests.get(url, params=params).json()
print("Ads Archive Search Results:")
for ad in resp.get('data', []):
    print(f"Page: {ad.get('page_name')} (ID: {ad.get('page_id')})")
