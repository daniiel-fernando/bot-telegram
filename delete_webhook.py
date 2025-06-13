import requests

BOT_TOKEN = "7511685057:AAH0RMb1Ys2uM1Cejgdrh4KvQ6augHYjfdU"  # Token como string
url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

response = requests.get(url)
print(response.json())
