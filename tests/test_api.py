# test_api.py
import requests
import json

def test_fact_check():
    url = "http://localhost:8000/api/v1/fact-check"
    
    test_input = {
        "status": "Success",
        "content_type": "youtube",
        "transcript": {
            "text": "Scientists recently discovered that drinking 8 glasses of water daily is essential for health. The study was published in Nature Medicine in 2024.",
            "words": []
        },
        "metadata": {
            "source_type": "youtube",
            "content_length": 150,
            "language_code": "en"
        },
        "beliefs": []
    }
    
    print("🔍 Testing Tattva Agent API with Google Gemini...")
    print(f"URL: {url}")
    print(f"\nInput text: {test_input['transcript']['text']}\n")
    
    try:
        response = requests.post(url, json=test_input, timeout=180)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Success!")
        print(f"\n📊 Summary: {result['summary']}")
        print(f"📈 Tattva Score: {result['tattva_score']:.1f}/100")
        print(f"🔢 Number of claims: {len(result['claims'])}")
        
        if result['claims']:
            print("\n📋 Claims:")
            for i, claim in enumerate(result['claims'], 1):
                print(f"\n  {i}. {claim['text']}")
                print(f"     Verdict: {claim['verdict']['label']}")
                print(f"     Truth Probability: {claim['verdict']['truth_prob_cal']:.2f}")
                print(f"     Evidence Strength: {claim['evidence_strength']:.2f}")
        
        print(f"\n💾 Full response saved to: tattva_response.json")
        with open('tattva_response.json', 'w') as f:
            json.dump(result, f, indent=2)
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Gemini might be taking longer than expected.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_fact_check()