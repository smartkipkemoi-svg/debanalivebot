import requests, os, random, time
from PIL import Image, ImageDraw, ImageFont

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')

print(f"Page ID: {bool(page_id)} | Token: {bool(token)}")

def fb_bold(t):
    try:
        a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        b = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
        return t.translate(str.maketrans(a,b))
    except:
        return t.upper()

STYLE = [
    f"{fb_bold('GOAL EXPLOSION!')} Defenders on vacation! Who's bottling?",
    f"{fb_bold('DRAMA!')} VAR check... GOAL STANDS! Pure chaos!",
    f"{fb_bold('WHAT A GAME!')} Keeper needs to buy defenders lunch!",
    f"{fb_bold('FOOTBALL IS MAD!')} One team dancing, one crying!",
    f"{fb_bold('THIS IS CINEMA!')} Predict final score NOW!",
]

LEAGUES = {
    "eng.1": "PREMIER LEAGUE", "esp.1": "LA LIGA", "ita.1": "SERIE A",
    "ger.1": "BUNDESLIGA", "fra.1": "LIGUE 1",
    "uefa.champions": "CHAMPIONS LEAGUE", "uefa.europa": "EUROPA LEAGUE",
    "caf.champions": "CAF CHAMPIONS", "caf.nations": "AFCON",
    "ksa.1": "SAUDI PRO LEAGUE", "usa.1": "MLS", "por.1": "LIGA PORTUGAL"
}

def make_img(home, away, sh, sa, minute, typ, league, extra=""):
    W,H = 1080,1350
    colors = {
        "GOAL": (220,38
