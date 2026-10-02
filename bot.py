import requests, json, os, time, random, concurrent.futures

FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN')
POSTED_FILE = "posted.json"
SLEEP_LIVE = 35
SLEEP_QUIET = 120

LEAGUES = [
    "eng.1","eng.2","eng.fa","eng.league_cup",
    "esp.1","esp.2","esp.copa_del_rey",
    "ger.1","ita.1","fra.1","ned.1","por.1","bel.1","tur.1","sco.1","gre.1","sui.1",
    "uefa.champions","uefa.europa","uefa.europa_conference","uefa.super_cup","uefa.nations",
    "usa.1","bra.1","arg.1","conmebol.libertadores","conmebol.sudamericana",
    "ken.1","rsa.1","egy.1","caf.champions","caf.confed","caf.nations",
    "fifa.world","fifa.world.u20","fifa.friendly","uefa.euro","concacaf.gold","afc.asian"
]

MEMES = [
    "When you said you'll sleep early but UCL is at 10PM 😂\nWho else is still awake?",
    "KPL defender seeing Gor Mahia counter attack 🏃‍♂️💨\nPray for him!",
    "Man Utd fans: 'Next season is ours' - Every season since 2013 😅",
    "That friend who says football is boring 🙄\nWe don't talk to him.",
    "VAR in KPL = Vibes And Random decisions 🤣",
    "When you bet Under 2.5 and it's 2-2 at 90' 😭💔",
]

def load_posted():
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE,'r') as f:
                data=json.load(f)
                return data if isinstance(data,list) else []
    except Exception as e:
        print(f"load error {e}")
    return []

def save_posted(p):
    if len(p)>1500: p=p[-1500:]
    try:
        with open(POSTED_FILE,'w') as f:
            json.dump(p,f)
        print(f"SAVED {len(p)}")
    except Exception as e:
        print(f"save error {e}")

def post_fb(msg):
    if not FB_PAGE_ID or not FB_TOKEN:
        print(f"NO TOKEN: {msg[:80]}")
        return False
    try:
        r=requests.post(f"https://graph.facebook.com/{FB_PAGE_ID}/feed",
                        data={"message":msg,"access_token":FB_TOKEN}, timeout=15)
        print(f"FB {r.status_code}: {msg[:80]}")
        return r.status_code==200
    except Exception as e:
        print(f"FB ERR {e}")
        return False

def fetch_league(lg):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard"
        r=requests.get(url, timeout=10)
        if r.status_code!=200: return []
        out=[]
        for ev in r.json().get('events',[]):
            ev['_lg']=lg
            out.append(ev)
        return out
    except:
        return []

def fetch_news():
    news=[]
    for lg in ["eng.1","esp.1","ken.1","uefa.champions"]:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/news"
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                for a in r.json().get('articles',[])[:2]:
                    news.append(a)
        except: pass
    return news

posted=load_posted()
last_news=0
last_meme=0
print(f"De Bana BOT STARTED - {len(posted)} posted - {len(LEAGUES)} leagues")

while True:
    try:
        games=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            for res in ex.map(fetch_league, LEAGUES):
                games.extend(res)

        live_now=False
        for ev in games:
            gid=ev.get('id')
            state=ev.get('status',{}).get('type',{}).get('state','')
            comp=ev.get('competitions',[{}])[0]
            teams=comp.get('competitors',[])
            if len(teams)<2: continue
            home=teams[0]['team']['displayName']
            away=teams[1]['team']['displayName']
            hs=teams[0].get('score','0')
            as_=teams[1].get('score','0')
            lg=ev.get('_lg','')

            # FT - post once then block
            if state=='post':
                pid=f"{gid}_FT_{hs}-{as_}"
                if pid not in posted:
                    msg=f"🔚 FULL TIME: {home} {hs}-{as_} {away}\n\nWhat a game! Thoughts? 👇\n#FT #{lg} #DeBana"
                    if post_fb(msg):
                        posted.append(pid); save_posted(posted)
                continue

            if state=='in': live_now=True

            # LINEUP
            if state=='pre' and comp.get('lineups'):
                pid=f"{gid}_LINEUP"
                if pid not in posted:
                    msg=f"📋 LINEUP DROP
