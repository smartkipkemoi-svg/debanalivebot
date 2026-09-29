import requests, json, os, time, random
from datetime import datetime

FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN') or os.environ.get('FB_PAGE_TOKEN')
POSTED_FILE = "posted.json"
RUN_TIME = 270
SLEEP_TIME = 10

LEAGUES = ["eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions","uefa.europa","fifa.worldq","usa.1","mex.1","bra.1"]

FUNNY_GOAL = [
    "BOOM! {player} just broke the net!",
    "GOALAZO! {player} with a banger!",
    "OMG! {player} made keeper look silly!",
    "ROCKET! {player} scores!",
    "UNBELIEVABLE! {player} cooks!"
]

def load_posted():
    if not os.path.exists(POSTED_FILE): return []
    try:
        with open(POSTED_FILE,'r') as f:
            d=json.load(f)
            return d if isinstance(d,list) else []
    except: return []

def save_posted(p):
    if len(p)>800: p=p[-800:]
    with open(POSTED_FILE,'w') as f: json.dump(p,f)

def post_fb(msg):
    if not FB_PAGE_ID or not FB_TOKEN:
        print(f"NO SECRET - {msg[:100]}")
        return False
    try:
        r=requests.post(f"https://graph.facebook.com/{FB_PAGE_ID}/feed", data={"message":msg,"access_token":FB_TOKEN}, timeout=15)
        print(f"FB {r.status_code} {r.text[:200]}")
        return r.status_code==200
    except Exception as e:
        print(f"FB ERR {e}")
        return False

def get_games():
    games=[]
    for league in LEAGUES:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
            if r.status_code!=200: continue
            for ev in r.json().get('events',[]):
                if ev.get('status',{}).get('type',{}).get('state','') in ['in','pre','post']:
                    ev['_league']=league
                    games.append(ev)
        except: continue
    return games

def get_teams(comp):
    try:
        h=[c for c in comp['competitors'] if c['homeAway']=='home'][0]
        a=[c for c in comp['competitors'] if c['homeAway']=='away'][0]
        return h,a
    except:
        return comp['competitors'][0], comp['competitors'][1] if len(comp['competitors'])>1 else comp['competitors'][0]

print(f"START - {RUN_TIME}s run")
posted=load_posted()
start=time.time()
checks=0

while time.time()-start < RUN_TIME:
    checks+=1
    print(f"CHECK {checks} {datetime.now().strftime('%H:%M:%S')}")
    try:
        games=get_games()
        print(f"{len(games)} games found")
        for ev in games:
            gid=ev.get('id','')
            comp=ev.get('competitions',[{}])[0]
            if not comp: continue
            home,away=get_teams(comp)
            league=comp.get('competition',{}).get('name',ev.get('_league','Football'))
            state=comp.get('status',{}).get('type',{}).get('state','')
            detail=comp.get('status',{}).get('type',{}).get('detail','').lower()
            h_name=home['team']['displayName']
            a_name=away['team']['displayName']
            hs=home.get('score','0')
            aws=away.get('score','0')

            for d in comp.get('details',[]):
                if not isinstance(d,dict): continue
                txt=d.get('text','').lower()
                is_goal='goal' in str(d.get('type','')).lower() or 'goal' in txt or d.get('scoringPlay',False)
                is_red='red card' in txt
                if not (is_goal or is_red): continue
                pid=f"{gid}_{d.get('id','')}_{hs}-{aws}_{d.get('text','')[:20]}"
                if pid in posted: continue
                player=d.get('athletesInvolved',[{}])[0].get('displayName','') if d.get('athletesInvolved') else "GOAL"
                if not player: player="GOAL"
                if is_goal:
                    template=random.choice(FUNNY_GOAL).format(player=player)
                    msg=f"{template}\n\n{h_name} {hs} - {aws} {a_name}\nLeague: {league}\n\n#LiveScore #Goal"
                else:
                    msg=f"RED CARD! {player} sent off!\n\n{h_name} {hs} - {aws} {a_name}\n{league}"
                print(f"NEW EVENT {pid}")
                if post_fb(msg):
                    posted.append(pid)
                    save_posted(posted)
                    time.sleep(2)

            if 'halftime' in detail:
                pid=f"{gid}_HT_{hs}-{aws}"
                if pid not in posted:
                    msg=f"HALFTIME\n\n{h_name} {hs} - {aws} {a_name}\n{league}\n\n#HT"
                    if post_fb(msg):
                        posted.append(pid)
                        save_posted(posted)

            if state=='post' and 'final' in detail:
                pid=f"{gid}_FT_{hs}-{aws}"
                if pid not in posted:
                    msg=f"FULL TIME\n\n{h_name} {hs} - {aws} {a_name}\n{league}\n\n#FT #Result"
                    if post_fb(msg):
                        posted.append(pid)
                        save_posted(posted)
    except Exception as e:
        print(f"LOOP ERR {e}")

    time.sleep(SLEEP_TIME)
    if time.time()-start >= RUN_TIME: break

print(f"DONE {checks} checks total")
