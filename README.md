# PORTÉ

PORTÉ is a fashion-tech platform that generates a realistic 3D digital avatar from a single user photo and enables AI-powered virtual outfit try-ons.

The goal is to remove the uncertainty of online clothing purchases by allowing users to see how clothes actually look on their own body before buying.

## Core Idea

Most online clothing purchases fail because users cannot visualize how a garment will fit or look on them. PORTÉ solves this by generating a personalized digital twin and simulating clothing directly on the user's avatar.

## Key Features

- **Single Photo → 3D Avatar**
  - Generate a realistic digital body model from one image.

- **Virtual Try-On**
  - Overlay clothing items on the avatar to simulate fit and appearance.

- **AI Outfit Generator**
  - Suggest complete outfit combinations based on style, color harmony, and trends.

- **Personal Wardrobe Builder**
  - Save owned clothes and test combinations before wearing them.

- **E-commerce Integration**
  - Preview clothing from online stores before purchase.

## Potential Use Cases

- Online shoppers reducing return rates
- Fashion discovery and outfit planning
- Digital wardrobes
- Virtual fitting rooms for e-commerce platforms

## Long-Term Vision

PORTÉ aims to become the **standard digital identity layer for fashion**, enabling users to carry a persistent avatar across shopping platforms, fashion apps, and virtual environments.

## Tech Stack (Planned)

- **Frontend:** React / Three.js
- **3D Rendering:** WebGL / Three.js
- **AI Models:** Body reconstruction + garment simulation
- **Backend:** Node.js / Python
- **ML Tools:** PyTorch / diffusion models

---

## Developer Tooling

### Multi-Site Garment Scraper
The PORTE backend includes a powerful multi-strategy scraper capable of bypassing aggressive anti-bot protections (like Akamai and Cloudflare) to extract high-resolution garment images from popular e-commerce sites.

**Supported Sites:**
- Myntra
- Amazon
- Ajio (via internal API & TLS fingerprint impersonation)
- Shein (via geoblock routing & TLS fingerprint impersonation)

#### How to use the Scraper from the CLI

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Ensure dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Run the scraper via Python:**
   Pass the full product URL as an argument to the script.
   ```bash
   # Amazon
   python scraper.py "https://www.amazon.in/dp/B0CBBB5843/"

   # Ajio
   python scraper.py "https://www.ajio.com/buda-jeans-co-men-striped-regular-fit-shirt-/p/702891478_blue"

   # Myntra
   python scraper.py "https://www.myntra.com/tshirts/brand/product-name/12345/buy"
   
   # Shein
   python scraper.py "https://shein.in/some-product.html"
   ```

The script will output the detected site, the extraction strategy used, and a clean list of high-resolution image URLs ready to be used by the virtual try-on engine.
