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

LEAGUES={
    "eng.1":"PREMIER LEAGUE",
    "esp.1":"LA LIGA",
    "ita.1":"SERIE A",
    "ger.1":"BUNDESLIGA",
    "fra.1":"LIGUE 1",
    "ned.1":"EREDIVISIE",
    "uefa.champions":"UCL",
    "uefa.europa":"UEL",
    "ksa.1":"SAUDI",
    "usa.1":"MLS",
    "caf.champions":"CAF",
    "eng.fa":"FA CUP"
}

LINES=[
    "Defenders on vacation! Who wins this?",
    "VAR drama! Pure chaos!",
    "Rate this goal 1-10! Comment!",
    "Football is BEAUTIFUL! Agree?",
    "Predict final score below!"
]

def make_img(home,away,sh,sa,minute,typ,league):
    W,H=1080,1350
    colors={
        "GOAL":(220,38,38),
        "RED":(120,0,0),
        "LIVE":(15,23,42),
        "HT":(30,58,138),
        "FT":(2,60,2),
        "PEN":(124,58,0),
        "NEWS":(0,0,0)
    }
    bg=colors.get(typ,(15,23,42))
    img=Image.new('RGB',(W,H),color=bg)
    d=ImageDraw.Draw(img)
    try:
        fb=ImageFont.truetype("DejaVuSans-Bold.ttf",110)
        fm=ImageFont.truetype("DejaVuSans-Bold.ttf",50)
        fs=ImageFont.truetype("DejaVuSans-Bold.ttf",38)
        ft=ImageFont.truetype("DejaVuSans.ttf",32)
    except:
        fb=fm=fs=ft=ImageFont.load_default()
    d.rectangle([0,0,W,120],fill=(0,0,0))
    d.text((W//2,60),league,font=fs,fill="white",anchor="mm")
    labels={"GOAL":"GOAL ALERT","RED":"RED CARD","HT":"HALF-TIME","FT":"FULL-TIME","PEN":"PENALTY","LIVE":"LIVE","NEWS":"BREAKING"}
    d.rectangle([0,120,W,280],fill="white")
    d.text((W//2,200),labels.get(typ,"LIVE"),font=fm,fill=bg,anchor="mm")
    d.text((W//2,460),f"{sh} - {sa}",font=fb,fill="white",anchor="mm")
    d.text((W//2,570),f"{minute} {typ}",font=fm,fill="yellow",anchor="mm")
    d.text((W//2,760),home.upper()[:24],font=fm,fill="white",anchor="mm")
    d.text((W//2,830),"VS",font=ft,fill=(200,200,200),anchor="mm")
    d.text((W//2,900),away.upper()[:24],font=fm,fill="white",anchor="mm")
    d.rectangle([0,1160,W,H],fill=(0,0,0))
    d.text((W//2,1210),"DE BANA LIVE - ALL LEAGUES",font=fs,fill="white",anchor="mm")
    d.text((W//2,1270),"Goals Red Pen HT FT Transfers",font=ft,fill=(150,150,150),anchor="mm")
    img.save("/tmp/live.jpg","JPEG",quality=95)
    return "/tmp/live.jpg"

def post(cap,path):
    try:
        with open(path,'rb') as f:
            r=requests.post(f"https://graph.facebook.com/{page_id}/photos",files={'source':f},data={'caption':cap,'access_token':token},timeout=15)
        print(r.text[:300])
    except Exception as e:
        print(f"post err {e}")

last_score={}
last_detail={}
print(f"START {len(LEAGUES)} leagues - 140 loops x 2 sec")

for loop in range(140):
    for code,lname in LEAGUES.items():
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
            data=requests.get(url,timeout=7).json()
            for ev in data.get('events',[]):
                comp=ev['competitions'][0]
                c1,c2=comp['competitors'][0],comp['competitors'][1]
                if c1['homeAway']!='home':
                    c1,c2=c2,c1
                home=c1['team']['displayName']
                away=c2['team']['displayName']
                sh=c1.get('score','0')
                sa=c2.get('score','0')
                state=ev['status']['type']['state']
                detail=ev['status']['type'].get('detail','')
                minute=ev['status'].get('displayClock','LIVE')
                mid=f"{code}_{ev['id']}"
                cur=f"{sh}-{sa}"
                prev=last_score.get(mid)

                if prev and prev!=cur and state=='in':
                    img=make_img(home,away,sh,sa,minute,"GOAL",lname)
                    scorer=home if sh!=prev.split('-')[0] else away
                    cap=f"{bold('GOOOAL!!!')} | {lname}\n\n{bold(minute)} | {bold(home)} {sh}-{sa} {bold(away)}\n\n{bold(scorer.upper()+' SCORES!')} {random.choice(LINES)}\n\n{bold('Predict final score below!')}\n\n#DeBana #GoalAlert"
                    post(cap,img)

                if detail!=last_detail.get(mid):
                    if "Halftime" in detail:
                        img=make_img(home,away,sh,sa,"HALF-TIME","HT",lname)
                        cap=f"{bold('HALF-TIME')} | {lname}\n\n{bold(home)} {sh}-{sa} {bold(away)}\n\nFirst half thoughts? \n\n#DeBana"
                        post(cap,img)
                    if state=='post' and last_detail.get(mid,'')!='post' and last_detail.get(mid,'')!='':
                        img=make_img(home,away,sh,sa,"FULL-TIME","FT",lname)
                        cap=f"{bold('FULL-TIME')} | {lname}\n\n{bold(home)} {sh}-{sa} {bold(away)}\n\nRate this match 1-10 \n\n#DeBana #FT"
                        post(cap,img)

                if state in ['in','post']:
                    last_score[mid]=cur
                last_detail[mid]=detail if state!='in' else last_detail.get(mid,'')
        except:
            continue
    print(f"Loop {loop} -> {len(last_score)} games")
    time.sleep(2)

if not last_score:
    img=make_img("TRANSFER","WINDOW","NEWS","LIVE","BREAKING","NEWS","TRANSFER CENTER")
    news=random.choice([
        f"{bold('BREAKING:')} 95M striker to Man Utd! Here we go?",
        f"{bold('DONE DEAL:')} Chelsea hijack Arsenal target!",
        f"{bold('INJURY:')} Star out 3 weeks before UCL final!",
        f"{bold('LINEUP:')} Shocking XI leaked! Fans fuming!"
    ])
    cap=f"{news}\n\n{random.choice(LINES)}\n\nYES or NO? Comment \n\n#DeBana"
    post(cap,img)
