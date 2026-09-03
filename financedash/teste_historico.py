import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("BRAPI_TOKEN")

url = "https://brapi.dev/api/v2/stocks/historical"

params = {
    "symbols": "PETR4",
    "range": "1mo",
    "interval": "1d"
}

headers = {
    "Authorization": f"Bearer {token}"
}

resposta = requests.get(
    url,
    params=params,
    headers=headers
)

print("Status:", resposta.status_code)
print(resposta.json())