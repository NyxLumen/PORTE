import os
import requests
from dotenv import load_dotenv

def test_api():
    load_dotenv()

    api_key = os.getenv("LIGHTX_API_KEY")
    if not api_key:
        print("❌ Error: LIGHTX_API_KEY not found in .env")
        return

    print(f"🔑 Using API Key: {api_key[:5]}...{api_key[-5:]}")
    
    url = "https://api.lightxeditor.com/external/api/v2/aivirtualtryon"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "imageUrl": "https://picsum.photos/400/600",
        "styleImageUrl": "https://picsum.photos/400/600"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 402:
            print("⚠️ 402 Payment Required: 25 Credits Finished!")
        elif response.status_code == 200:
            print("✅ Success! API is working.")
            print("Response:", response.json())
        else:
            print(f"❌ Error Output: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api()
