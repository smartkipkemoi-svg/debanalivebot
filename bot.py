import requests, json, os, time, concurrent.futures, random, collections
from datetime import datetime, timezone
import pytz
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_TOKEN = os.environ.get('FB_TOKEN')
POSTED_FILE = "posted.json"
SLEEP_LIVE_KPL = 5
SLEEP_LIVE = 10
SLEEP_QUIET = 120
POST_QUEUE = collections.deque()
LAST_POST_TIME = 0
MIN_POST_GAP = 90
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
    def _c(ch):
        if 'A' <= ch <= 'Z':
            return chr(0x1D5D4 + ord(ch) - 65)
        if 'a' <= ch <= 'z':
            return chr(0x1D5EE + ord(ch) - 97)
        if '0' <= ch <= '9':
            return chr(0x1D7EC + ord(ch) - 48)
        return ch
    return "".join(_c(c) for c in text)
LEAGUE_FLAGS = {
    "eng.1": "EPL", "eng.2": "EPL", "eng.fa": "FA Cup", "eng.league_cup": "EFL Cup",
    "esp.1": "LaLiga", "esp.2": "LaLiga2", "ger.1": "Bundesliga", "ita.1": "Serie A", "fra.1": "Ligue 1",
    "ken.1": "KPL", "rsa.1": "PSL", "egy.1": "EGY", "nga.1": "NPFL", "tza.1": "NBC PL", "ng.1": "NPFL", "tz.1": "NBC", "uga.1": "UPL", "rwa.1": "RPL",
    "uefa.champions": "UCL", "uefa.europa": "UEL", "uefa.europa_conference": "UECL", "caf.champions": "CAF"
}
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
POINT = "\U0001f449"
BELL = "\U0001f514"
ZAP = "\u26a1"
EYE = "\U0001f440"
GIFT = "\U0001f381"
THINK = "\U0001f914"
NEWSP = "\U0001f4f0"
GEAR = "\U00002699\ufe0f"
STAR = "\U00002b50"
AMB = "\U0001f691"
CHART = "\U0001f4ca"
CONTROVERSY = [
    "VAR: Hii ilikuwa penalty? YES or NO? \U0001f447 Debate!",
    "GOAT debate: Messi vs Ronaldo - nani true GOAT? \U0001f525 Comment!",
    "Ref ameuza game leo? \U0001f621 ama ni sawa?",
    "Hii team itashinda league? Predict! \U0001f3c6",
    "Best coach Kenya right now ni nani? \U0001f447",
    "KPL vs EPL - ligi gani tamu zaidi? Debate!",
    "Man Utd itarudi top 4? YES/NO? \U0001f605"
]
def check_giveaway_day():
    return datetime.now().weekday() == 4
def get_lineup_extra(comp):
    try:
        lineups = comp.get('lineups', []) or comp.get('lineup', [])
        formations = []
        key_players = []
        for lu in lineups[:2]:
            f = lu.get('formation') or lu.get('formationString') or ""
            if f:
                formations.append(f)
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
                    if name:
                        key_players.append(name)
        extra = ""
        if formations:
            extra = extra + "\n" + GEAR + " Formation: " + " vs ".join(formations[:2])
        if key_players:
            extra = extra + "\n" + STAR + " Key: " + ", ".join(key_players[:4])
        notes = comp.get('notes', [])
        if notes:
            for n in notes[:1]:
                if 'injur' in str(n).lower():
                    extra = extra + "\n" + AMB + " " + n.get('headline','')[:80]
        return extra
    except:
        return ""
def get_eat_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
        eat = dt.astimezone(pytz.timezone("Africa/Nairobi")) if pytz else dt
        return eat.strftime("%I:%M %p EAT")
    except:
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
            return str((dt.hour+3)%24) + ":00 EAT"
        except:
            return iso_str
def get_match_photo(lg, gid, is_kpl=False):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/" + lg + "/summary?event=" + gid
        r = requests.get(url, timeout=10).json()
        articles = r.get('news',{}).get('articles',[]) or r.get('headlines',[])
        for art in articles[:3]:
            imgs = art.get('images',[])
            if imgs and imgs[0].get('url'):
                return imgs[0]['url']
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
                if 'possession' in name or 'shots' in name:
                    out = out + " " + item.get('displayValue','') + " " + name + ","
        if out:
            return "\n" + CHART + " Stats:" + out[:80]
        return ""
    except:
        return ""
SHENG_STARTS = ["Gooool!", "Wamefunga!", "Wamepasua net!", "Moto!", "Chuma!", "Hatari!", "Bazuu!", "Woi!"]
SHENG_MIDS = ["wamechapa", "wamefunga", "wameweka ndani", "wameingiza", "amewasha", "amepasua", "amechoma"]
SHENG_ENDS = ["mambo imechemka", "hii game ni moto", "wameamua leo", "hakuna mchezo", "form ni kali", "wamezima", "KPL ni yetu!"]
EMOJIS = [FIRE, SOCCER, "\U0001f4a5", "\U0001f680", "\U0001f4a8", "\U0001f631", ZAP]
SHENG_EXTRAS = ["KPL ni yetu!", "Hii ndio yetu!", "Ligi yetu tamu!", "Tuko ndani!", "Bana wamezima!"]
def kpl_sheng_caption(team, home, away, minute, player="", flag="KPL"):
    s = random.choice(SHENG_STARTS)
    m = random.choice(SHENG_MIDS)
    e = random.choice(SHENG_ENDS)
    emoji = random.choice(EMOJIS)
    extra = random.choice(SHENG_EXTRAS)
    score_str = home + "-" + away
    bold_score = to_bold(score_str)
    bold_team = to_bold(team)
    bold_s = to_bold(s)
    bold_min = to_bold(str(minute))
    player_txt = ""
    if player:
        player_txt = " - " + to_bold(player) + " amefanya!"
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
    except Exception as e:
        print("load error " + str(e))
    return []
def save_posted(p):
    if len(p)>2000:
        p=p[-2000:]
    try:
        tmp = POSTED_FILE + ".tmp"
        with open(tmp,'w') as f:
            json.dump(p,f)
        os.replace(tmp, POSTED_FILE)
        print("SAVED " + str(len(p)))
    except Exception as e:
        print("save error " + str(e))
