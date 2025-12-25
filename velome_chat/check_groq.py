import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY not found in environment or .env file.")
    exit(1)

url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print("Success! API Key is valid.")
    print("Available Models:")
    models = response.json()
    for model in models['data']:
        print(f" - {model['id']}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to Groq API: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
