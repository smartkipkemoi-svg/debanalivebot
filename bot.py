import os, time, requests, json

PAGE_ID=os.getenv("FB_PAGE_ID")
PAGE_TOKEN=os.getenv("FB_PAGE_TOKEN")

# ALL LEAGUES - ESPN CODES
LEAGUES={
# Top 5
"eng.1":"PREMIER LEAGUE 🏴󐁧󐁢󐁥󐁮󐁧󐁿",
"esp.1":"LA LIGA 🇪🇸",
"ita.1":"SERIE A 🇮🇹",
"ger.1":"BUNDESLIGA 🇩🇪",
"fra.1":"LIGUE 1 🇫🇷",
# Other Europe
"ned.1":"EREDIVISIE 🇳🇱",
"por.1":"LIGA PORTUGAL 🇵🇹",
"tur.1":"SUPER LIG 🇹🇷",
"bel.1":"BELGIAN PRO LEAGUE 🇧🇪",
"sco.1":"SCOTTISH PREMIERSHIP 🏴󐁧󐁢󐁳󐁣󐁴󐁿",
"eng.2":"CHAMPIONSHIP",
"eng.fa":"FA CUP",
"eng.league_cup":"CARABAO CUP",
# Americas
"usa.1":"MLS 🇺🇸",
"mex.1":"LIGA MX 🇲🇽",
"arg.1":"LIGA ARGENTINA 🇦🇷",
"bra.1":"BRASILEIRAO 🇧🇷",
# International Club
"uefa.champions":"CHAMPIONS LEAGUE 🏆",
"uefa.europa":"EUROPA LEAGUE",
"uefa.conference":"CONFERENCE LEAGUE",
"uefa.champions_qual":"UCL QUALIFIERS",
# International Country - MOST IMPORTANT
"fifa.worldq.uefa":"WORLD CUP QUAL - EUROPE 🌍",
"fifa.worldq.concacaf":"WORLD CUP QUAL - CONCACAF",
"fifa.worldq.conmebol":"WORLD CUP QUAL - SOUTH AMERICA",
"fifa.worldq.caf":"WORLD CUP QUAL - AFRICA 🌍",
"fifa.worldq.afc":"WORLD CUP QUAL - ASIA",
"fifa.world":"FIFA WORLD CUP 🏆",
"uefa.euro":"EURO CUP 🇪🇺",
"uefa.euroq":"EURO QUALIFIERS",
"uefa.nations":"NATIONS LEAGUE",
"conmebol.america":"COPA AMERICA",
"caf.nations":"AFCON 🌍",
"afc.asian":"ASIAN CUP"
}

def post_text(msg):
    try:
        url=f"https://graph.facebook.com/{PAGE_ID}/feed"
        r=requests.post(url,data={"message":msg,"access_token":PAGE_TOKEN},timeout=30)
        print(f"POSTED {r.status_code}")
        return True
    except Exception as e:
        print(e)
        return False

def get_summary(league,eid):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}"
        return requests.get(url,timeout=20).json()
    except:
        return {}

def run():
    try: posted=json.load(open("posted.json"))
    except: posted={}
    try: state=json.load(open("state.json"))
    except: state={}

    start=time.time()
    print("BOT STARTED - ALL LEAGUES PRO")

    while time.time()-start<540:
        for league,lname in LEAGUES.items():
            try:
                sb=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
                data=requests.get(sb,timeout=15).json()
                for g in data.get("events",[]):
                    eid=str(g["id"])
                    comp=g["competitions"][0]
                    cstate=comp["status"]["type"]["state"] # pre,in,post
                    desc=comp["status"]["type"]["description"]
                    short=comp["status"]["type"].get("shortDetail","")

                    home=comp["competitors"][0]
                    away=comp["competitors"][1]
                    if home["homeAway"]!="home": home,away=away,home
                    hn=home["team"]["shortDisplayName"]
                    an=away["team"]["shortDisplayName"]
                    hs=home["score"]; aws=away["score"]
                    score_now=f"{hs}-{aws}"

                    if eid not in posted: posted[eid]=[]

                    # Get detailed summary
                    summ={}
                    if cstate in ["pre","in","post"]:
                        summ=get_summary(league,eid)

                    # 1. LINEUPS (1 hour before)
                    if cstate=="pre" and "LINEUP" not in posted[eid]:
                        rosters=summ.get("rosters",[])
                        if rosters and len(rosters[0].get("roster",[]))>=10:
                            txt=f"📋 CONFIRMED LINEUPS!\n\n{hn} vs {an}\n{lname}\n{short}\n\n"
                            for team in rosters[:2]:
                                tname=team.get("team",{}).get("shortDisplayName","")
                                txt+=f"{tname} XI:\n"
                                for p in [x for x in team.get("roster",[]) if x.get("starter")][:11]:
                                    txt+=f"• {p.get('athlete',{}).get('displayName','')}\n"
                                txt+="\n"
                            txt+="#Lineup #DeBanaLive"
                            if post_text(txt): posted[eid].append("LINEUP")

                    # 2. KICK OFF
                    if cstate=="in" and "KICK" not in posted[eid]:
                        if post_text(f"🔴 KICK OFF!\n\n{hn} vs {an}\n{lname} is LIVE!\n{short}\n\n#Live #DeBanaLive"):
                            posted[eid].append("KICK")

                    # 3. ALL KEY EVENTS
                    if cstate=="in":
                        for ev in summ.get("keyEvents",[]):
                            ev_id=str(ev.get("id",""))
                            if not ev_id or ev_id in posted[eid]: continue
                            etype=ev.get("type",{}).get("text","")
                            etext=ev.get("text","")
                            clock=ev.get("clock",{}).get("displayValue","") or short

                            if "Goal" in etype:
                                emoji="⚽🔥"
                                if "Penalty" in etype: emoji="⚽ PENALTY GOAL!"
                                txt=f"{emoji} GOOOAL!!!\n\n{clock}' {etext}\n\n{hn} {score_now} {an}\n{lname}\n\n#Goal #DeBanaLive"
                                if post_text(txt): posted[eid].append(ev_id)

                            elif "Red Card" in etype:
                                txt=f"🟥 RED CARD!\n\n{clock}' {etext}\n{hn} {score_now} {an}\n{lname}\n#RedCard"
                                if post_text(txt): posted[eid].append(ev_id)

                            elif "Yellow Card" in etype:
                                # Only post yellow if important player
                                if post_text(f"🟨 YELLOW CARD\n{clock}' {etext}\n{hn} {score_now} {an}"):
                                    posted[eid].append(ev_id)

                            elif "Substitution" in etype:
                                txt=f"🔄 SUBSTITUTION\n{clock}' {etext}\n{hn} {score_now} {an}"
                                if post_text(txt): posted[eid].append(ev_id)

                            elif "VAR" in etext or "VAR" in etype:
                                txt=f"📺 VAR CHECK!\n{clock}' {etext}\n{hn} {score_now} {an}\n{lname}"
                                if post_text(txt): posted[eid].append(ev_id)

                        state[eid]=score_now

                    # 4. HALF TIME
                    if desc=="Halftime" and "HT" not in posted[eid]:
                        if post_text(f"⏸️ HALF TIME\n\n{hn} {score_now} {an}\n{lname}\n\n#HalfTime"):
                            posted[eid].append("HT")

                    # 5. FULL TIME + STATS
                    if cstate=="post" and "FT" not in posted[eid] and score_now!="0-0":
                        goals=""
                        for ev in summ.get("keyEvents",[]):
                            if "Goal" in ev.get("type",{}).get("text",""):
                                goals+=f"⚽ {ev.get('text','')}\n"
                        stats=summ.get("statistics",[])
                        txt=f"✅ FULL TIME\n\n{hn} {score_now} {an}\n{lname}\n\n{goals}\n#FullTime #DeBanaLive"
                        if post_text(txt): posted[eid].append("FT")

            except Exception as e:
                print(f"err {league} {e}")

        json.dump(posted,open("posted.json","w"))
        json.dump(state,open("state.json","w"))
        time.sleep(45)

    print("DONE 9 MIN")

if __name__=="__main__":
    run()
