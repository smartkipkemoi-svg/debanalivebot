import requests, os, json, time
from PIL import Image, ImageDraw
from io import BytesIO

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_TOKEN = os.getenv("FB_TOKEN")
POSTED_FILE = "posted.json"

LEAGUES = ["eng.1","esp.1","ita.1","ger.1","fra.1","uefa.champions","uefa.europa"]

def load_posted():
    try:
        with open(POSTED_FILE,"r") as f: return json.load(f)
    except: return {}

def save_posted(d):
    with open(POSTED_FILE,"w") as f: json.dump(d,f)

def create_img(h_logo,a_logo,h_team,a_team,hs,aws,minute):
    W,H=1080,1080
    img=Image.new("RGB",(W,H),(15,23,42))
    draw=ImageDraw.Draw(img)
    try:
        r1=requests.get(h_logo,timeout=10)
        r2=requests.get(a_logo,timeout=10)
        im1=Image.open(BytesIO(r1.content)).convert("RGBA").resize((300,300))
        im2=Image.open(BytesIO(r2.content)).convert("RGBA").resize((300,300))
        img.paste(im1,(150,280),im1)
        img.paste(im2,(630,280),im2)
    except: pass
    draw.text((540,200),minute,fill=(34,197,94),anchor="mm")
    draw.rectangle
