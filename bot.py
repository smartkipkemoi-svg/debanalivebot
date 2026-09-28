import requests
import os
import time
from PIL import Image, ImageDraw, ImageFont

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')
posts = 0

def bold(t):
    a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    b = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    try:
        return t.translate(str.maketrans(a,b))
    except:
        return t.upper()

LEAGUES = {
    "eng.1": "PREMIER LEAGUE",
    "esp.1": "LA LIGA",
    "ita.1": "SERIE A",
    "ger.1": "BUNDESLIGA",
    "fra.1": "LIGUE 1",
    "tur.1": "TURKISH SUPER LIG",
    "uefa.champions": "CHAMPIONS LEAGUE",
    "uefa.europa": "EUROPA LEAGUE",
    "uefa.conference": "CONFERENCE LEAGUE"
}

def make_img(home, away, sh, sa, minute, typ, league):
    W, H = 1080, 1350
    bg = (220, 38, 38) if typ == "GOAL" else (15, 23, 42)
    img = Image.new('RGB', (W, H), color=bg)
    d = ImageDraw.Draw(img)
    try:
        fb = ImageFont.truetype("DejaVuSans-Bold.ttf", 90)
        fm = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
    except:
        fb = ImageFont.load_default()
        fm = ImageFont.load_default()
    d.text((W//2, 500), league, font=fm, fill="white", anchor="mm")
    d.text((W//2, 600), f"{sh} - {sa}", font=fb, fill="white", anchor="mm")
    d.text((W//2, 750), f"{home[:22]}", font=fm, fill="white", anchor="mm")
    d.text((W//2, 810), "VS", font=fm, fill="yellow", anchor="mm")
    d.text((W//2, 870), f"{away[:22]}", font=fm, fill="white", anchor="mm")
    d.text((W//2, 950), minute, font=fm, fill="yellow", anchor="mm")
    img.save("/tmp/live.jpg", "JPEG", quality=95)
    return "/tmp/live.jpg"

def post_fb(cap, path):
    global posts
    try:
        with open(path, 'rb') as f:
            r = requests.post(
                f"https://graph.facebook.com/{page_id}/photos",
                files={'source': f},
                data={'caption': cap, 'access_token': token},
                timeout=15
            )
        print(f"POSTED {posts} {r.status_code}")
        posts += 1
    except Exception as e:
        print(f"err {e}")

last_score = {}
print("START - 9 leagues including Turkish + Conference - 7m run")

for loop in range(140):
    for code, lname in LEAGUES.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            data = requests.get(url, timeout=6).json()
            for ev in data.get('events', []):
                comp = ev['competitions'][0]
                c1 = comp
