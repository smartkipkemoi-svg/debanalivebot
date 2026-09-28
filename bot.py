import os, time, requests, json

PAGE_ID=os.getenv("FB_PAGE_ID")
PAGE_TOKEN=os.getenv("FB_PAGE_TOKEN")

LEAGUES={"eng.1":"PREMIER LEAGUE","esp.1":"LA LIGA","ita.1":"SERIE A","ger.1":"BUNDESLIGA","fra.1":"LIGUE 1","uefa.champions":"CHAMPIONS LEAGUE"}

def post_text(msg):
    try:
        url=f"https://graph.facebook.com/{PAGE_ID}/feed"
        requests.post(url,data={"message":msg,"access_token":PAGE_TOKEN},timeout=30)
        print("POSTED")
    except Exception as e:
        print(e)

def get_summary(league,eid):
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}"
        r=requests.get(url,timeout=15)
        return r.json()
    except Exception:
        return {}

def run():
    try:
        state=json.load(open("state.json"))
    except Exception:
        state={}
    try:
        posted=json.load(open("posted.json"))
    except Exception:
        posted={}

    start=time.time()
    while time.time()-start<540:
        for league,lname in LEAGUES.items():
            try:
                data=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard",timeout=15).json()
                for g in data.get("events",[]):
                    eid=g["id"]
                    comp=g["competitions"][0]
                    cstate=comp["status"]["type"]["state"]
                    desc=comp["status"]["type"]["description"]
                    short=comp["status"]["type"].get("shortDetail","")
                    home=comp["competitors"][0]
                    away=comp["competitors"][1]
                    if home["homeAway"]!="home":
                        home,away=away,home
                    hn=home["team"]["shortDisplayName"]
                    an=away["team"]["shortDisplayName"]
                    score_now=f"{home['score']}-{away['score']}"
                    if eid not in posted:
                        posted[eid]=[]
                    summ=get_summary(league,eid)
                    if cstate=="in" and "kick" not in posted[eid]:
                        post_text(f"KICK OFF!\n\n{hn} vs {an}\n{lname}")
                        posted[eid].append("kick")
                        time.sleep(3)
                    if cstate=="in":
                        for ev in summ.get("keyEvents",[]):
                            ev_id=str(ev.get("id",""))
                            if ev_id in posted[eid]:
                                continue
                            etype=ev.get("type",{}).get("text","")
                            etext=ev.get("text","")
                            clock=ev.get("clock",{}).get("displayValue","") or short
                            if "Goal" in etype:
                                post_text(f"GOOOAL!!!\n\n{clock}' {etext}\n{hn} {score_now} {an}\n{lname}")
                                posted[eid].append(ev_id)
                                time.sleep(4)
                            if "Red Card" in etype:
                                post_text(f"RED CARD!\n\n{clock}' {etext}\n{hn} {score_now} {an}\n{lname}")
                                posted[eid].append(ev_id)
                                time.sleep(4)
                        state[eid]=score_now
                    if desc=="Halftime" and "ht" not in posted[eid]:
                        post_text(f"HALF TIME\n\n{hn} {score_now} {an}\n{lname}")
                        posted[eid].append("ht")
                    if cstate=="post" and "ft" not in posted[eid] and score_now!="0-0":
                        post_text(f"FULL TIME\n\n{hn} {score_now} {an}\n{lname}")
                        posted[eid].append("ft")
            except Exception as e:
                print(e)
        json.dump(state,open("state.json","w"))
        json.dump(posted,open("posted.json","w"))
        time.sleep(30)

if __name__=="__main__":
    run()
