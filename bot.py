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
        if formations: extra += f"\n\U00002699\ufe0f Formation: {' vs '.join(formations[:2])}"
        if key_players: extra += f"\n\U00002b50 Key: {', '.join(key_players[:4])}"
        notes = comp.get('notes', [])
        if notes:
            for n in notes[:1]:
                if 'injur' in str(n).lower():
                    extra += f"\n\U0001f691 {n.get('headline','')[:80]}"
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

def get_match_stats(comp):
    try:
        stats = comp.get('statistics',[]) or comp.get('stats',[])
        out = ""
        for st in stats[:2]:
            s = st.get('stats',[]) if isinstance(st, dict) else []
            for item in s:
                name = item.get('name','').lower()
                if 'possession' in name or 'shots' in name:
                    out += f" {item.get('displayValue','')} {name},"
        if out:
            return f"\n\U0001f4ca Stats:{out[:80]}"
        return ""
    except: return ""

SHENG_STARTS = ["Gooool!", "Wamefunga!", "Wamepasua net!", "Moto!", "Chuma!", "Hatari!", "Bazuu!", "Woi!"]
SHENG_MIDS = ["wamechapa", "wamefunga", "wameweka ndani", "wameingiza", "amewasha", "amepasua", "amechoma"]
SHENG_ENDS = ["mambo imechemka", "hii game ni moto", "wameamua leo", "hakuna mchezo", "form ni kali", "wamezima", "KPL ni yetu!"]
EMOJIS = ["\U0001f525", "\u26bd", "\U0001f4a5", "\U0001f680", "\U0001f4a8", "\U0001f631", "\u26a1"]
SHENG_EXTRAS = ["KPL ni yetu!", "Hii ndio yetu!", "Ligi yetu tamu!", "Tuko ndani!", "Bana wamezima!"]

def kpl_sheng_caption(team, home, away, minute, player="", flag="KPL"):
    s = random.choice(SHENG_STARTS); m = random.choice(SHENG_MIDS); e = random.choice(SHENG_ENDS)
    emoji = random.choice(EMOJIS); extra = random.choice(SHENG_EXTRAS)
    player_txt = f" - {to_bold(player)} amefanya!" if player else ""
    templates = [
        f"{BRAND} {flag} | {to
