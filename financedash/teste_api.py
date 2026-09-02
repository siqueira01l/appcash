import requests

url = "https://brapi.dev/api/v2/stocks/quote"

params = {
    "symbols": "PETR4,VALE3,ITUB4"
}

resposta = requests.get(url, params=params)

print(resposta.status_code)
print(resposta.json())