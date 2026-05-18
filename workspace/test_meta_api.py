import requests
TOKEN = ""
acc = "act_943943398169185"
url = f"https://graph.facebook.com/v19.0/{acc}/campaigns"
params = {"access_token": TOKEN, "fields": "id,name"}
r = requests.get(url, params=params)
print(r.json())
