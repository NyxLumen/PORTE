import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_clothing_image(url: str) -> str:
    """
    A foundational web scraper that attempts to find the main product image 
    from a given e-commerce or website URL.
    Returns the absolute URL of the extracted image.
    """
    try:
        print(f"🕵️ Scraping URL: {url}")
        
        # We use a browser-like User-Agent to prevent anti-bot blocking on e-commerce sites
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Strategy 1: Open Graph Image (Most standard way modern sites define their main thumbnail)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            print("✅ Found image via Open Graph (og:image)")
            return urljoin(url, og_image["content"])
            
        # Strategy 2: Twitter Card Image
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            print("✅ Found image via Twitter Card")
            return urljoin(url, twitter_image["content"])
            
        # Strategy 3: Inspect <img> tags specifically for product heuristics
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
                
            # Convert to absolute URL
            abs_url = urljoin(url, src)
            
            # Simple heuristic: Look for keywords that suggest it's a main product picture
            img_class = " ".join(img.get("class", [])).lower()
            if "product" in img_class or "product" in src.lower() or "main" in img_class:
                print("✅ Found image via product heuristic")
                return abs_url
                
        # Strategy 4: Fallback to the very first valid image found on the page
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("http"):
                print("⚠️ Falling back to first generic image found")
                return src
                
        raise Exception("No suitable image found on the page.")
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None

# --- Quick Test ---
if __name__ == "__main__":
    # Test it with a random url when run directly!
    test_url = "https://picsum.photos/"
    result = scrape_clothing_image(test_url)
    print(f"Resulting Image URL: {result}")
