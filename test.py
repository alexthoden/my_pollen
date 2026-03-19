import requests

url = "https://pollen.googleapis.com/v1/forecast:lookup"
GOOGLE_API_KEY = "AIzaSyCEGcHOsNWArDRqOLAiEVS3uCBPU9whuaI"


params = {
    "key": GOOGLE_API_KEY,
    "location.latitude": 38.9072,
    "location.longitude": -77.0369,
    "days": 5
}

response = requests.get(url, params=params, timeout=10)

# Debug helpers
print("Status code:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Raw body:", response.text[:500])

response.raise_for_status()
data = response.json()

print(data)
