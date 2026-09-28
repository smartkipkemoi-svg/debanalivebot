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

LEAGUES={
    "eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1",
    "ned.1":"EREDIVISIE","por.1":"LIGA PORTUGAL","ksa.1":"SAUDI PRO LEAGUE","usa.1":"MLS",
    "uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE",
    "fifa.worldq":"WORLD CUP QUALIFIERS","uefa.nations":"NATIONS LEAGUE","caf.nations":"AFCON"
}

def make_img(home,away,sh,sa,minute,typ,league):
    W,H=1080,1350
    bg=(220,38,38) if typ=="GOAL" else (15,23,42)
    if typ=="NEWS": bg=(0,0,0)
    img=Image.new('RGB',(W,H),color=bg)
    d=ImageDraw.Draw(img)
    try:
        fb=ImageFont.truetype("DejaVuSans-Bold.ttf",110); fm=ImageFont.truetype("DejaVuSans-Bold.ttf",50)
        fs=ImageFont.truetype("DejaVuSans-Bold.ttf",38)
    except: fb=fm=fs=ImageFont.load_default()
    d.rectangle([0,0,W,120],fill=(0,0,0)); d.text((W//2,60),league,font=fs,fill="white",anchor="mm")
    d.rectangle([0,120,W,280],fill="white"); d.text((W//2,200),typ,font=fm,fill=bg,anchor="mm")
    d.text((W//2,460),f"{sh} - {sa}",font=fb,fill="white",anchor="mm"); d.text((W//2,570),f"{minute}",font=fm,fill="yellow",anchor="mm")
    d.text((W//2,760),home[:22].upper(),font=fm,fill="white",anchor="mm"); d.text((W//2,900),away[:22].upper(),font=fm,fill="white",anchor="mm")
    d.rectangle([0,1160,W,H],fill=(0,0,0)); d.text((W//2,1220),"DE BANA LIVE",font=fs,fill="white",anchor="mm")
    img.save("/tmp/live.jpg","JPEG",quality=95); return "/tmp/live.jpg"

def post(cap,path):
    global posts
    try:
        with open(path,'rb') as f:
            r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':cap,'access_token':token},timeout=15)
        print(f"POSTED {posts}: {r.text[:120]}"); posts+=1
    except Exception as e: print(f"err {e}")

last_score={}
print(f"START {len(LEAGUES)} leagues - will run 7 mins")

for loop in range(140):
    for code,lname in LEAGUES.items():
        try:
            data=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",timeout=7).json()
            for ev in data.get('events',[]):
                comp=ev['competitions'][0]; c1,c2=comp['competitors'][0],comp['competitors'][1]
                if c1['homeAway']!='home': c1,c2=c2,c1
                home=c1['team']['displayName']; away=c2['team']['displayName']
                sh=c1.get('score','0'); sa=c2.get('score','0')
                state=ev['status']['type']['state']; minute=ev['status'].get('displayClock','LIVE')
                mid=f"{code}_{ev['id']}";
