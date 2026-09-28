import requests
import os
import random
import time
from PIL import Image, ImageDraw, ImageFont

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')

print(f"Page ID exists: {bool(page_id)}")

def fb_bold(s):
    mapping = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    )
    return s.translate(mapping)

style_c_bold = [
    f"{fb_bold('GOAL EXPLOSION!')} Pep is cooking, Arteta SWEATING! 😅 Who bottling?",
    f"{fb_bold('THIS GAME IS MAD!')} My heart can't take it! Defenders on VACATION! 💔",
    f"{fb_bold('VAR... GOAL STANDS!')} Pure CHAOS! Football BEAUTIFUL! 🔥",
    f"{fb_bold('WHAT A STRIKE!')} Keeper needs to buy defenders LUNCH! 😭",
    f"{fb_bold('DRAMA!')} One team DANCING, one CRYING! Which side you on? 🍿",
    f"{fb_bold('GOAL! GOAL! GOAL!')} Predict FINAL SCORE now! 👇"
]

# ========= ALL FOOTBALL LEAGUES =========
LEAGUES = {
    "eng.1": "PREMIER LEAGUE",
    "esp.1": "LA LIGA",
    "ita.1": "SERIE A",
    "ger.1": "BUNDESLIGA",
    "fra.1": "LIGUE 1",
    "uefa.champions": "CHAMPIONS LEAGUE",
    "uefa.europa": "EUROPA LEAGUE",
    "eng.fa": "FA CUP",
    "esp.copa_del_rey": "COPA DEL REY",
    "caf.champions": "CAF CHAMPIONS LEAGUE",
    "eng.2": "CHAMPIONSHIP",
    "por.1": "LIGA PORTUGAL",
    "ned.1": "EREDIVISIE",
    "usa.1": "MLS",
    "ksa.1": "SAUDI PRO LEAGUE"
}

def create_goal_image(home, away, sh, sa, minute, is_goal=False, scorer="GOAL!", league="FOOTBALL"):
    W, H = 1080, 1350
    bg_color = (220, 38, 38) if is_goal else (15, 23, 42)
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf",
