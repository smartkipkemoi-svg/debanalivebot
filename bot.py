import os, time, requests, json
from datetime import datetime

PAGE_ID=os.getenv("FB_PAGE_ID")
PAGE_TOKEN=os.getenv("FB_PAGE_TOKEN") or os.getenv("FB_TOKEN")

LEAGUES={
"eng.1":"PREMIER LEAGUE 🏴󐁧󐁢󐁥󐁮󐁧󐁿","esp.1":"LA LIGA 🇪🇸","ita.1":"SERIE A 🇮🇹","ger.1":"BUNDESLIGA 🇩🇪","fra.1":"LIGUE 1 🇫🇷",
"ned.1":"EREDIVISIE 🇳🇱","por.1":"PORTUGAL 🇵🇹","tur.1":"SUPER LIG 🇹🇷","usa.1":"MLS 🇺🇸","mex.1":"LIGA MX 🇲🇽",
"uefa.champions":"CHAMPIONS LEAGUE 🏆","uefa.europa":"EUROPA LEAGUE","fifa.worldq.caf":"WC QUAL AFRICA 🌍",
"fifa.worldq.uefa":"WC QUAL EUROPE","uefa.euro":"EURO 🇪🇺","caf.nations":"AFCON 🌍","conmebol.america":"COPA AMERICA"
}

NEWS_LEAGUES=["eng.1","esp.1","ita.1","uefa.champions"] # To avoid spam, check only big leagues for news

def post_text(msg):
    try:
        url=f"https://graph.facebook.com/{PAGE_ID}/feed"
        r=requests.post(url,data={"message":msg,"access_token":PAGE_TOKEN},timeout=30)
        print(f"POSTED {r.status_code}")
        return r.status_code==200
    except Exception as e:
        print(e); return False

def get_summary(league,eid):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}"
        return requests.get(url,timeout=20).json()
    except: return {}

def get_news(league):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/news"
        return requests.get(url,timeout=15).json().get("articles",[])[:5]
    except: return []

def run():
    try: posted=json.load(open("posted.json"))
    except: posted={}
    try: state=json.load(open("state.json"))
    except: state={}

    if "NEWS" not in posted: posted["NEWS"]=[]
    if "DAILY" not in posted: posted["DAILY"]=[]
    start=time.time()
    print("BOT STARTED - ULTIMATE PAGE")

    # --- PART 1: TRANSFERS / BREAKING / INTERVIEWS ---
    # This runs once per hour
    try:
        for league in NEWS_LEAGUES:
            articles=get_news(league)
            for art in articles:
                art_id=str(art.get("id") or art.get("dataSourceIdentifier",""))
                if not art_id or art_id in posted["NEWS"]: continue

                title=art.get("headline","")
                desc=art.get("description","")[:250]
                link=art.get("links",{}).get("web",{}).get("href","")

                low=(title+desc).lower()

                # TRANSFER NEWS
                if any(x in low for x in ["transfer","signs","deal","joins","agreement","here we go","medical"]):
                    msg=f"🚨 TRANSFER NEWS!\n\n{title}\n\n{desc}\n\n🔗 {link}\n\n#Transfer #DeBanaLive"
                    if post_text(msg):
                        posted["NEWS"].append(art_id)
                        time.sleep(5)
                        continue

                # BREAKING NEWS
                if any(x in low for x in ["breaking","injury","out for","suspended","fired","sacked","announced"]):
                    msg=f"🚨 BREAKING NEWS!\n\n{title}\n\n{desc}\n\n{link}\n\n#Breaking #DeBanaLive"
                    if post_text(msg):
                        posted["NEWS"].append(art_id)
                        time.sleep(5)
                        continue

                # INTERVIEW / QUOTES
                if any(x in low for x in ["says","interview","admits","reveals","slams","responds","quotes","press conference"]):
                    msg=f"🎙️ INTERVIEW / QUOTES\n\n{title}\n\n\"{desc}\"\n\n{link}\n\nWhat do you think? 👇\n#Interview"
                    if post_text(msg):
                        posted["NEWS"].append(art_id)
                        time.sleep(5)
    except Exception as e: print(f"news err {e}")

    # --- PART 2: DAILY FIXTURES ---
    today=datetime.now().strftime("%Y-%m-%d")
    if f"FIX_{today}" not in posted["DAILY"]:
        try:
            fix_text=f"⚽ TODAY'S GAMES - {today}\n\n"
            c=0
            for lg, lname in list(LEAGUES.items())[:10]:
                try:
                    data=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/scoreboard",timeout=10).json()
                    for g in data.get("events",[])[:2]:
                        comp=g["competitions"][0]
                        h=comp["competitors"][0]; a=comp["competitors"][1]
                        if h["homeAway"]!="home": h,a=a,h
                        fix_text+=f"• {h['team']['shortDisplayName']} vs {a['team']['shortDisplayName']} - {lname}\n"
                        c+=1
                except: pass
            fix_text+="\nDrop your predictions! 👇 #Fixtures"
            if c>0 and post_text(fix_text):
                posted["DAILY"].append(f"FIX_{today}")
        except: pass

    # --- PART 3: LIVE MATCHES ---
    while time.time()-start<540:
        for league,lname in LEAGUES.items():
            try:
                data=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard",timeout=15).json()
                for g in data.get("events",[]):
                    eid=str(g["id"])
                    comp=g["competitions"][0]
                    cstate=comp["status"]["type"]["state"]; desc=comp["status"]["type"]["description"]
                    short=comp["status"]["type"].get("shortDetail","")
                    home=comp["competitors"][0]; away=comp["competitors"][1]
                    if home["homeAway"]!="home": home,away=away,home
                    hn=home["team"]["shortDisplayName"]; an=away["team"]["shortDisplayName"]
                    score_now=f"{home['score']}-{away['score']}"
                    if eid not in posted: posted[eid]=[]
                    summ=get_summary(league,eid) if cstate in ["pre","in","post"] else {}

                    # LINEUPS - PRO FORMAT
                    if cstate=="pre" and "LINEUP" not in posted[eid]:
                        rosters=summ.get("rosters",[])
                        if rosters and len(rosters[0].get("roster",[]))>=10:
                            txt=f"📋 STARTING XI - CONFIRMED!\n\n{hn} vs {an}\n🏆 {lname}\n⏰ {short}\n\n"
                            for team in rosters[:2]:
                                tname=team.get("team",{}).get("shortDisplayName","")
                                formation=team.get("formation","")
                                txt+=f"🔹 {tname} ({formation}):\n"
                                for p in [x for x in team.get("roster",[]) if x.get("starter")][:11]:
                                    name=p.get('athlete',{}).get('displayName','')
                                    pos=p.get('position',{}).get('abbreviation','')
                                    txt+=f"{pos} {name}\n"
                                txt+="\n"
                            txt+="Who will win? 👇"
                            if post_text(txt): posted[eid].append("LINEUP")

                    # KICK OFF
                    if cstate=="in" and "KICK" not in posted[eid]:
                        if post_text(f"🔴 KICK OFF!\n{hn} vs {an}\n{lname} LIVE!\n\nFollow here for goals!"): posted[eid].append("KICK")

                    # GOALS / RED CARDS
                    if cstate=="in":
                        for ev in summ.get("keyEvents",[]):
                            ev_id=str(ev.get("id",""))
                            if not ev_id or ev_id in posted[eid]: continue
                            etype=ev.get("type",{}).get("text",""); etext=ev.get("text","")
                            clock=ev.get("clock",{}).get("displayValue","") or short
                            if "Goal" in etype:
                                if post_text(f"⚽🔥 GOOAL {clock}'\n{etext}\n\n{hn} {score_now} {an}\n{lname}\n#Goal"): posted[eid].append(ev_id)
                            elif "Red Card" in etype:
                                if post_text(f"🟥 RED CARD {clock}'\n{etext}\n{hn} {score_now} {an}\nThis changes everything!"): posted[eid].append(ev_id)

                    if desc=="Halftime" and "HT" not in posted[eid]:
                        if post_text(f"⏸️ HALF TIME: {hn} {score_now} {an} - {lname}"): posted[eid].append("HT")
                    if cstate=="post" and "FT" not in posted[eid] and score_now!="0-0":
                        if post_text(f"✅ FULL TIME: {hn} {score_now} {an}\n{lname}\n\nThoughts on the game? 👇"): posted[eid].append("FT")
            except Exception as e: print(e)

        json.dump(posted,open("posted.json","w")); json.dump(state,open("state.json","w"))
        time.sleep(50)

if __name__=="__main__": run()
