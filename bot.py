import os, time, requests, json

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

LEAGUES = {
    "eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1",
    "ned.1":"EREDIVISIE","por.1":"LIGA PORTUGAL","tur.1":"TURKISH SUPER LIG","eng.2":"CHAMPIONSHIP",
    "uefa.champions":"CHAMPIONS LEAGUE","uefa.europa":"EUROPA LEAGUE","uefa.conference":"CONFERENCE LEAGUE","uefa.nations":"NATIONS LEAGUE"
}

def post_text(msg):
    url=f"https://graph.facebook.com/{PAGE_ID}/feed"
    r=requests.post(url,data={"message":msg,"access_token":PAGE_TOKEN},timeout=30)
    print(f"POSTED {r.status_code}")
    return r

def get_summary(league,eid):
    try:
        return requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}",timeout=15).json()
    except: return {}

def run():
    try: state=json.load(open("state.json"))
    except: state={}
    try: posted=json.load(open("posted.json"))
    except: posted={}

    start=time.time()
    print("COMPLETE BOT - ALL EVENTS - TEXT ONLY")

    while time.time()-start < 540:
        for league,lname in LEAGUES.items():
            try:
                games=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard",timeout=15).json().get("events",[])
                for g in games:
                    eid=g["id"]; comp=g["competitions"][0]
                    st=comp["status"]["type"]["state"]
                    desc=comp["status"]["type"]["description"]
                    short=comp["status"]["type"].get("shortDetail","")
                    home=comp["competitors"][0]; away=comp["competitors"][1]
                    if home["homeAway"]!="home": home,away=away,home
                    hn=home['team']['shortDisplayName']; an=away['team']['shortDisplayName']
                    score=f"{home['score']}-{away['score']}"
                    if eid not in posted: posted[eid]=[]

                    summ={}
                    if st in ["pre","in","post"]:
                        summ=get_summary(league,eid)

                    # 1. CONFIRMED LINEUPS (1 hour before)
                    if st=="pre" and "lineup" not in posted[eid]:
                        rosters=summ.get("rosters",[])
                        if rosters and len(rosters[0].get("roster",[]))>10:
                            txt=f"📋 CONFIRMED LINEUPS!\n\n{hn} vs {an}\n{lname}\n{short}\n\n"
                            for team in rosters[:2]:
                                tname=team.get("team",{}).get("shortDisplayName","")
                                txt+=f"{tname} XI:\n"
                                for p in [x for x in team.get("roster",[]) if x.get("starter")][:11]:
                                    name=p.get("athlete",{}).get("displayName","")
                                    txt+=f"• {name}\n"
                                txt+="\n"
                            txt+=f"#Lineups #DeBanaLive"
                            post_text(txt); posted[eid].append("lineup"); time.sleep(5)

                    # 2. KICK OFF
                    if st=="in" and "kick" not in posted[eid]:
                        txt=f"🔴 KICK OFF!\n\n{hn} vs {an}\n{lname} is LIVE now!\n\n#Live #DeBanaLive"
                        post_text(txt); posted[eid].append("kick"); time.sleep(4)

                    # 3. GOALS + RED CARDS + PENALTIES (from keyEvents)
                    if st=="in":
                        for ev in summ.get("keyEvents",[]):
                            ev_id=str(ev.get("id",""))
                            if ev_id in posted[eid]: continue
                            etype=ev.get("type",{}).get("text",""); etext=ev.get("text","")
                            clock=ev.get("clock",{}).get("displayValue","") or short

                            if "Goal" in etype:
                                msg=f"GOOOAL!!! ⚽🔥\n\n{clock}' {etext}\n\n{hn} {score} {an}\n{lname}\n\n#Goal #DeBanaLive"
                                post_text(msg); posted[eid].append(ev_id); time.sleep(5)

                            if "Red Card" in etype:
                                msg=f"🟥 RED CARD!\n\n{clock}' {etext}\n{hn} {score} {an} - {hn if 'home' in etext.lower() else an} down to 10 men!\n{lname}\n\n#RedCard"
                                post_text(msg); posted[eid].append(ev_id); time.sleep(5)

                        # fallback for score change if keyEvents late
                        if state.get(eid) and state.get(eid)!=score and state.get(eid)!="0-0":
                            if score!=state.get(eid):
                                msg=f"GOAL! ⚽\n\n{short}\n{hn} {score} {an}\n{lname}"
                                post_text(msg); time.sleep(4)
                        state[eid]=score

                    # 4. HALF TIME
                    if desc=="Halftime" and "ht" not in posted
