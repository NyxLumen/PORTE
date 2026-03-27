import os
import requests
import hashlib
import asyncio
import time
from fastapi import FastAPI, HTTPException, File, UploadFile
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

def upload_to_tmpfiles(file_content: bytes) -> str:
    print("☁️ Uploading local file to temporary host (tmpfiles.org)...")
    url = "https://tmpfiles.org/api/v1/upload"
    # tmpfiles.org uses 'file' instead of 'image'
    response = requests.post(url, files={"file": ("upload.jpg", file_content, "image/jpeg")})
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            # Convert viewer URL to direct download URL
            original_url = data["data"]["url"]
            direct_url = original_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            return direct_url
    
    raise Exception(f"Failed to upload image to host. Status: {response.status_code}, Error: {response.text}")

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
        
        # Check for orderId (async processing)
        order_id = data.get("body", {}).get("orderId")
        
        if not order_id:
            # Maybe it returned synchronously?
            result_url = data.get("body", {}).get("imageUrl")
            if result_url:
                api_cache[cache_key] = result_url
                return {"status": "success", "result_image_url": result_url}
            raise Exception("API failure: No orderId or imageUrl returned.")

        print(f"⏳ Async Job Started. Order ID: {order_id}. Polling for result...")
        
        status_url = "https://api.lightxeditor.com/external/api/v1/order-status"
        
        # Poll up to 20 times (60 seconds)
        for _ in range(20):
            await asyncio.sleep(3)
            status_res = requests.post(status_url, json={"orderId": order_id}, headers=headers)
            status_data = status_res.json()
            
            job_status = status_data.get("body", {}).get("status")
            if job_status == "active":
                result_url = status_data.get("body", {}).get("output")
                if result_url:
                    api_cache[cache_key] = result_url
                    print("✅ Image generated successfully!")
                    return {"status": "success", "result_image_url": result_url}
            
            elif job_status == "failed":
                raise Exception("LightX order failed during processing.")
                
            print(f"🔄 Status: {job_status}... waiting.")
            
        raise Exception("LightX API timeout - image took too long.")

    except Exception as e:
        print(f"❌ Error: {e}")
        # Send 503 so Adi's frontend shows the mock/pre-generated image
        raise HTTPException(status_code=503, detail="AI_ENGINE_OFFLINE")

@app.post("/api/try-on-upload")
async def generate_tryon_upload(
    person_image: UploadFile = File(...), 
    garment_image: UploadFile = File(...)
):
    try:
        # Read files into memory
        person_bytes = await person_image.read()
        garment_bytes = await garment_image.read()
        
        # Upload to get public URLs
        person_url = upload_to_tmpfiles(person_bytes)
        garment_url = upload_to_tmpfiles(garment_bytes)
        
        print(f"🔗 Uploaded URLs:\nPerson: {person_url}\nGarment: {garment_url}")
        
        # Now use the existing TryOn logic
        request_obj = TryOnRequest(user_image_url=person_url, garment_image_url=garment_url)
        return await generate_tryon(request_obj)
        
    except Exception as e:
        print(f"❌ Upload API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))