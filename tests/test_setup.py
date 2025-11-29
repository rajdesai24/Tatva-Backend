# test_url_transcriber.py
import requests
import json

def test_youtube():
    url = "http://localhost:8000/api/v1/fact-check-url"
    
    params = {
        "url": "https://www.youtube.com/watch?v=OY8o5e331iM"
    }
    
    print("🎥 Testing YouTube URL...")
    response = requests.post(url, params=params, timeout=180)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

# def test_article():
#     url = "http://localhost:8000/api/v1/fact-check-url"
    
#     params = {
#         "url": "https://www.bbc.com/news/health"
#     }
    
#     print("\n📰 Testing Article URL...")
#     response = requests.post(url, params=params, timeout=180)
#     print(f"Status: {response.status_code}")
#     print(json.dumps(response.json(), indent=2))

# def test_twitter():
#     url = "http://localhost:8000/api/v1/fact-check-url"
    
#     params = {
#         "url": "https://twitter.com/elonmusk/status/1234567890"
#     }
    
#     print("\n🐦 Testing Twitter URL...")
#     response = requests.post(url, params=params, timeout=180)
#     print(f"Status: {response.status_code}")
#     print(json.dumps(response.json(), indent=2))

# def test_invalid():
#     url = "http://localhost:8000/api/v1/fact-check-url"
    
#     params = {
#         "url": "not-a-valid-url"
#     }
    
#     print("\n❌ Testing Invalid URL...")
#     response = requests.post(url, params=params)
#     print(f"Status: {response.status_code}")
#     print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_youtube()
