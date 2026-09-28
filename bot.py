import requests,os,random,time
from PIL import Image,ImageDraw,ImageFont
page_id=os.environ.get('FB_PAGE_ID');token=os.environ.get('FB_TOKEN');posts=0
def bold(t):
 a="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
 b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
 try: return t.translate(str.maketrans(a,b))
 except: return t
LEAGUES={"eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1","ned.1":"EREDIVISIE","por.1":"LIGA PORTUGAL","tur.1":"TURKISH SUPER LIG","sco.1":"SCOTTISH PREMIERSHIP","bel.1":"JUPILER LEAGUE","gre.1":"GREEK SUPER LEAGUE","eng.fa":"FA CUP","ksa.1":"SAUDI LEAGUE","usa.1":"MLS","uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE","uefa.conference":"CONFERENCE LEAGUE","fifa.worldq":"WORLD CUP QUALIFIERS","uefa.nations":"NATIONS LEAGUE","caf.nations":"AFCON"}
def make_img(h,a,sh,sa,mi,ty,lg):
 W,H=1080,1350;bg=(220,38,38) if ty=="GOAL" else (15,23,42)
 if ty=="NEWS":bg=(0,0,0)
 img=Image.new('RGB',(W,H),color=bg);d=ImageDraw.Draw(img)
 try: fb=ImageFont.truetype("DejaVuSans-Bold.ttf",100);fm=ImageFont.truetype("DejaVuSans-Bold.ttf",45);fs=ImageFont.truetype("DejaVuSans-Bold.ttf",35)
 except: fb=fm=fs=ImageFont.load_default()
 d.rectangle([0,0,W,110],fill=(0,0,0));d.text((W//2,55),lg,font=fs,fill="white",anchor="mm")
 d.rectangle([0,110,W,260],fill="white");d.text((W//2,185),"GOAL ALERT" if ty=="GOAL" else ty,font=fm,fill=bg,anchor="mm")
 d.text((W//2,450),f"{sh}-{sa}",font=fb,fill="white",anchor="mm");d.text((W//2,550),mi,font=fm,fill="yellow",anchor="mm")
 d.text((W//2,750),h[:22].upper(),font=fm,fill="white",anchor="mm");d.text((W//2,900),a[:22].upper(),font=fm,fill="white",anchor="mm")
 d.rectangle([0,1180,W,H],fill=(0,0,0));d.text((W//2,1250),"DE BANA LIVE",font=fs,fill="white",anchor="mm")
 img.save("/tmp/j.jpg","JPEG",quality=90);return "/tmp/j.jpg"
def post(cap,path):
 global posts
 try:
  with open(path,'rb') as f: r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':cap,'access_token':token},timeout=15)
  print(f"POST {r.status_code}");posts+=1
 except Exception as e: print(e)
print(f"START {len(LEAGUES)} leagues")
last={}
for loop in range(140):
 for code,lname in LEAGUES.items():
  try:
   d=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",timeout=6).json()
   for ev in d.get('events',[]):
    comp=ev['competitions'][0];c1,c2=comp['competitors'][0],comp['competitors'][1]
    if c1['homeAway']!='home':c1,c2=c2,c1
    h=c1['team']['displayName'];a=c2['team']['displayName'];sh=c1.get('score','0');sa=c2.get('score','0');st=ev['status']['type']['state'];mid=f"{code}_{ev['id']}";cur=f"{sh}-{sa}";prev=last.get(mid)
    if prev and prev!=cur and st=='in':
     img=make_img(h,a,sh,sa,"LIVE","GOAL",lname);cap=f"{bold('GOOOAL!')} {lname}\n{h} {sh}-{sa} {a}\n#DeBana";post(cap,img)
    if st in ['in','post']: last[mid]=cur
  except: continue
 print(f"Loop {loop} games {len(last)} posted {posts}");time.sleep(2)
if posts==0:
 img=make_img("ALL LEAGUES","LIVE","26","NOW","BREAKING","NEWS","DE BANA")
 cap=f"{bold('BREAKING: Turkish Super Lig + Conference League ADDED!')}\n\nWe now cover 20 competitions: Premier, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Portugal, TURKEY, Scotland, Belgium, Greece, Saudi, MLS, FA Cup, Champions, Europa, CONFERENCE LEAGUE, World Cup Qualifiers, Nations League, AFCON\n\n#DeBana #SuperLig #ConferenceLeague"
 post(cap,img)
