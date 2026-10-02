import requests, json, os, time, concurrent.futures, random, collections
from datetime import datetime, timezone
import pytz

FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN')
POSTED_FILE = "posted.json"
SLEEP_LIVE_KPL = 5
SLEEP_LIVE = 10
SLEEP_QUIET = 120

# === ADDED: CRASH-PROOF - FB RATE LIMIT QUEUE ===
POST_QUEUE = collections.deque()
LAST_POST_TIME = 0
MIN_POST_GAP = 90 # FB allows 25/hr, we do 90 sec gap = safe

LEAGUES = [
    "eng.1","eng.2","eng.fa","eng.league_cup",
    "esp.1","esp.2","esp.copa_del_rey",
    "ger.1","ita.1","fra.1","ned.1","por.1","bel.1","tur.1","sco.1","gre.1","sui.1",
    "uefa.champions","uefa.europa","uefa.europa_conference","uefa.super_cup","uefa.nations",
    "usa.1","bra.1","arg.1","conmebol.libertadores","conmebol.sudamericana",
    "ken.1","rsa.1","egy.1","caf.champions","caf.confed","caf.nations",
    "fifa.world","fifa.world.u20","fifa.friendly","uefa.euro","concacaf.gold","afc.asian",
    "nga.1","tza.1","ng.1","tz.1","uga.1","rwa.1"
]

def to_bold(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

LEAGUE_FLAGS = {
    "eng.1": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL", "eng.2": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "eng.fa": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 FA", "eng.league_cup": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "esp.1": "🇪🇸 LaLiga", "esp.2": "🇪🇸", "ger.1": "🇩🇪 Bundesliga", "ita.1": "🇮🇹 Serie A", "fra.1": "🇫🇷 Ligue 1",
    "ken.1": "🇰🇪 KPL", "rsa.1": "🇿🇦 PSL", "egy.1": "🇪🇬", "nga.1": "🇳🇬 NPFL", "tza.1": "🇹🇿 NBC PL", "ng.1": "🇳🇬", "tz.1": "🇹🇿", "uga.1": "🇺🇬 UPL", "rwa.1": "🇷🇼",
    "uefa.champions": "🏆 UCL", "uefa.europa": "🏆 UEL", "uefa.europa_conference": "🏆", "caf.champions": "🌍 CAF"
}
BRAND = "🎯"

CONTROVERSY = [
    "VAR: Hii ilikuwa penalty? YES or NO? 👇 Debate!",
    "GOAT debate: Messi vs Ronaldo - nani true GOAT? 🔥 Comment!",
    "Ref ameuza game leo? 😡 ama ni sawa?",
    "Hii team itashinda league? Predict! 🏆",
    "Best coach Kenya right now ni nani? 👇",
    "KPL vs EPL - ligi gani tamu zaidi? Debate!",
    "Man Utd itarudi top 4? YES/NO? 😅"
]

def check_giveaway_day():
    return datetime.now().weekday() == 4

def get_lineup_extra(comp):
    try:
        lineups = comp.get('lineups', []) or comp.get('lineup', [])
        formations = []; key_players = []
        for lu in lineups[:2]:
            f = lu.get('formation') or lu.get('formationString') or ""
            if f: formations.append(f)
            athletes = lu.get('athletes') or lu.get('players') or []
            if isinstance(athletes, list) and athletes:
                flat = []
                for group in athletes:
                    if isinstance(group, dict) and 'athletes' in group:
                        flat.extend(group.get('athletes', []))
                    elif isinstance(group, dict) and 'displayName' in group:
                        flat.append(group)
                for pl in flat[:2]:
                    name = pl.get('displayName') or pl.get('shortName') or ""
                    if name: key_players.append(name)
        extra = ""
        if formations: extra += f"\n⚙️ Formation: {' vs '.join(formations[:2])}"
        if key_players: extra += f"\n⭐ Key: {', '.join(key_players[:4])}"
        notes = comp.get('notes', [])
        if notes:
            for n in notes[:1]:
                if 'injur' in str(n).lower():
                    extra += f"\n🚑 {n.get('headline','')[:80]}"
        return extra
    except: return ""

def get_eat_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
        eat = dt.astimezone(pytz.timezone("Africa/Nairobi")) if pytz else dt
        return eat.strftime("%I:%M %p EAT")
    except:
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
            return f"{(dt.hour+3)%24}:00 EAT"
        except: return iso_str

def get_match_photo(lg, gid, is_kpl=False):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/summary?event={gid}"
        r = requests.get(url, timeout=10).json()
        articles = r.get('news',{}).get('articles',[]) or r.get('headlines',[])
        for art in articles[:3]:
            imgs = art.get('images',[])
            if imgs and imgs[0].get('url'): return imgs[0]['url']
        return None
    except Exception as e:
        print(f"photo err {e}"); return None

# === ADDED: CRASH-PROOF - GET STATS FOR FT ===
def get_match_stats(comp):
    try:
        stats = comp.get('statistics',[]) or comp.get('stats',[])
        out = ""
        for st in stats[:2]:
            # ESPN stats format varies
            s = st.get('stats',[]) if isinstance(st, dict) else []
            for item in s:
                name = item.get('name','').lower()
                if 'possession' in name or 'shots' in name:
                    out += f" {item.get('displayValue','')} {name},"
        if out:
            return f"\n📊 Stats:{out[:80]}"
        return ""
    except: return ""

SHENG_STARTS = ["Gooool!", "Wamefunga!", "Wamepasua net!", "Moto!", "Chuma!", "Hatari!", "Bazuu!", "Woi!"]
SHENG_MIDS = ["wamechapa", "wamefunga", "wameweka ndani", "wameingiza", "amewasha", "amepasua", "amechoma"]
SHENG_ENDS = ["mambo imechemka", "hii game ni moto", "wameamua leo", "hakuna mchezo", "form ni kali", "wamezima", "KPL ni yetu!"]
EMOJIS = ["🔥", "⚽", "💥", "🚀", "💨", "😱", "⚡"]
SHENG_EXTRAS = ["KPL ni yetu!", "Hii ndio yetu!", "Ligi yetu tamu!", "Tuko ndani!", "Bana wamezima!"]

def kpl_sheng_caption(team, home, away, minute, player="", flag="🇰🇪 KPL"):
    s = random.choice(SHENG_STARTS); m = random.choice(SHENG_MIDS); e = random.choice(SHENG_ENDS)
    emoji = random.choice(EMOJIS); extra = random.choice(SHENG_EXTRAS)
    player_txt = f" - {to_bold(player)} amefanya!" if player else ""
    templates = [
        f"{BRAND} {flag} | {to_bold(s)} {to_bold(team)} {m} {emoji} {to_bold(f'{home}-{away}')} ({minute}') {player_txt}\n{e} | {extra}\n\n📲 Track code yako hapa De Bana! Weka bet code yako comment 👇\n#DeBana #FKFPL #KPLLive",
        f"{BRAND} {flag} | {emoji} Dakika {to_bold(minute)}' - {to_bold(team)} {m} goli! {to_bold(f'{home}-{away}')} {player_txt}\n{e} - {extra}\n\n💬 Code yako iko aje? Drop kwa comment tuku-trackie!\n#DeBana",
        f"{BRAND} {flag} | {to_bold(team)} {m}! {s} {to_bold(f'{home}-{away}')} min {minute}' {emoji}\n{player} {e}\n\n🔥 {extra} | Track bet yako na De Bana!\n#FKFPL",
    ]
    return random.choice(templates)

def load_posted():
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE,'r') as f:
                data=json.load(f)
                return data if isinstance(data,list) else []
    except Exception as e: print(f"load error {e}")
    return []

# === ADDED: CRASH-PROOF SAVE - NO CORRUPT ===
def save_posted(p):
    if len(p)>2000: p=p[-2000:] # ADDED: bigger but trimmed
    try:
        tmp = POSTED_FILE + ".tmp"
        with open(tmp,'w') as f:
            json.dump(p,f)
        os.replace(tmp, POSTED_FILE) # atomic - never corrupt
        print(f"SAVED {len(p)}")
    except Exception as e: print(f"save error {e}")

def post_fb(msg, is_kpl=False, lg="", gid="", teams=[]):
    global LAST_POST_TIME
    # === ADDED: RATE LIMIT QUEUE ===
    now = time.time()
    if now - LAST_POST_TIME < MIN_POST_GAP:
        wait = MIN_POST_GAP - (now - LAST_POST_TIME)
        print(f"RATE LIMIT: waiting {int(wait)}s")
        time.sleep(wait)

    if not FB_PAGE_ID or not FB_TOKEN:
        print(f"NO TOKEN: {msg[:80]}"); return False
    if not is_kpl and random.random() < 0.3:
        time.sleep(random.randint(15,25))
    photo_url = None
    if gid and lg:
        try: photo_url = get_match_photo(lg, gid, is_kpl)
        except: photo_url = None
        if not is_kpl and photo_url and random.random() < 0.6: photo_url = None
    try:
        # ADDED: retry 3 times if fail - crash-proof
        for attempt in range(3):
            try:
                if photo_url:
                    r=requests.post(f"https://graph.facebook.com/{FB_PAGE_ID}/photos",
                                    data={"caption":msg, "url":photo_url, "access_token":FB_TOKEN}, timeout=20)
                else:
                    logo_url = None
                    if teams and len(teams)>=2:
                        logo_url = teams[0]['team'].get('logo') or teams[1]['team'].get('logo')
                    if logo_url and random.random() < 0.7:
                        r=requests.post(f"https://graph.facebook.com/{FB_PAGE_ID}/photos",
                                        data={"caption":msg, "url":logo_url, "access_token":FB_TOKEN}, timeout=20)
                    else:
                        r=requests.post(f"https://graph.facebook.com/{FB_PAGE_ID}/feed",
                                        data={"message":msg,"access_token":FB_TOKEN}, timeout=15)
                print(f"FB {r.status_code} attempt {attempt}: {msg[:70]}")
                if r.status_code==200:
                    LAST_POST_TIME = time.time()
                    try:
                        post_id = r.json().get('id') or r.json().get('post_id')
                        if post_id:
                            comment_msg = "👉 Follow De Bana for fastest goals! ⚡ Turn ON notifications 🔔 | Drop your bet code 👇 tunatrack live!"
                            if is_kpl: comment_msg = "👉 Follow De Bana! Fastest KPL updates hapa! 🔔 Weka bet code yako hapa tuku-trackie! #DeBana"
                            requests.post(f"https://graph.facebook.com/{post_id}/comments",
                                data={"message":comment_msg,"access_token":FB_TOKEN}, timeout=10)
                    except Exception as e: print(f"comment err {e}")
                    return True
                elif r.status_code == 429: # rate limited
                    print("FB RATE LIMITED - sleeping 5 min")
                    time.sleep(300)
                    continue
                else:
                    time.sleep(5)
            except Exception as e:
                print(f"FB attempt {attempt} err {e}")
                time.sleep(5)
        return False
    except Exception as e: print(f"FB ERR {e}"); return False

def fetch_league(lg):
    try:
        # ADDED: retry + timeout crash-proof
        for _ in range(2):
            try:
                url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard"
                r=requests.get(url, timeout=15) # increased timeout
                if r.status_code!=200: return []
                out=[]
                for ev in r.json().get('events',[]):
                    ev['_lg']=lg; out.append(ev)
                return out
            except: time.sleep(1)
        return []
    except: return []

def fetch_news():
    news=[]
    for lg in ["eng.1","esp.1","ken.1","uefa.champions"]:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/news"
            r=requests.get(url, timeout=10)
            if r.status_code==200:
                for a in r.json().get('articles',[])[:2]: news.append(a)
        except: pass
    return news

posted=load_posted()
last_news=0
last_controversy = time.time() - 10000
print(f"De Bana BOT v100 STARTED - {len(posted)} posted - CRASH-PROOF + RATE LIMIT + STATS + FLOOD MODE")

while True:
    try:
        games=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            for res in ex.map(fetch_league, LEAGUES):
                games.extend(res)

        live_now=False
        kpl_live=False
        for ev in games:
            gid=ev.get('id')
            state=ev.get('status',{}).get('type',{}).get('state','')
            comp=ev.get('competitions',[{}])[0]
            teams=comp.get('competitors',[])
            if len(teams)<2: continue
            home=teams[0]['team']['displayName']; away=teams[1]['team']['displayName']
            hs=teams[0].get('score','0'); as_=teams[1].get('score','0')
            lg=ev.get('_lg','')
            is_kpl = lg in ["ken.1","KE.1"] or "kenya" in lg.lower()
            flag = LEAGUE_FLAGS.get(lg, f"#{lg}")

            if state=='post':
                pid=f"{gid}_FT_{hs}-{as_}"
                if pid not in posted:
                    stats_extra = get_match_stats(comp) # ADDED
                    if is_kpl:
                        # ADDED: FULL SHENG FT
                        msg=f"{BRAND} {flag} | 🔚 {to_bold('FT hapa KPL!')} {to_bold(home)} {to_bold(f'{hs}-{as_}')} {to_bold(away)}. {random.choice(SHENG_ENDS)}! {random.choice(SHENG_EXTRAS)} 🔥{stats_extra}\n\nCode yako iliingia? Drop comment 👇 Wamebaki na point ngapi?\n#FT #FKFPL #DeBana"
                    else:
                        msg=f"{BRAND} {flag} | 🔚 {to_bold('FULL TIME:')} {to_bold(home)} {to_bold(f'{hs}-{as_}')} {to_bold(away)}{stats_extra}\n\nWhat a game! Thoughts? 👇 Who was MOTM?\n#FT #{lg} #DeBana"
                    if post_fb(msg, is_kpl, lg, gid, teams):
                        posted.append(pid); save_posted(posted)
                continue

            if state=='in':
                live_now=True
                if is_kpl: kpl_live=True

            if state=='pre':
                try:
                    from dateutil import parser
                    dt = parser.isoparse(ev.get('date'))
                    mins_to_kick = (dt - datetime.now(timezone.utc)).total_seconds()/60
                    if 110 < mins_to_kick < 130:
                        pid=f"{gid}_PREVIEW"
                        if pid not in posted:
                            try: eat_str = get_eat_time(ev.get('date'))
                            except: eat_str = "Tonight"
                            msg=f"{BRAND} {flag} | ⏰ {to_bold('COMING UP')} - {to_bold(home)} vs {to_bold(away)} | {eat_str}\n\nH2H? Form? Nani atashinda? Drop prediction 👇\nOdds? Bet code? Tukutrack!\n#Preview #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                    # ADDED: KPL lineup fallback if ESPN has none
                    if 5 < mins_to_kick < 35 and is_kpl:
                        pid=f"{gid}_LINEUP_FALLBACK"
                        if pid not in posted and not comp.get('lineups'):
                            msg=f"{BRAND} {flag} | ⏰ {to_bold('LINEUP SOON')} - {to_bold(home)} vs {to_bold(away)} | {eat_str if 'eat_str' in locals() else ''}\n\nNani a-anze leo? Who should start? 👇 Predict XI!\n#KPL #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                except: pass

            if state=='pre' and comp.get('lineups'):
                pid=f"{gid}_LINEUP"
                if pid not in posted:
                    extra_info = get_lineup_extra(comp)
                    msg=f"{BRAND} {flag} | 📋 {to_bold('LINEUP DROP:')} {to_bold(home)} vs {to_bold(away)}{extra_info}\n\nStarting XIs are out! Who wins? 👀 Predict score 👇\n#Lineup #BuildUp #DeBana"
                    if post_fb(msg, is_kpl, lg, gid, teams):
                        posted.append(pid); save_posted(posted)

            if state=='in':
                status_detail = comp.get('status',{}).get('type',{}).get('detail','').lower()
                if 'half' in status_detail:
                    pid=f"{gid}_HT_{hs}-{as_}"
                    if pid not in posted:
                        if is_kpl:
                            msg=f"{BRAND} {flag} | ⏸️ {to_bold('HT hapa KPL!')} {to_bold(home)} {to_bold(f'{hs}-{as_}')} {to_bold(away)} - Mapumziko! {random.choice(SHENG_ENDS)}\n\nSecond half nani atafunga? 👇\n#HT #DeBana"
                        else:
                            msg=f"{BRAND} {flag} | ⏸️ {to_bold('HALF TIME:')} {to_bold(home)} {to_bold(f'{hs}-{as_}')} {to_bold(away)}\n\nSecond half nani atafunga? 👇 Drop prediction!\n#HT #DeBana"
                        if post_fb(msg, is_kpl, lg, gid, teams):
                            posted.append(pid); save_posted(posted)

                for det in comp.get('details',[]):
                    if not isinstance(det, dict): continue
                    dtype = str(det.get('type','')).lower()
                    minute=det.get('clock',{}).get('displayValue','')
                    player=det.get('athletesInvolved',[{}])[0].get('displayName','') if det.get('athletesInvolved') else ''
                    det_id = det.get('id') or f"{minute}_{player}_{dtype}"
                    if 'red' in dtype or 'ejection' in dtype:
                        pid=f"{gid}_RED_{det_id}"
                        if pid not in posted:
                            msg=f"{BRAND} {flag} | 🚨 {to_bold('RED CARD')} {minute}' - {to_bold(player)} ({home} vs {away}) OFF!\n\nGame imebadilika! 👀 Score itaisha aje?\n#RedCard #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                            continue
                    if 'penalty' in dtype or 'pen' in dtype:
                        pid=f"{gid}_PEN_{det_id}"
                        if pid not in posted:
                            msg=f"{BRAND} {flag} | ⚠️ {to_bold('PENALTY')} {minute}' - {to_bold(home)} vs {to_bold(away)} - {player}\n\nAtafunga? Yes/No 👇\n#Penalty #DeBana"
                            if post_fb(msg, is_kpl, lg, gid, teams):
                                posted.append(pid); save_posted(posted)
                            continue
                    if 'goal' not in dtype: continue
                    score_val = det.get('scoreValue','')
                    if score_val and '-' in score_val: goal_score = score_val
                    else:
                        h = det.get('homeScore') or det.get('home_score') or hs
                        a = det.get('awayScore') or det.get('away_score') or as_
                        goal_score = f"{h}-{a}"
                    pid=f"{gid}_GOAL_{det_id}"
                    if pid not in posted:
                        if is_kpl:
                            scoring_team = home
                            try:
                                if int(goal_score.split('-')[0]) > int(str(hs)): scoring_team = home
                                else: scoring_team = away
                            except: scoring_team = player or home
                            msg = kpl_sheng_caption(scoring_team, goal_score.split('-')[0] if '-' in goal_score else hs, goal_score.split('-')[1] if '-' in goal_score else as_, minute, player, flag)
                        else:
                            msg=f"{BRAND} {flag} | ⚽ {to_bold('GOAL ALERT')} {minute}' : {to_bold(home)} {to_bold(goal_score)} {to_bold(away)} - {to_bold(player)}\n\n🔥 Is this the winner? 👀 Drop your bet code in comments we track live!\n#DeBanaLive #{lg}"
                        if post_fb(msg, is_kpl, lg, gid, teams):
                            posted.append(pid); save_posted(posted)

        if time.time() - last_controversy > 10800:
            pid=f"CONTRO_{int(time.time()//10800)}"
            if pid not in posted:
                if check_giveaway_day() and random.random() < 0.5:
                    msg=f"{BRAND} 🎁 {to_bold('PREDICT & WIN FRIDAY!')} 100 bob airtime!\n\n{to_bold('Predict correct score ya Gor vs AFC')} 👇 First correct wins! Must FOLLOW page! 🔔\n#Giveaway #DeBana"
                else:
                    msg=f"{BRAND} 🤔 {to_bold(random.choice(CONTROVERSY))}\n\nComment below - best comment pinned! 👇\n#DeBanaDebate"
                if post_fb(msg, False, "", "", []):
                    posted.append(pid); save_posted(posted)
                    last_controversy = time.time()

        if time.time()-last_news>1800:
            for art in fetch_news()[:1]:
             
