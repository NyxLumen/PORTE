"""
PORTE - Garment Image Scraper
Extracts high-resolution product images from e-commerce URLs.

Strategy:
  1. First try a fast `requests` + regex approach to extract image URLs
     from the page source / embedded JSON (works for Myntra, Ajio, etc.)
  2. If that fails, fall back to Playwright (headless browser) for JS-heavy sites.

Network notes:
  - Ajio (Akamai WAF): Uses Safari iOS TLS fingerprint via curl_cffi to
    bypass bot detection. Chrome fingerprints are blocked on Indian mobile IPs.
  - Shein: Geoblocked from India at the IP level. Requires a proxy (set
    SCRAPER_PROXY in .env) or a non-Indian network to function.
"""

import asyncio
import json
import os
import re
import time
from urllib.parse import urlparse
from typing import Optional

import requests as http_requests


# ---------------------------------------------------------------------------
# Proxy & network config (loaded from environment)
# ---------------------------------------------------------------------------
# Set SCRAPER_PROXY in .env to route Ajio/Shein through a proxy.
# Example: SCRAPER_PROXY=http://user:pass@proxy.example.com:8080
#          SCRAPER_PROXY=socks5://user:pass@proxy.example.com:1080

def _get_proxy() -> Optional[str]:
    """Get proxy URL from environment if configured."""
    proxy = os.environ.get("SCRAPER_PROXY", "").strip()
    return proxy if proxy else None


def _proxy_dict() -> Optional[dict]:
    """Return proxy dict for curl_cffi / requests, or None."""
    proxy = _get_proxy()
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


# ---------------------------------------------------------------------------
# Site detection
# ---------------------------------------------------------------------------

def _detect_site(url: str) -> str:
    host = urlparse(url).hostname or ""
    if "myntra" in host:
        return "myntra"
    if "ajio" in host:
        return "ajio"
    if "amazon" in host:
        return "amazon"
    if "shein" in host:
        return "shein"
    return "generic"


# ---------------------------------------------------------------------------
# URL cleaning & filtering
# ---------------------------------------------------------------------------

def _clean_url(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    parts = raw.strip().split(",")
    last = parts[-1].strip().split(" ")[0]
    if last.startswith("//"):
        last = "https:" + last
    if last.startswith("http"):
        return last
    return None


def _upgrade_resolution(url: str) -> str:
    """Upgrade Myntra/Ajio thumbnail URLs to high resolution."""
    url = re.sub(r"/w_\d+", "/w_960", url)
    url = re.sub(r"/h_\d+", "/h_1280", url)
    url = re.sub(r"/q_\d+", "/q_95", url)
    return url


def _filter_unique(urls: list[str]) -> list[str]:
    seen = set()
    results = []
    skip = re.compile(
        r"(logo|icon|sprite|placeholder|blank|\.svg|\.gif|1x1|tracking|pixel|banner|"
        r"ad[-_]|favicon|retaillabs|return_request|request_approval|refund|app-strip|"
        r"scratch_card|sne-man|ticket-unit|vip-pass|msite\.jpg|300\.png|group-2x)",
        re.IGNORECASE,
    )
    for u in urls:
        if skip.search(u):
            continue
        upgraded = _upgrade_resolution(u)
        if upgraded not in seen:
            seen.add(upgraded)
            results.append(upgraded)
    return results


# ---------------------------------------------------------------------------
# Strategy 1: Fast HTTP requests + regex/JSON parsing
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def _scrape_myntra_fast(url: str) -> list[str]:
    """Extract Myntra images from the embedded pdpData JSON in page source."""
    print("[SCRAPER] Trying fast extraction for Myntra...")
    try:
        resp = http_requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[SCRAPER] Myntra returned status {resp.status_code}")
            return []

        html = resp.text
        images: list[str] = []

        # Myntra embeds product data as: window.__myx = {"pdpData":...}
        # or in a <script> with pdpData
        pdp_match = re.search(r'"pdpData"\s*:\s*(\{.+?\})\s*[,}]\s*\n', html, re.DOTALL)
        if not pdp_match:
            # Try alternative pattern
            pdp_match = re.search(r'pdpData\s*=\s*(\{.+?\});\s*\n', html, re.DOTALL)

        if pdp_match:
            try:
                data = json.loads(pdp_match.group(1))
                # Navigate: pdpData -> media -> albums -> images
                media = data.get("media", {})
                albums = media.get("albums", {})

                for album_key, album in albums.items():
                    if isinstance(album, dict):
                        album_images = album.get("images", [])
                        for img in album_images:
                            if isinstance(img, dict):
                                # Try highest resolution keys
                                for key in ["secureSrc", "imageURL", "src"]:
                                    if key in img:
                                        cleaned = _clean_url(img[key])
                                        if cleaned:
                                            images.append(cleaned)
                                        break
                    elif isinstance(album, list):
                        for img in album:
                            if isinstance(img, dict):
                                for key in ["secureSrc", "imageURL", "src"]:
                                    if key in img:
                                        cleaned = _clean_url(img[key])
                                        if cleaned:
                                            images.append(cleaned)
                                        break
            except json.JSONDecodeError:
                print("[SCRAPER] Could not parse pdpData JSON")

        # Fallback: regex for Myntra image CDN URLs
        if not images:
            cdn_pattern = re.compile(
                r'https?://assets\.myntassets\.com/[^\s"\'<>]+\.(?:jpg|jpeg|webp|png)',
                re.IGNORECASE,
            )
            images = cdn_pattern.findall(html)

        unique_images = _filter_unique(images)
        return [unique_images[0]] if unique_images else []

    except Exception as e:
        print(f"[SCRAPER] Fast Myntra extraction failed: {e}")
        return []


def _extract_ajio_product_code(url: str) -> str | None:
    """Extract product code from Ajio URL. e.g. /p/702891478_blue -> 702891478_blue"""
    match = re.search(r'/p/([^/?&#]+)', url)
    return match.group(1) if match else None


# Safari iOS headers — Akamai on Ajio whitelists Safari TLS fingerprints
# while aggressively blocking Chrome fingerprints from Indian mobile IPs.
AJIO_API_HEADERS_SAFARI = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ajio.com/",
}

AJIO_API_HEADERS_CHROME = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "application/json",
    "x-requested-with": "XMLHttpRequest",
    "Referer": "https://www.ajio.com/",
}

# Ordered by success rate on Indian mobile networks
_AJIO_PROFILES = [
    ("safari17_0",    AJIO_API_HEADERS_SAFARI),
    ("safari17_2_ios", AJIO_API_HEADERS_SAFARI),
    ("safari15_5",    AJIO_API_HEADERS_SAFARI),
    ("chrome120",     AJIO_API_HEADERS_CHROME),
    ("chrome110",     AJIO_API_HEADERS_CHROME),
]


def _parse_ajio_images(data: dict) -> list[str]:
    """Extract image URLs from Ajio API JSON response."""
    images: list[str] = []

    # The API returns an "images" array with format types:
    # "superZoomPdp" (1117x1400), "product" (473x593), "thumbnail" (78x98)
    api_images = data.get("images", [])
    for img in api_images:
        if isinstance(img, dict):
            fmt = img.get("format", "")
            img_url = img.get("url", "")
            if fmt == "superZoomPdp" and img_url:
                cleaned = _clean_url(img_url)
                if cleaned:
                    images.append(cleaned)

    # Fallback to product format
    if not images:
        for img in api_images:
            if isinstance(img, dict):
                fmt = img.get("format", "")
                img_url = img.get("url", "")
                if fmt == "product" and img_url:
                    cleaned = _clean_url(img_url)
                    if cleaned:
                        images.append(cleaned)

    # Also check modelImage from baseOptions
    if not images:
        base_options = data.get("baseOptions", [])
        for opt in base_options:
            selected = opt.get("selected", {})
            model_img = selected.get("modelImage", {})
            img_url = model_img.get("url", "")
            if img_url:
                cleaned = _clean_url(img_url)
                if cleaned:
                    images.append(cleaned)

    # Fallback: look for any key containing image URLs in the response
    if not images:
        _find_image_urls_recursive(data, images, depth=0)

    return images


def _find_image_urls_recursive(obj, results: list, depth: int = 0):
    """Recursively search a JSON object for image URLs."""
    if depth > 6 or len(results) > 20:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("http") and any(
                ext in v.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]
            ):
                cleaned = _clean_url(v)
                if cleaned:
                    results.append(cleaned)
            elif isinstance(v, (dict, list)):
                _find_image_urls_recursive(v, results, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _find_image_urls_recursive(item, results, depth + 1)


def _scrape_ajio_fast(url: str) -> list[str]:
    """Extract Ajio images via internal product API using curl_cffi.

    Tries multiple TLS impersonation profiles (Safari first, then Chrome)
    because Akamai blocks Chrome fingerprints from Indian mobile IPs.
    Falls back to a configured proxy if all direct attempts fail.
    """
    print("[SCRAPER] Trying Ajio extraction via internal product API...")
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        print("[SCRAPER] curl_cffi not installed. Run: pip install curl_cffi")
        return []

    product_code = _extract_ajio_product_code(url)
    if not product_code:
        print(f"[SCRAPER] Could not extract product code from URL: {url}")
        return []

    api_url = f"https://www.ajio.com/api/p/{product_code}"
    print(f"[SCRAPER] Ajio API: {api_url}")
    proxies = _proxy_dict()

    # Try each impersonation profile
    for profile_name, headers in _AJIO_PROFILES:
        try:
            kwargs = {
                "headers": headers,
                "timeout": 15,
                "impersonate": profile_name,
            }
            if proxies:
                kwargs["proxies"] = proxies

            print(f"[SCRAPER]   Trying profile: {profile_name}" + (" (via proxy)" if proxies else ""))
            resp = cffi_requests.get(api_url, **kwargs)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    images = _parse_ajio_images(data)
                    if images:
                        print(f"[SCRAPER]   Success with {profile_name}: {len(images)} image(s)")
                        return _filter_unique(images)
                    else:
                        print(f"[SCRAPER]   {profile_name} returned 200 but no images in response")
                except (json.JSONDecodeError, ValueError):
                    print(f"[SCRAPER]   {profile_name} returned 200 but non-JSON body")
            else:
                print(f"[SCRAPER]   {profile_name} returned status {resp.status_code}")

        except Exception as e:
            err = str(e)[:80]
            print(f"[SCRAPER]   {profile_name} failed: {err}")

    # If all profiles failed without proxy, try again with proxy if available
    if not proxies:
        proxy_url = _get_proxy()
        if not proxy_url:
            print("[SCRAPER] All Ajio profiles failed. Set SCRAPER_PROXY in .env for proxy bypass.")
    else:
        print("[SCRAPER] All Ajio profiles failed even with proxy.")

    return []


def _scrape_amazon_fast(url: str) -> list[str]:
    """Extract Amazon product images from embedded colorImages JSON or data-a-dynamic-image."""
    print("[SCRAPER] Trying fast extraction for Amazon...")
    try:
        resp = http_requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[SCRAPER] Amazon returned status {resp.status_code}")
            return []

        html = resp.text
        images: list[str] = []

        # Strategy 1: Extract from 'colorImages' JSON embedded in a <script>
        # Amazon stores all product images in: 'colorImages': {'initial': [{"hiRes": "...", "large": "..."}]}
        color_match = re.search(r"'colorImages'\s*:\s*\{\s*'initial'\s*:\s*(\[.+?\])", html, re.DOTALL)
        if color_match:
            try:
                # Amazon uses single quotes in JS, convert to valid JSON
                raw_json = color_match.group(1)
                raw_json = raw_json.replace("'", '"')
                img_list = json.loads(raw_json)
                for item in img_list:
                    if isinstance(item, dict):
                        # Prefer hiRes > large > thumb
                        for key in ["hiRes", "large", "thumb"]:
                            img_url = item.get(key)
                            if img_url and img_url != "null":
                                cleaned = _clean_url(img_url)
                                if cleaned:
                                    images.append(cleaned)
                                break
            except (json.JSONDecodeError, Exception) as e:
                print(f"[SCRAPER] Could not parse Amazon colorImages: {e}")

        # Strategy 2: data-a-dynamic-image attribute on #landingImage
        if not images:
            dyn_match = re.search(r'data-a-dynamic-image="([^"]+)"', html)
            if dyn_match:
                try:
                    # This attribute is HTML-escaped JSON
                    raw = dyn_match.group(1).replace('&quot;', '"')
                    dyn_data = json.loads(raw)
                    # Keys are URLs, values are [width, height]
                    for img_url in dyn_data.keys():
                        cleaned = _clean_url(img_url)
                        if cleaned:
                            images.append(cleaned)
                except (json.JSONDecodeError, Exception):
                    print("[SCRAPER] Could not parse data-a-dynamic-image")

        # Strategy 3: application/ld+json structured data
        if not images:
            ld_match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.+?)</script>', html, re.DOTALL)
            if ld_match:
                try:
                    ld_data = json.loads(ld_match.group(1))
                    if isinstance(ld_data, dict):
                        img = ld_data.get("image")
                        if isinstance(img, str):
                            images.append(img)
                        elif isinstance(img, list):
                            images.extend([u for u in img if isinstance(u, str)])
                except json.JSONDecodeError:
                    pass

        # Strategy 4: Regex fallback for Amazon image CDN
        if not images:
            cdn_pattern = re.compile(
                r'https?://m\.media-amazon\.com/images/I/[^\s"\'\'<>]+\.(?:jpg|jpeg|png)',
                re.IGNORECASE,
            )
            raw_urls = cdn_pattern.findall(html)
            # Upgrade Amazon thumbnails: replace ._SX/_SY with large size
            for u in raw_urls:
                upgraded = re.sub(r'\._[A-Z]{2}\d+_', '._SL1500_', u)
                images.append(upgraded)

        # Filter Amazon-specific junk (buy-box icons, rating stars, etc.)
        amazon_skip = re.compile(
            r"(sprite|icon|badge|star|prime|a-icon|loading|grey-pixel|transparent-pixel)",
            re.IGNORECASE,
        )
        images = [u for u in images if not amazon_skip.search(u)]

        return _filter_unique(images)

    except Exception as e:
        print(f"[SCRAPER] Fast Amazon extraction failed: {e}")
        return []


def _normalize_shein_url(url: str) -> str:
    """Normalize shein.in (geoblocked) to us.shein.com."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host == "www.shein.in" or host == "shein.in":
        new_url = url.replace("://www.shein.in", "://us.shein.com")
        new_url = new_url.replace("://shein.in", "://us.shein.com")
        print(f"[SCRAPER] Redirecting geoblocked shein.in -> us.shein.com")
        return new_url
    return url


_SHEIN_PROFILES = [
    "chrome120",
    "safari17_0",
    "chrome110",
    "safari15_5",
]


def _parse_shein_html(html: str) -> list[str]:
    """Parse Shein HTML for product images."""
    images: list[str] = []

    # Strategy 1: window.__INITIAL_STATE__ JSON
    state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});\s*</', html, re.DOTALL)
    if state_match:
        try:
            data = json.loads(state_match.group(1))
            product_intro = data.get("productIntro", {})
            goods_mirror = product_intro.get("goodsMirror", {})
            goods_imgs = goods_mirror.get("goods_imgs", {})

            for img_key, img_data in goods_imgs.items():
                if isinstance(img_data, list):
                    for item in img_data:
                        if isinstance(item, dict):
                            img_url = item.get("origin_image") or item.get("image_url") or item.get("thumbnail")
                            if img_url:
                                cleaned = _clean_url(img_url)
                                if cleaned:
                                    images.append(cleaned)
                        elif isinstance(item, str):
                            cleaned = _clean_url(item)
                            if cleaned:
                                images.append(cleaned)
                elif isinstance(img_data, str):
                    cleaned = _clean_url(img_data)
                    if cleaned:
                        images.append(cleaned)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[SCRAPER] Could not parse Shein __INITIAL_STATE__: {e}")

    # Strategy 1b: Try recursive search on __INITIAL_STATE__ if structured extraction failed
    if not images and state_match:
        try:
            data = json.loads(state_match.group(1))
            _find_image_urls_recursive(data, images, depth=0)
        except:
            pass

    # Strategy 2: application/ld+json structured data
    if not images:
        ld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.+?)</script>', html, re.DOTALL)
        for ld_text in ld_matches:
            try:
                ld_data = json.loads(ld_text)
                if isinstance(ld_data, dict):
                    img = ld_data.get("image")
                    if isinstance(img, str):
                        images.append(img)
                    elif isinstance(img, list):
                        images.extend([u for u in img if isinstance(u, str)])
            except json.JSONDecodeError:
                continue

    # Strategy 3: Regex for Shein CDN URLs (img.ltwebstatic.com)
    if not images:
        cdn_pattern = re.compile(
            r'https?://img\.ltwebstatic\.com/[^\s"\'<>]+\.(?:jpg|jpeg|webp|png)',
            re.IGNORECASE,
        )
        images = cdn_pattern.findall(html)

    return images


def _scrape_shein_fast(url: str) -> list[str]:
    """Extract Shein product images using curl_cffi for anti-bot bypass.

    Shein is fully geoblocked from Indian IPs (connection timeout).
    A proxy (SCRAPER_PROXY env var) is required when on Indian networks.
    """
    print("[SCRAPER] Trying Shein extraction with TLS fingerprint bypass...")

    # Normalize geoblocked shein.in to us.shein.com
    url = _normalize_shein_url(url)

    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        print("[SCRAPER] curl_cffi not installed. Run: pip install curl_cffi")
        return []

    proxies = _proxy_dict()
    if not proxies:
        print("[SCRAPER] WARNING: No SCRAPER_PROXY set. Shein is geoblocked from Indian IPs — set SCRAPER_PROXY in .env")

    for profile in _SHEIN_PROFILES:
        try:
            kwargs = {
                "headers": HEADERS,
                "timeout": 20,
                "impersonate": profile,
                "allow_redirects": True,
            }
            if proxies:
                kwargs["proxies"] = proxies

            print(f"[SCRAPER]   Trying Shein with {profile}" + (" (via proxy)" if proxies else ""))
            resp = cffi_requests.get(url, **kwargs)

            if resp.status_code == 200:
                images = _parse_shein_html(resp.text)
                if images:
                    print(f"[SCRAPER]   Success with {profile}: {len(images)} image(s)")
                    return _filter_unique(images)
                else:
                    print(f"[SCRAPER]   {profile} returned 200 but no images found in HTML")
            else:
                print(f"[SCRAPER]   {profile} returned status {resp.status_code}")

        except Exception as e:
            err = str(e)[:80]
            print(f"[SCRAPER]   {profile} failed: {err}")

    print("[SCRAPER] All Shein profiles failed. Ensure SCRAPER_PROXY is set for Indian networks.")
    return []


def _scrape_generic_fast(url: str) -> list[str]:
    """Generic: grab all image URLs from HTML source."""
    print("[SCRAPER] Trying generic fast extraction...")
    try:
        resp = http_requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[SCRAPER] Site returned status {resp.status_code}")
            return []

        html = resp.text
        # Find all image URLs in src, srcset, and data-src attributes
        img_pattern = re.compile(
            r'(?:src|srcset|data-src)\s*=\s*["\']([^"\']+\.(?:jpg|jpeg|webp|png)[^"\']*)',
            re.IGNORECASE,
        )
        raw = img_pattern.findall(html)
        images = []
        for u in raw:
            cleaned = _clean_url(u)
            if cleaned:
                images.append(cleaned)

        return _filter_unique(images)

    except Exception as e:
        print(f"[SCRAPER] Generic extraction failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Strategy 2: Playwright browser fallback
# ---------------------------------------------------------------------------

STEALTH_JS = """
() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
}
"""


async def _launch_stealth_browser():
    """Launch a stealth headless browser. Returns (playwright, browser, context, page) tuple."""
    from playwright.async_api import async_playwright
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    context = await browser.new_context(
        user_agent=HEADERS["User-Agent"],
        viewport={"width": 1920, "height": 1080},
        java_script_enabled=True,
        locale="en-US",
    )
    page = await context.new_page()
    await page.add_init_script(STEALTH_JS)
    return pw, browser, context, page


async def _scrape_ajio_browser(url: str) -> list[str]:
    """Scrape Ajio using Playwright since they block HTTP requests with Akamai."""
    print("[SCRAPER] Using browser for Ajio (Akamai protected)...")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[SCRAPER] Playwright not installed.")
        return []

    pw, browser, context, page = await _launch_stealth_browser()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # Try to extract __PRELOADED_STATE__ from page JS context
        images: list[str] = []
        state_data = await page.evaluate("""
            () => {
                try {
                    if (window.__PRELOADED_STATE__) {
                        return JSON.stringify(window.__PRELOADED_STATE__);
                    }
                } catch(e) {}
                return null;
            }
        """)

        if state_data:
            try:
                data = json.loads(state_data)
                # Navigate: product -> images or pdp data
                # Ajio stores images under various paths
                for key in ["product", "pdp", "products"]:
                    section = data.get(key, {})
                    if isinstance(section, dict):
                        for pid, prod in section.items():
                            if isinstance(prod, dict):
                                for img_key in ["images", "imageList", "galleryImages"]:
                                    img_list = prod.get(img_key, [])
                                    if isinstance(img_list, list):
                                        for item in img_list:
                                            if isinstance(item, str):
                                                cleaned = _clean_url(item)
                                                if cleaned:
                                                    images.append(cleaned)
                                            elif isinstance(item, dict):
                                                for k in ["url", "src", "imageUrl", "originalImage"]:
                                                    if k in item:
                                                        cleaned = _clean_url(item[k])
                                                        if cleaned:
                                                            images.append(cleaned)
                                                        break
            except json.JSONDecodeError:
                pass

        # Fallback: grab images from DOM
        if not images:
            img_urls = await page.evaluate("""
                () => {
                    const urls = [];
                    // Ajio product images
                    document.querySelectorAll('.rilrtl-lazy-img, .zoom-wrap img, .img-alignment img, .carousel-container img').forEach(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        if (src) urls.push(src);
                    });
                    // Also try all images and filter by size
                    if (urls.length === 0) {
                        document.querySelectorAll('img').forEach(img => {
                            const w = img.naturalWidth || img.width || 0;
                            const h = img.naturalHeight || img.height || 0;
                            if ((w > 200 || h > 200) && img.src) {
                                urls.push(img.src);
                            }
                        });
                    }
                    return urls;
                }
            """)
            for u in img_urls:
                cleaned = _clean_url(u)
                if cleaned:
                    images.append(cleaned)

        # Also try regex on page source for Ajio CDN
        if not images:
            content = await page.content()
            cdn_pattern = re.compile(
                r'https?://assets\.ajio\.com/[^\s"\'\'<>]+\.(?:jpg|jpeg|webp|png)',
                re.IGNORECASE,
            )
            images = cdn_pattern.findall(content)

        return _filter_unique(images)

    except Exception as e:
        print(f"[SCRAPER] Ajio browser extraction error: {e}")
        return []
    finally:
        await browser.close()
        await pw.stop()


async def _scrape_with_browser(url: str, timeout_ms: int = 30000) -> list[str]:
    """Fallback: use headless browser for JS-rendered pages."""
    print("[SCRAPER] Falling back to browser-based extraction...")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[SCRAPER] Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        return []

    pw, browser, context, page = await _launch_stealth_browser()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        await page.wait_for_timeout(5000)

        # Scroll to trigger lazy loading
        await page.evaluate("""
            async () => {
                const delay = ms => new Promise(r => setTimeout(r, ms));
                for (let i = 0; i < 5; i++) {
                    window.scrollBy(0, window.innerHeight / 2);
                    await delay(500);
                }
                window.scrollTo(0, 0);
            }
        """)
        await page.wait_for_timeout(2000)

        # Extract all images via JS
        img_data = await page.evaluate("""
            () => {
                const imgs = [];
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || '';
                    const srcset = img.srcset || '';
                    const dataSrc = img.getAttribute('data-src') || '';
                    if (src) imgs.push(src);
                    if (srcset) imgs.push(srcset.split(',').pop().trim().split(' ')[0]);
                    if (dataSrc) imgs.push(dataSrc);
                });
                // Also check background images
                document.querySelectorAll('[style*="background-image"]').forEach(el => {
                    const bg = getComputedStyle(el).backgroundImage;
                    const match = bg.match(/url\\(["']?(.+?)["']?\\)/);
                    if (match) imgs.push(match[1]);
                });
                return imgs;
            }
        """)

        images = []
        for u in img_data:
            cleaned = _clean_url(u)
            if cleaned:
                images.append(cleaned)

        return _filter_unique(images)

    except Exception as e:
        print(f"[SCRAPER] Browser extraction error: {e}")
        return []
    finally:
        await browser.close()
        await pw.stop()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def scrape_garment_images(product_url: str) -> list[str]:
    """
    Scrape garment images from a product URL.
    
    Tries fast HTTP-based extraction first, then falls back to browser.
    
    Args:
        product_url: Full URL of the product page.
    
    Returns:
        List of high-resolution image URLs.
    """
    site = _detect_site(product_url)
    print(f"[SCRAPER] Detected site: {site} | URL: {product_url}")

    # Step 1: Try fast HTTP extraction
    images: list[str] = []

    if site == "myntra":
        images = _scrape_myntra_fast(product_url)
    elif site == "ajio":
        # Ajio blocks HTTP requests (Akamai), so try fast first, then browser
        images = _scrape_ajio_fast(product_url)
        if not images:
            images = await _scrape_ajio_browser(product_url)
            if images:
                print(f"[SCRAPER] Ajio browser extraction found {len(images)} image(s)")
                return images
    elif site == "amazon":
        images = _scrape_amazon_fast(product_url)
    elif site == "shein":
        images = _scrape_shein_fast(product_url)
    else:
        images = _scrape_generic_fast(product_url)

    if images:
        print(f"[SCRAPER] Fast extraction found {len(images)} image(s)")
        return images

    # Step 2: Fallback to browser-based scraping
    print("[SCRAPER] Fast extraction failed, trying browser fallback...")
    images = await _scrape_with_browser(product_url)

    if images:
        print(f"[SCRAPER] Browser extraction found {len(images)} image(s)")
    else:
        print("[SCRAPER] No images found via any method")

    return images


# ---------------------------------------------------------------------------
# Standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.myntra.com"
    
    # Redirect all debug prints to stderr so that stdout only contains the final raw URL
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    proxy = _get_proxy()
    if not proxy:
        print("[CONFIG] No SCRAPER_PROXY set (Ajio/Shein may fail on Indian networks)")
    
    results = asyncio.run(scrape_garment_images(url))
    
    # Restore stdout
    sys.stdout = old_stdout
    
    # Output JUST the first link on stdout, cleanly
    if results:
        print(results[0])
