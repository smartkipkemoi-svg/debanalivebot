import requests, os, random, time
from PIL import Image, ImageDraw, ImageFont

page_id = os.environ.get('FB_PAGE_ID')
token = os.environ.get('FB_TOKEN')
posts=0

def bold(t):
    a="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    try: return t.translate(str.maketrans(a,b))
    except: return t.upper()

# FULL LIST: Leagues + International + Europe
LEAGUES={
    # Top 5
    "eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1",
    # Other Important European
    "ned.1":"EREDIVISIE","por.1":"LIGA PORTUGAL","tur.1":"TURKISH SUPER LIG","sco.1":"SCOTTISH PREMIERSHIP",
    "bel.1":"JUPILER PRO LEAGUE","gre.1":"GREEK SUPER LEAGUE","aut.1":"AUSTRIAN BUNDESLIGA","den.1":"DANISH SUPERLIGA",
    "eng.fa":"FA CUP","eng.league_cup":"CARABAO CUP",
    # Outside Europe
    "ksa.1":"SAUDI PRO LEAGUE","usa.1":"MLS","mex.1":"LIGA MX",
    # UEFA Tournaments
    "uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE","uefa.conference":"CONFERENCE LEAGUE",
    # International
    "fifa.worldq":"WORLD CUP QUALIFIERS","uefa.nations":"NATIONS LEAGUE","uefa.euro.q":"EURO QUALIFIERS",
    "conmebol.america":"COPA AMERICA","caf.nations":"AFCON","fifa.world":"WORLD CUP"
}

LINES=["Defenders on vacation! Who wins?","VAR drama! Pure chaos!","Rate this goal 1-10!","Predict final score!","Football is BEAUTIFUL!"]

def make_img(home,away,sh,sa,minute,typ,league):
    W,H=1080,1350
    bg=(220,38,38) if typ=="GOAL" else (15,23,42)
    if typ=="HT": bg=(30,58,138)
    if typ=="FT": bg=(2,60,2)
    if typ=="NEWS": bg=(0,0,0)
    img=Image.new('RGB',(W,H),color=bg)
    d=ImageDraw.Draw(img)
    try:
        fb=ImageFont.truetype("DejaVuSans-Bold.ttf",110); fm=ImageFont.truetype("DejaVuSans-Bold.ttf",50)
        fs=ImageFont.truetype("DejaVuSans-Bold.ttf",38); ft=ImageFont.truetype("DejaVuSans.ttf",32)
    except: fb=fm=fs=ft=ImageFont.load_default()
    d.rectangle([0,0,W,120],fill=(0,0,0)); d.text((W//2,60),league,font=fs,fill="white",anchor="mm")
    label="GOAL ALERT" if typ=="GOAL" else typ
    d.rectangle([0,120,W,280],fill="white"); d.text((W//2,200),label,font=fm,fill=bg,anchor="mm")
    d.text((W//2,460),f"{sh} - {sa}",font=fb,fill="white",anchor="mm"); d.text((W//2,570),f"{minute}",font=fm,fill="yellow",anchor="mm")
    d.text((W//2,760),home[:22].upper(),font=fm,fill="white",anchor="mm"); d.text((W//2,830),"VS",font=ft,fill=(200,200,200),anchor="mm")
    d.text((W//2,900),away[:22].upper(),font=fm,fill="white",anchor="mm")
    d.rectangle([0,1160,W,H],fill=(0,0,0)); d.text((W//2,1210),"DE BANA LIVE",font=fs,fill="white",anchor="mm")
    d.text((W//2,1270),"26 Leagues + Intl",font=ft,fill=(150,150,150),anchor="mm")
    img.save("/tmp/live.jpg","JPEG",quality=95); return "/tmp/live.jpg"

def post(cap,path):
    global posts
    try:
        with open(path,'rb') as f:
            r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':cap,'access_token':token},timeout=15)
        print(f"POSTED {posts}: {r.text[:120]}"); posts+=1
    except Exception as e: print(f"err {e}")

last_score={}; last_detail={}
print(f"START {len(LEAGUES)} comps - 140 loops")

for loop in range(140):
    for code,lname in LEAGUES.items():
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            data=requests.get(url,timeout=7).json()
            for ev in data.get('events',[]):
                comp=ev['competitions'][0]; c1,c2=comp['competitors'][0],comp['competitors'][1]
                if c1['homeAway']!='home': c1,c2=c2,c1
                home=c1['team']['displayName']; away=c2['team']['displayName']
                sh=c1.get('score','0'); sa=c2.get('score','0')
                state=ev['status']['type']['state']; detail=ev['status']['type'].get('detail','')
                minute=ev['status'].get('displayClock','LIVE')
                mid=f"{code}_{ev['id']}"; cur=f"{sh}-{sa}"; prev=last_score.get(mid)
                if prev and prev!=cur and state=='in':
                    img=make_img(home,away,sh,sa,minute,"GOAL",lname)
                    cap=f"{bold('GOOO
