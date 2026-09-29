import requests, json, os, time, random
from datetime import datetime

FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN') or os.environ.get('FB_PAGE_TOKEN')
POSTED_FILE = "posted.json"
RUN_TIME = 270
SLEEP_TIME = 10

# === ALL LEAGUES IN THE WORLD ===
LEAGUES = [
    "eng.1","esp.1","ger.1","ita.1","fra.1","ned.1","por.1","eng.2","eng.3",
    "usa.1","mex.1","bra.1","arg.1",
    "uefa.champions","uefa.europa","uefa.europa.conf",
    "fifa.world","fifa.worldq","uefa.nations","conmebol.copa","caf.nations","afc.asian",
    "eng.fa","esp.copa_del_rey","ger.dfb_pokal","ita.coppa_italia"
]

# Funny headline templates
FUNNY_GOAL = [
    "𝐁𝐎𝐎𝐌! {player} just broke the net! 💥",
    "𝐆𝐎𝐀𝐋𝐀𝐙𝐎! {player} said 'hold my beer' 🍺⚽",
    "𝐎𝐌𝐆! {player} just made the keeper look silly 🤣",
    "𝐁𝐀𝐍𝐆𝐄𝐑! {player} with a rocket 🚀",
    "𝐔𝐍𝐁𝐄𝐋𝐈𝐄𝐕𝐀𝐁𝐋𝐄! {player} cooks! 👨‍🍳⚽"
]
FUNNY_RED = ["𝐒𝐄𝐍𝐓 𝐎𝐅! {player} took the early shower 🚿🟥", "𝐁𝐘𝐄 𝐁𝐘𝐄! {player} sees RED! 😳"]
FUNNY_FT = ["𝐈𝐓'𝐒 𝐎𝐕𝐄𝐑! {home} {hs}-{as} {away} - What a drama! 🍿", "𝐅𝐔𝐋𝐋 𝐓𝐈𝐌𝐄! {home} cooked {away}! 🔥"]

def to_bold(text):
    # Facebook bold using unicode
    return f"𝐁{ text[1:].upper() }" if text else text

def load_posted():
    if not os.path.exists(POSTED_FILE): return []
    try:
        with open(POSTED_FILE,'r') as f:
            d=json.load(f)
            return d if isinstance(d,list) else []
    except: return []

def save_posted(p):
    if len(p)>1000: p=p[-1000:]
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

def get_all_games():
    games=[]
    for league in LEAGUES:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
            if r.status_code!=200: continue
            for ev in r.json().get('events',[]):
                state=ev.get('status',{}).get('type',{}).get('state','')
                if state in ['in','pre','post']:
                    ev['_league_name']=ev.get('competitions',[{}])[0].get('competition',{}).get('name',league)
                    games.append(ev)
        except: continue
    return games

def get_lineup(game_id):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/summary?event={game_id}"
        r=requests.get(url, timeout=8)
        if r.status_code!=200: return None
        data=r.json()
        lineups=data.get('rosters',[]) or data.get('lineups',[])
        if not lineups: return None
        txt="📋 𝐋𝐈𝐍𝐄𝐔𝐏𝐒\n\n"
        for team in lineups[:2]:
            tname=team.get('team',{}).get('displayName','Team')
            txt+=f"𝐁{ tname }:\n"
            for p in team.get('roster',[])[:11]:
                txt+=f"• {p.get('athlete',{}).get('displayName','')} \n"
            txt+="\n"
        return txt
    except: return None

def get_breaking_news():
    try:
        # ESPN Soccer News
        url="https://site.api.espn.com/apis/site/v2/sports/soccer/news?limit=10"
        r=requests.get(url, timeout=8)
        if r.status_code!=200: return []
        arts=r.json().get('articles',[])
        news=[]
        for a in arts[:3]:
            title=a.get('headline','')
            if any(k in title.lower() for k in ['transfer','breaking','deal','agree','sign','injury','sack']):
                news.append({"title":title, "desc":a.get('description','')[:150]})
        return news
    except: return []

def get_teams(comp):
    try:
        h=[c for c in comp['competitors'] if c['homeAway']=='home'][0]
        a=[c for c in comp['competitors'] if c['homeAway']=='away'][0]
        return h,a
    except:
        return comp['competitors'][0], comp['competitors'][1] if len(comp['competitors'])>1 else comp['competitors'][0]

print(f"ULTIMATE BOT START - {RUN_TIME}s")
posted=load_posted()
print(f"History {len(posted)}")
start=time.time()
checks=0

# Post breaking news once per run
news_checked=False

while time.time()-start < RUN_TIME:
    checks+=1
    print(f"\n--- CHECK {checks} {datetime.now().strftime('%H:%M:%S')} ---")
    try:
        # 1. BREAKING NEWS / TRANSFERS - once every run
        if not news_checked:
            news=get_breaking_news()
            for n in news:
                pid=f"NEWS_{n['title'][:40]}"
                if pid not in posted:
                    msg=f"🚨 𝐁𝐑𝐄𝐀𝐊𝐈𝐍𝐆 𝐍𝐄𝐖𝐒 🚨\n\n𝐁{ n['title'].upper() }\n\n{n['desc']}\n\n#Transfer #BreakingNews #Football"
                    if post_fb(msg):
                        posted.append(pid); save_posted(posted)
                        print("Posted news")
            news_checked=True

        games=get_all_games()
        print(f"{len(games)} games")
        for ev in games:
            gid=ev.get('id','')
            comp=ev.get('competitions',[{}])[0]
            if not comp: continue
            home,away=get_teams(comp)
            league=comp.get('competition',{}).get('name',ev.get('_league_name','Football'))
            state=comp.get('status',{}).get('type',{}).get('state','')
            detail=comp.get('status',{}).get('type',{}).get('detail','')
            clock=comp.get('status',{}).get('displayClock','0')
            h_name=home['team']['displayName']
            a_name=away['team']['displayName']
            hs=home.get('score','0')
            as_=away.get('score','0')

            # LINEUPS - 1 hour before match
            if state=='pre':
                pid=f"{gid}_LINEUP"
                if pid not in posted and 'lineup' not in detail.lower():
                    # Check if match starts in <70 mins
                    lineup_txt=get_lineup(gid)
                    if lineup_txt:
                        msg=f"{lineup_txt}\n🏆 {league}\n⏰ Kickoff soon!\n\n#Lineup #{h_name.replace(' ','')} #{a_name.replace(' ','')}"
                        if post_fb(msg):
                            posted.append(pid); save_posted(posted)

            # KICKOFF
            if state=='in' and comp.get('status',{}).get('period',0)==1:
                try:
                    mins=int(''.join(filter(str.isdigit, clock.split(':')[0]))) if clock else 0
                    if mins<=2:
                        pid=f"{gid}_KICK"
                        if pid not in posted:
                            msg=f"▶️ 𝐊𝐈𝐂𝐊 𝐎𝐅𝐅!\n\n𝐁{ h_name.upper() } vs { a_name.upper() }\n🏆 {league}\n\nWho's winning this one? 👇\n\n#LiveNow"
                            if post_fb(msg):
                                posted.append(pid); save_posted(posted)
                except: pass

            # GOALS & RED CARDS
            for d in comp.get('details',[]):
                if not isinstance(d,dict): continue
                txt_low=d.get('text','').lower()
                t_low=str(d.get('type','')).lower()
                is_goal='goal' in t_low or 'goal' in txt_low or d.get('scoringPlay',False)
                is_red='red card' in txt_low

                if not (is_goal or is_red): continue

                pid=f"{gid}_{d.get('id','')}_{hs}-{as_}_{d.get('text','')[:20]}"
                if pid in posted: continue

                player=d.get('athletesInvolved',[{}])[0].get('displayName','') if d.get('athletesInvolved') else d.get('text','').split('-')[0][:25]
                clock_d=d.get('clock',{}).get('displayValue','') if isinstance(d.get('clock'),dict) else str(d.get('clock',''))

                if is_goal:
                    template=random.choice(FUNNY_GOAL).format(player=player)
                    msg=f"{template}\n\n𝐁{ h_name } {hs} - {as_} {a_name }\n⏰ {clock_d}' | 🏆 {league}\n\n#Goal #LiveScore #Football"
                else:
                    template=random.choice(FUNNY_RED).format(player=player)
                    msg=f"{template}\n\n𝐁{ h_name } {hs} - {as_} {a_name }\n⏰ {clock_d}' | 🏆 {league}\n\n#RedCard"

                print(f"NEW {pid}")
                if post_fb(msg):
                    posted.append(pid); save_posted(posted); time.sleep(2)

            # HALFTIME
            if 'halftime' in detail.lower():
                pid=f"{gid}_HT_{hs}-{as_}"
                if pid not in posted:
                    msg=f"⏸️ 𝐇𝐀𝐋𝐅𝐓𝐈𝐌𝐄\n\n𝐁{ h_name } {hs} - {as_} {a_name }\n🏆 {league}\n\nFirst half thoughts? 👇\n#HT"
                    if post_fb(msg):
                        posted.append(pid); save_posted(posted)

            # FULLTIME
            if state=='post':
                pid=f"{gid}_FT_{hs}-{as_}"
                if pid not in posted:
                    template=random.choice(FUNNY_FT).format(home=h_name, hs=hs, as=as_, away=a_name)
                    msg=f"{template}\n\n🏆 {league}\n\n#FullTime #Result"
                    if post_fb(msg):
                        posted.append(pid); save_posted(posted)

    except Exception as e:
        print(f"ERR {e}")

    time.sleep(SLEEP_TIME)
    if time.time()-start >= RUN_TIME: break

print(f"FINISHED {checks} checks")
