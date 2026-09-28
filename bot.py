import requests, os, random, time
from PIL import Image, ImageDraw, ImageFont

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')

def bold(t):
    a="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    try:
        return t.translate(str.maketrans(a,b))
    except:
        return t.upper()

# ALL LEAGUES + INTERNATIONAL TOURNAMENTS
LEAGUES={
    # Top 5 leagues
    "eng.1":"PREMIER LEAGUE",
    "esp.1":"LA LIGA",
    "ita.1":"SERIE A",
    "ger.1":"BUNDESLIGA",
    "fra.1":"LIGUE 1",
    # Other leagues
    "ned.1":"EREDIVISIE",
    "por.1":"PRIMEIRA LIGA",
    "ksa.1":"SAUDI PRO LEAGUE",
    "usa.1":"MLS",
    "eng.fa":"FA CUP",
    # International + Tournaments
    "fifa.worldq":"WORLD CUP QUALIFIERS",
    "uefa.champions":"CHAMPIONS LEAGUE",
    "uefa.europa":"EUROPA LEAGUE",
    "uefa.nations":"NATIONS LEAGUE",
    "uefa.euro.q":"EURO QUALIFIERS",
    "concacaf.nations":"NATIONS LEAGUE",
    "conmebol.america":"COPA AMERICA",
    "caf.nations":"AFCON",
    "fifa.world":"WORLD CUP"
}

LINES=[
    "Defenders on vacation! Who wins?",
    "VAR drama! Pure chaos!",
    "Rate this goal 1-10!",
    "Predict final score below!",
    "Football is BEAUTIFUL!"
]

def make_img(home,away,sh,sa,minute,typ,league):
    W,H=1080
