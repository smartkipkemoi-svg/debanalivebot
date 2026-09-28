import requests,os,random,time
from PIL import Image,ImageDraw,ImageFont

page_id=os.environ.get('FB_PAGE_ID')
token=os.environ.get('FB_TOKEN')
posts=0

def bold(t):
 a="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
 b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
 try: return t.translate(str.maketrans(a,b))
 except: return t.upper()

# 20 LEAGUES INCLUDING TURKEY + CONFERENCE
LEAGUES={
 "eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1",
 "ned.1":"EREDIVISIE","por.1":"LIGA PORTUGAL","tur.1":"TURKISH SUPER LIG","sco.1":"SCOTTISH PREMIERSHIP",
 "bel.1":"JUPILER PRO LEAGUE","gre.1":"SUPER LEAGUE GREECE","ksa.1":"SAUDI PRO LEAGUE","usa.1":"MLS",
 "uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE","uefa.conference":"CONFERENCE LEAGUE",
 "fifa.worldq":"WORLD CUP QUALIFIERS","uefa.nations":"NATIONS LEAGUE","caf.nations":"AFCON","fifa.world":"WORLD CUP"
}

def make_img(home,away,sh,sa,minute,typ,league):
 W,H=1080,1350
 bg=(220,38,38) if typ=="GOAL" else (15,23,42)
 if typ=="NEWS": bg=(0,0,0)
 if typ=="FT": bg=(2,60,2)
 img=Image.new('RGB',(W,H),color=bg)
 d=ImageDraw.Draw(img)
 try:
  fb=ImageFont.truetype("DejaVuSans-Bold.ttf",110); fm=ImageFont.truetype("DejaVuSans-Bold.ttf",50)
  fs=ImageFont.truetype("DejaVuSans-Bold.ttf",36); ft=ImageFont.truetype("DejaVuSans.ttf",30)
 except: fb=fm=fs=ft=ImageFont.load_default()
 d.rectangle([0,0,W,110],fill=(0,0,0)); d.text((W//2,55),league,font=fs,fill="white",anchor="mm")
 d.rectangle([0,110,W,270],fill="white"); d.text((W//2,190),typ if typ!="GOAL" else "GOAL ALERT",font=fm,fill=bg,anchor="mm")
 d.text((W//2,450),f"{sh} - {sa}",font=fb,fill="white",anchor="mm"); d.text((W//2,550),minute,font=fm,fill="yellow",anchor="mm")
 d.text((W//2,750),home[:22].upper(),font=fm,fill="white",anchor="mm"); d.text((W//2,820),"VS",font=ft,fill=(200,200,200),anchor="mm")
 d.text((W//2,890),away[:22].upper(),font=fm,fill="white",anchor="mm")
 d.rectangle([0,1180,W,H],fill=(0,0,0)); d.text((W//2,1230),"DE BANA LIVE",font=fs,fill="white",anchor="mm")
 d.text((W//2,1290),"Turkish Super Lig + Conference League Included",font=ft,fill=(150,150,150),anchor="mm")
 img.save("/tmp/live.jpg","JPEG",quality=95); return "/tmp/live.jpg"

def post(cap,path):
 global posts
 try:
  with open(path,'rb') as f:
   r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':cap,'access_token':token},timeout=20)
  print(f"POSTED {posts}: {r.status_code} {r.text[:150]}"); posts+=1
 except Exception as e: print(f"POST ERR {e}")

last_score={}; last_detail={}
print(f"START {len(LEAGUES)} leagues - THIS WILL RUN 7 MINUTES")
# THIS LOOP MAKES IT RUN 7 MINUTES LIKE BEFORE
for loop in range(200):
 for code,lname in LEAGUES.items():
  try:
   url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
   data=requests.get(url,timeout=6).json()
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
     cap=f"{bold('GOOOAL!!!')} | {lname}\n\n{minute} | {bold(home)} {sh}-{sa} {bold(away)}\n\nWho scores next? Predict!\n\n#DeBana"
     post(cap,img)
    if state in ['in','post']: last_score[mid]=cur
  except: continue
 print(f"Loop {loop}/200 - games {len(last_score)} posted {posts}")
 time.sleep(2)

if posts==0:
 print("No goals live - posting news to keep page active")
 img=make_img("TURKISH SUPER
