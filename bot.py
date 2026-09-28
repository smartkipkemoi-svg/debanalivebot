import requests
import os

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')

print(f"Page ID exists: {bool(page_id)}")
print(f"Token exists: {bool(token)}")

# Test post - no image, just text to check FB works
url = f"https://graph.facebook.com/{page_id}/feed"
data = {
    "message": "🔥 De Bana LIVE BOT is now ACTIVE! Testing... Bot will auto-post live scores every 2 mins. Stay tuned from Kisumu! ⚽",
    "access_token": token
}
r = requests.post(url, data=data)
print("FB Response:", r.text)
