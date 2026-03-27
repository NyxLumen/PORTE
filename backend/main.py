import os
import requests
import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. CREDIT SAVER: CACHE ---
# Prevents wasting your 25 credits on repeat tests
api_cache = {}

class TryOnRequest(BaseModel):
    user_image_url: str
    garment_image_url: str

@app.post("/api/try-on")
async def generate_tryon(request: TryOnRequest):
    # Unique key for these two images
    cache_key = hashlib.md5(f"{request.user_image_url}{request.garment_image_url}".encode()).hexdigest()
    
    if cache_key in api_cache:
        print("💡 Cache Hit! Returning previous result to save credits.")
        return {"status": "success", "result_image_url": api_cache[cache_key]}

    print("🚀 Calling LightX V2 (Identity Lock Mode)...")
    
    # Using the V2 Endpoint which is better for keeping the face intact
    url = "https://api.lightxeditor.com/external/api/v2/aivirtualtryon"
    
    headers = {
        "x-api-key": os.getenv("LIGHTX_API_KEY"),
        "Content-Type": "application/json"
    }
    
    # V2 payload uses 'styleImageUrl' for the garment
    payload = {
        "imageUrl": request.user_image_url,
        "styleImageUrl": request.garment_image_url
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        # Check if credits are empty before we even try to parse
        if response.status_code == 402:
            print("⚠️ 25 Credits Finished! Triggering Failsafe.")
            raise HTTPException(status_code=503, detail="CREDITS_EXHAUSTED")

        response.raise_for_status()
        data = response.json()
        
        # LightX V2 path: data -> body -> imageUrl
        result_url = data.get("body", {}).get("imageUrl")
        
        if result_url:
            api_cache[cache_key] = result_url
            return {"status": "success", "result_image_url": result_url}
        else:
            raise Exception("API failure: No image returned.")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Send 503 so Adi's frontend shows the mock/pre-generated image
        raise HTTPException(status_code=503, detail="AI_ENGINE_OFFLINE")