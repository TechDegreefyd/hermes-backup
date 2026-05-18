import asyncio
from playwright.async_api import async_playwright
import json
import sys

async def scrape_ads(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {url}...", file=sys.stderr)
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div[role="main"]', timeout=30000)
            await asyncio.sleep(5)
            
            # Extract ad cards
            # Meta Ads Library uses complex class names. We'll use a more robust selector.
            # Ad cards often have a specific structure.
            ads = await page.query_selector_all('div[role="main"] > div > div > div > div')
            
            results = []
            for ad in ads:
                text = await ad.inner_text()
                if not text or len(text) < 20: continue
                
                # Try to get image
                img = await ad.query_selector('img')
                img_src = await img.get_attribute('src') if img else ""
                
                results.append({
                    "text": text,
                    "image": img_src
                })
                if len(results) >= 10: break
            
            await browser.close()
            return results
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            await browser.close()
            return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    ads_data = asyncio.run(scrape_ads(url))
    print(json.dumps(ads_data, indent=2))
