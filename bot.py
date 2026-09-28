import os, time, requests, json

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

LEAGUES = {
    "eng.1":"PREMIER LEAGUE", "esp.1":"LA LIGA", "ita.1":"SERIE A",
    "ger.1":"BUNDESLIGA", "fra.1":"LIGUE 1", "ned.1":"EREDIVISIE",
    "por.1":"LIGA PORTUGAL", "tur.1":"TURKISH SUPER LIG",
    "uefa.champions":"CHAMPIONS LEAGUE", "uefa.europa":"EUROPA LEAGUE",
    "uefa.conference":"CONFERENCE LEAGUE", "uefa.nations":"NATIONS LEAGUE"
}

STATE_FILE = "state.json"
POSTED_FILE = "posted_events.json"

def post_to_fb(msg):
    url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    r = requests.post(url, data={"message": msg, "access_token": PAGE_TOKEN}, timeout=30)
    print(f"POSTED {r.status_code}: {msg[:80]}")
    return r

def get_summary(league, eid):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}"
        return requests.get(url, timeout=15).json()
