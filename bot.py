import requests, json, os, time, concurrent.futures, random, collections
from datetime import datetime, timezone
try:
    import pytz
except ImportError:
    pytz = None
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN')
POSTED_FILE = "posted.json"
SLEEP_LIVE_KPL = 5
SLEEP_LIVE = 10
SLEEP_QUIET = 120
POST_QUEUE = collections.deque()
LAST_POST_TIME = 0
MIN_POST_GAP = 90
LEAGUES = ["eng.1","eng.2","eng.fa","eng.league_cup","esp.1","esp.2","esp.copa_del_rey","ger.1","ita.1","fra.1","ned.1","por.1","bel.1","tur.1","sco.1","gre.1","sui.1","uefa.champions","uefa.europa","uefa.europa_conference","uefa.super_cup","uefa.nations","usa.1","bra.1","arg.1","conmebol.libertadores","conmebol.sudamericana","ken.1","rsa.1","egy.1","caf.champions","caf.confed","caf.nations","fifa.world","fifa.world.u20","fifa.friendly","uefa.euro","concacaf.gold","afc.asian","nga.1","tza.1","ng.1","tz.1","uga.1","rwa.1"]
def to_bold(text):
    def _c(ch):
        if 'A' <= ch <= 'Z': return chr(0x1D5D4 + ord(ch) - 65)
        if 'a' <= ch <= 'z': return chr(0x1D5EE + ord(ch) - 97)
        if '0' <= ch <= '9': return chr(0x1D7EC + ord(ch) - 48)
        return ch
    return "".join(_c(c) for c in text)
LEAGUE_FLAGS = {"eng.1":"EPL","eng.2":"EPL","eng.fa":"FA Cup","eng.league_cup":"EFL Cup","esp.1":"LaLiga","esp.2":"LaLiga2","ger.1":"Bundesliga","ita.1":"Serie A","fra.1":"Ligue 1","ken.1":"KPL","rsa.1":"PSL","egy.1":"EGY","nga.1":"NPFL","tza.1":"NBC PL","ng.1":"NPFL","tz.1":"NBC","uga.1":"UPL","rwa.1":"RPL","uefa.champions":"UCL","uefa.europa":"UEL","uefa.europa_conference":"UECL","caf.champions":"CAF"}
BRAND = "\U0001f3af"
END = "\U0001f51a"
CLOCK = "\u23f0"
CLIP = "\U0001f4cb"
PAUSE = "\u23f8\ufe0f"
SIREN = "\U0001f6a8"
WARN = "\u26a0\ufe0f"
SOCCER = "\u26bd"
FIRE = "\U0001f525"
MOBILE = "\U0001f4f2"
CHAT = "\U0001f4ac"
DOWN = "\U0001f447"
def get_match_photo(lg, gid, is_kpl=False):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/" + lg + "/summary?event=" + gid
        r = requests.get(url, timeout=10).json()
        articles = r.get('news',{}).get('articles',[]) or r.get('headlines',[])
        for art in articles[:3]:
            imgs = art.get('images',[])
            if imgs and imgs[0].get('url'): return imgs[0]['url']
        return None
    except Exception as e:
        print("photo err " + str(e))
        return None
def get_match_stats(comp):
    try:
        stats = comp.get('statistics',[]) or comp.get('stats',[])
        out = ""
        for st in stats[:2]:
            s = st.get('stats',[]) if isinstance(st, dict) else []
            for item in s:
                name = item.get('name','').lower()
                if 'possession' in name or 'shots' in name: out = out + " " + item.get('displayValue','') + " " + name + ","
        if out: return "\n" + CHART + " Stats:" + out[:80]
        return ""
    except: return ""
SHENG_STARTS = ["Gooool!", "Wamefunga!", "Wamepasua net!", "Moto!", "Chuma!", "Hatari!", "Bazuu!", "Woi!"]
SHENG_MIDS = ["wamechapa", "wamefunga", "wameweka ndani", "wameingiza", "amewasha", "amepasua", "amechoma"]
SHENG_ENDS = ["mambo imechemka", "hii game ni moto", "wameamua leo", "hakuna mchezo", "form ni kali", "wamezima", "KPL ni yetu!"]
EMOJIS = ["\U0001f525", "\U000026BD", "\U0001f4a5", "\U0001f680", "\U0001f4a8", "\U0001f631", "\U000026A1"]
SHENG_EXTRAS = ["KPL ni yetu!", "Hii ndio yetu!", "Ligi yetu tamu!", "Tuko ndani!", "Bana wamezima!"]
def kpl_sheng_caption(team, home, away, minute, player="", flag="KPL"):
    s = random.choice(SHENG_STARTS); m = random.choice(SHENG_MIDS); e = random.choice(SHENG_ENDS)
    emoji = random.choice(EMOJIS); extra = random.choice(SHENG_EXTRAS)
    score_str = home + "-" + away; bold_score = to_bold(score_str); bold_team = to_bold(team)
    bold_s = to_bold(s); bold_min = to_bold(str(minute))
    player_txt = ""
    if player: player_txt = " - " + to_bold(player) + " amefanya!"
    t1 = BRAND + " " + flag + " | " + bold_s + " " + bold_team + " " + m + " " + emoji + " " + bold_score + " (" + str(minute) + "') " + player_txt + "\n" + e + " | " + extra + "\n\n" + MOBILE + " Track code yako hapa De Bana! Weka bet code yako comment " + DOWN + "\n#DeBana #FKFPL #KPLLive"
    t2 = BRAND + " " + flag + " | " + emoji + " Dakika " + bold_min + "' - " + bold_team + " " + m + " goli! " + bold_score + " " + player_txt + "\n" + e + " - " + extra + "\n\n" + CHAT + " Code yako iko aje? Drop kwa comment tuku-trackie!\n#DeBana"
    t3 = BRAND + " " + flag + " | " + bold_team + " " + m + "! " + s + " " + bold_score + " min " + str(minute) + "' " + emoji + "\n" + player + " " + e + "\n\n" + FIRE + " " + extra + " | Track bet yako na De Bana!\n#FKFPL"
    return random.choice([t1, t2, t3])
def load_posted():
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE,'r') as f:
                data=json.load(f)
                return data if isinstance(data,list) else []
    except Exception as e: print("load error " + str(e))
    return []
def save_posted(p):
    if len(p)>2000: p=p[-2000:]
    try:
        tmp = POSTED_FILE + ".tmp"
        with open(tmp,'w') as f: json.dump(p,f)
        os.replace(tmp, POSTED_FILE)
        print("SAVED " + str(len(p)))
    except Exception as e: print("save error " + str(e))
def post_fb(msg, is_kpl=False, lg="", gid="", teams=[]):
    global LAST_POST_TIME
    now = time.time()
    if now - LAST_POST_TIME < MIN_POST_GAP:
        wait = MIN_POST_GAP - (now - LAST_POST_TIME)
        print("RATE LIMIT: waiting " + str(int(wait)) + "s")
        time.sleep(wait)
    if not FB_PAGE_ID or not FB_TOKEN:
        print("NO TOKEN: " + msg[:80])
        return False
    if not is_kpl and random.random() < 0.3: time.sleep(random.randint(15,25))
    photo_url = None
    if gid and lg:
        try: photo_url = get_match_photo(lg, gid, is_kpl)
        except: photo_url = None
        if not is_kpl and photo_url and random.random() < 0.6: photo_url = None
    try:
        for attempt in range(3):
            try:
                if photo_url:
                    r=requests.post("https://graph.facebook.com/" + FB_PAGE_ID + "/photos", data={"caption":msg, "url":photo_url, "access_token":FB_TOKEN}, timeout=20)
                else:
                    logo_url = None
                         if teams and len(teams)>=2:
                             logo_url = "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800"
                    if logo_url and random.random() < 0.7:
                        r=requests.post("https://graph.facebook.com/" + FB_PAGE_ID + "/photos", data={"caption":msg, "url":logo_url, "access_token":FB_TOKEN}, timeout=20)
                    else:
                        r=requests.post("https://graph.facebook.com/" + FB_PAGE_ID + "/feed", data={"message":msg,"access_token":FB_TOKEN}, timeout=15)
                print("FB " + str(r.status_code) + " attempt " + str(attempt) + ": " + msg[:70])
                if r.status_code==200:
                    LAST_POST_TIME = time.time()
                    try:
                        post_id = r.json().get('id') or r.json().get('post_id')
                        if post_id:
                            comment_msg = POINT + " Follow De Bana for fastest goals! " + ZAP + " Turn ON notifications " + BELL + " | Drop your bet code " + DOWN + " tunatrack live!"
                            if is_kpl: comment_msg = POINT + " Follow De Bana! Fastest KPL updates hapa! " + BELL + " Weka bet code yako hapa tuku-trackie! #DeBana"
                            requests.post("https://graph.facebook.com/" + post_id + "/comments", data={"message":comment_msg,"access_token":FB_TOKEN}, timeout=10)
                    except Exception as e: print("comment err " + str(e))
                    return True
                elif r.status_code == 429:
                    print("FB RATE LIMITED - sleeping 5 min")
                    time.sleep(300)
                    continue
                else: time.sleep(5)
            except Exception as e:
                print("FB attempt " + str(attempt) + " err " + str(e))
                time.sleep(5)
        return False
    except Exception as e:
        print("FB ERR " + str(e))
        return False
def fetch_league(lg):
    try:
        for _ in range(2):
            try:
                url="https://site.api.espn.com/apis/site/v2/sports/soccer/" + lg + "/scoreboard"
                r=requests.get(url, timeout=15)
                if r.status_code!=200: return []
                out=[]
                for ev in r.json().get('events',[]):
                    ev['_lg']=lg
                    out.append(ev)
                return out
            except: time.sleep(1)
        return []
    except: return []
def fetch_news():
    news=[]
    for lg in ["eng.1","esp.1","ken.1","uefa.champions"]:
        try:
            url="https://site.api.espn.com/apis/site/v2/sports/soccer/" + lg + "/news"
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                for a in r.json().get('articles',[])[:2]: news.append(a)
        except: pass
    return news
posted=load_posted()
last_news=0
last_controversy = time.time() - 10000
print("De Bana BOT v100 STARTED - " + str(len(posted)) + " posted")
while True:
    try:
        games=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            for res in ex.map(fetch_league, LEAGUES): games.extend(res)
        live_now=False; kpl_live=False
        for ev in games:
            gid=ev.get('id')
            state=ev.get('status',{}).get('type',{}).get('state','')
            comp=ev.get('competitions',[{}])[0]
            teams=comp.get('competitors',[])
            if len(teams)<2: continue
            home=teams[0]['team']['displayName']; away=teams[1]['team']['displayName']
            hs=teams[0].get('score','0'); as_=teams[1].get('score','0')
            lg=ev.get('_lg',''); is_kpl = lg in ["ken.1","KE.1"] or "kenya" in lg.lower()
            flag = LEAGUE_FLAGS.get(lg, "#" + lg)
            if state=='post':
                pid=gid + "_FT_" + hs + "-" + as_
                if pid not in posted:
                    stats_extra = get_match_stats(comp)
                    if is_kpl: msg=BRAND + " " + flag + " | " + END + " " + to_bold('FT hapa KPL!') + " " + to_bold(home) + " " + to_bold(hs + "-" + as_) + " " + to_bold(away) + ". " + random.choice(SHENG_ENDS) + "! " + random.choice(SHENG_EXTRAS) + " " + FIRE + stats_extra + "\n\nCode yako iliingia? Drop comment " + DOWN + " Wamebaki na point ngapi?\n#FT #FKFPL #DeBana"
                    else: msg=BRAND + " " + flag + " | " + END + " " + to_bold('FULL TIME:') + " " + to_bold(home) + " " + to_bold(hs + "-" + as_) + " " + to_bold(away) + stats_extra + "\n\nWhat a game! Thoughts? " + DOWN + " Who was MOTM?\n#FT #" + lg + " #DeBana"
                    if post_fb(msg, is_kpl, lg, gid, teams):
                        posted.append(pid); save_posted(posted)
                continue
            if state=='in': live_now=True
            if is_kpl and state=='in': kpl_live=True
            if state=='pre':
                try:
                    from dateutil import parser
                    dt = parser.isoparse(ev.get('date'))
                    mins_to_kick = (dt - datetime.now(timezone.utc)).total_seconds()/60
                    if 110 < mins_to_kick < 130:
                        pid=gid + "_PREVIEW"
                        if pid not in posted:
                            try: eat_str = get_eat_time(ev.get('date'))
                            except: eat_str = "Tonight"
                            msg=BRAND + " " + flag + " | " + CLOCK + " " + to_bold('COMING UP') + " - " + to_bold(home) + " vs " + to_bold(away) + " | " + eat_str + "\n\nH2H? Form? Nani atashinda? Drop prediction " + DOWN + "\nOdds? Bet code? Tukutrack!\n#Preview #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                    if 5 < mins_to_kick < 35 and is_kpl:
                        pid=gid + "_LINEUP_FALLBACK"
                        if pid not in posted and not comp.get('lineups'):
                            est = eat_str if 'eat_str' in locals() else ""
                            msg=BRAND + " " + flag + " | " + CLOCK + " " + to_bold('LINEUP SOON') + " - " + to_bold(home) + " vs " + to_bold(away) + " | " + est + "\n\nNani a-anze leo? Who should start? " + DOWN + " Predict XI!\n#KPL #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                except: pass
            if state=='pre' and comp.get('lineups'):
                pid=gid + "_LINEUP"
                if pid not in posted:
                    extra_info = get_lineup_extra(comp)
                    msg=BRAND + " " + flag + " | " + CLIP + " " + to_bold('LINEUP DROP:') + " " + to_bold(home) + " vs " + to_bold(away) + extra_info + "\n\nStarting XIs are out! Who wins? " + EYE + " Predict score " + DOWN + "\n#Lineup #BuildUp #DeBana"
                    if post_fb(msg, is_kpl, lg, gid, teams):
                        posted.append(pid); save_posted(posted)
                status_detail = comp.get('status',{}).get('type',{}).get('detail','').lower()
                if 'half' in status_detail:
                    pid=gid + "_HT_" + hs + "-" + as_
                    if pid not in posted:
                        if is_kpl: msg=BRAND + " " + flag + " | " + PAUSE + " " + to_bold('HT hapa KPL!') + " " + to_bold(home) + " " + to_bold(hs + "-" + as_) + " " + to_bold(away) + " - Mapumziko! " + random.choice(SHENG_ENDS) + "\n\nSecond half nani atafunga? " + DOWN + "\n#HT #DeBana"
                        else: msg=BRAND + " " + flag + " | " + PAUSE + " " + to_bold('HALF TIME:') + " " + to_bold(home) + " " + to_bold(hs + "-" + as_) + " " + to_bold(away) + "\n\nSecond half nani atafunga? " + DOWN + " Drop prediction!\n#HT #DeBana"
                        if post_fb(msg, is_kpl, lg, gid, teams):
                            posted.append(pid); save_posted(posted)
                for det in comp.get('details',[]):
                    if not isinstance(det, dict): continue
                    dtype = str(det.get('type','')).lower()
                    minute=det.get('clock',{}).get('displayValue','')
                    player=det.get('athletesInvolved',[{}])[0].get('displayName','') if det.get('athletesInvolved') else ''
                    det_id = det.get('id') or (minute + "_" + player + "_" + dtype)
                    if 'red' in dtype or 'ejection' in dtype:
                        pid=gid + "_RED_" + det_id
                        if pid not in posted:
                            msg=BRAND + " " + flag + " | " + SIREN + " " + to_bold('RED CARD') + " " + minute + "' - " + to_bold(player) + " (" + home + " vs " + away + ") OFF!\n\nGame imebadilika! " + EYE + " Score itaisha aje?\n#RedCard #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                            continue
                    if 'penalty' in dtype or 'pen' in dtype:
                        pid=gid + "_PEN_" + det_id
                        if pid not in posted:
                            msg=BRAND + " " + flag + " | " + WARN + " " + to_bold('PENALTY') + " " + minute + "' - " + to_bold(home) + " vs " + to_bold(away) + " - " + player + "\n\nAtafunga? Yes/No " + DOWN + "\n#Penalty #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                            continue
                    if 'goal' not in dtype: continue
                    score_val = det.get('scoreValue','')
                    if score_val and '-' in score_val: goal_score = score_val
                    else:
                        h = det.get('homeScore') or det.get('home_score') or hs
                        a = det.get('awayScore') or det.get('away_score') or as_
                        goal_score = str(h) + "-" + str(a)
                    pid=gid + "_GOAL_" + det_id
                    if pid not in posted:
                        if is_kpl:
                            scoring_team = home
                            try:
                                parts = goal_score.split('-')
                                if int(parts[0]) > int(str(hs)): scoring_team = home
                                else: scoring_team = away
                            except: scoring_team = player or home
                            gp = goal_score.split('-'); gh = gp[0] if '-' in goal_score else hs; ga = gp[1] if '-' in goal_score else as_
                            msg = kpl_sheng_caption(scoring_team, gh, ga, minute, player, flag)
                        else: msg=BRAND + " " + flag + " | " + SOCCER + " " + to_bold('GOAL ALERT') + " " + minute + "' : " + to_bold(home) + " " + to_bold(goal_score) + " " + to_bold(away) + " - " + to_bold(player) + "\n\n" + FIRE + " Is this the winner? " + EYE + " Drop your bet code in comments we track live!\n#DeBanaLive #" + lg
                        if post_fb(msg, is_kpl, lg, gid, teams):
                            posted.append(pid); save_posted(posted)
        if time.time() - last_controversy > 10800:
            pid="CONTRO_" + str(int(time.time()//10800))
            if pid not in posted:
                if check_giveaway_day() and random.random() < 0.5: msg=BRAND + " " + GIFT + " " + to_bold('PREDICT & WIN FRIDAY!') + " 100 bob airtime!\n\n" + to_bold('Predict correct score ya Gor vs AFC') + " " + DOWN + " First correct wins! Must FOLLOW page! " + BELL + "\n#Giveaway #DeBana"
                else: msg=BRAND + " " + THINK + " " + to_bold(random.choice(CONTROVERSY)) + "\n\nComment below - best comment pinned! " + DOWN + "\n#DeBanaDebate"
                if post_fb(msg, False, "", "", []):
                    posted.append(pid); save_posted(posted); last_controversy = time.time()
        if time.time()-last_news>1800:
            for art in fetch_news()[:1]:
                pid="NEWS_" + art.get('id','')
                if pid not in posted:
                    msg_news = BRAND + " " + NEWSP + " " + to_bold(art.get('headline','')) + " #DeBana\n\nThoughts? " + DOWN
                    if post_fb(msg_news, False, "", "", []):
                        posted.append(pid); save_posted(posted); last_news=time.time(); break
        if kpl_live: time.sleep(SLEEP_LIVE_KPL)
        elif live_now: time.sleep(SLEEP_LIVE)
        else: time.sleep(SLEEP_QUIET)
    except Exception as e:
        print("LOOP ERR " + str(e) + " - restarting in 10 sec")
        try: save_posted(posted)
        except: pass
        time.sleep(10)
