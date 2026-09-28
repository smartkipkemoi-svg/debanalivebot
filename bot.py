import requests, os, time
from PIL import Image, ImageDraw, ImageFont
page_id=os.environ.get('FB_PAGE_ID')
token=os.environ.get('FB_TOKEN')
posts=0
def bold(t):
 a="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
 b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
 try: return t.translate(str.maketrans(a,b))
 except: return t.upper()
LEAGUES={"eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1","tur.1":"TURKISH SUPER LIG","uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE","uefa.conference":"CONFERENCE LEAGUE"}
def make_img(h,a,sh,sa,mn,lg):
 W,H=1080,1350;img=Image.new('RGB',(W,H),color=(220,38,38));d=ImageDraw.Draw(img)
 try: f=ImageFont.truetype("DejaVuSans-Bold.ttf",90)
 except: f=ImageFont.load_default()
 d.text((W//2,600),f"{sh}-{sa}",font=f,fill="white",anchor="mm")
 d.text((W//2,750),f"{h[:20]} vs {a[:20]}",font=f,fill="white",anchor="mm")
 img.save("/tmp/l.jpg","JPEG");return "/tmp/l.jpg"
def post_fb(c,p):
 global posts
 try:
  with open(p,'rb') as f: r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':c,'access_token':token},timeout=15)
  print(f"POSTED {posts}");posts+=1
 except Exception as e: print(e)
last={}
print("START 7m")
for loop in range(140):
 for code,lname in LEAGUES.items():
  try:
   d=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",timeout=6).json()
   for ev in d.get('events',[]):
    comp=ev['competitions'][0];c1=comp['competitors'][0];c2=comp['competitors'][1]
    if c1['homeAway']!='home': c1,c2=c2,c1
    h=c1['team']['displayName'];a=c2['team']['displayName'];sh=c1.get('score','0');sa=c2.get('score','0')
    st=ev['status']['type']['state'];mn=ev['status'].get('displayClock','LIVE')
    mid=str(ev['id'])
    cur=f"{sh}-{sa}";prev=last.get(mid)
    if prev and prev!=cur and st=='in':
     img=make_img(h,a,sh,sa,mn,lname);cap=f"GOAL {lname} {mn} {h} {sh}-{sa} {a} #DeBana";post_fb(cap,img)
    if st in ['in','post']: last[mid]=cur
  except:
   continue
 print(f"Loop {loop}");time.sleep(3)
if posts==0:
 img=make_img("DE BANA","LIVE","LIVE","NOW","LIVE","NEWS");post_fb("BOT IS BACK - Turkish + Conference added! #DeBana",img)
print(f"DONE {posts}")
