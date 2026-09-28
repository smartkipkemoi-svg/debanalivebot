import os
import time
import requests
import json

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

LEAGUES = {
    "eng.1": "PREMIER LEAGUE",
    "esp.1": "LA LIGA",
    "ita.1": "SERIE A",
    "ger.1": "BUNDESLIGA",
    "fra.1": "LIGUE 1",
    "ned.1": "EREDIVISIE",
    "por.1": "LIGA PORTUGAL",
    "tur.1": "TURKISH SUPER LIG",
    "eng.2": "CHAMPIONSHIP",
    "uefa.champions": "CHAMPIONS LEAGUE",
    "uefa.europa": "EUROPA LEAGUE",
    "uefa.conference": "CONFERENCE LEAGUE"
}

def post_text(msg):
    try:
        url = f"https://graph.facebook.com/{PAGE_ID}/feed"
        r = requests.post(url, data={"message": msg, "access_token": PAGE_TOKEN}, timeout=30)
        print(f"POSTED {r.status_code}")
        return r
    except Exception as e:
        print(f"Post error {e}")
        return None

def get_summary(league, eid):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={eid}"
        resp = requests.get(url, timeout=15)
        return resp.json()
    except Exception:
        return {}

def run():
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
    except Exception:
        state = {}

    try:
        with open("posted.json", "r") as f:
            posted = json.load(f)
    except Exception:
        posted = {}

    start = time.time()
    print("BOT STARTED - TEXT ONLY - ALL LEAGUES")

    while time.time() - start < 540:
        for league, lname in LEAGUES.items():
            try:
                sb_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
                data = requests.get(sb_url, timeout=15).json()
                games = data.get("events", [])

                for g in games:
                    eid = g["id"]
                    comp = g["competitions"][0]
                    cstate = comp["status"]["type"]["state"]
                    desc = comp["status"]["type"]["description"]
                    short = comp["status"]["type"].get("shortDetail", "")

                    home = comp["competitors"][0]
                    away = comp["competitors"][1]
                    if home["homeAway"]!= "home":
                        home, away = away, home

                    hn = home["team"]["shortDisplayName"]
                    an = away["team"]["shortDisplayName"]
                    score_now = f"{home['score']}-{away['score']}"

                    if eid not in posted:
                        posted[eid] = []

                    summ = {}
                    if cstate in ["pre", "in", "post"]:
                        summ = get_summary(league, eid)

                    # LINEUPS
                    if cstate == "pre" and "lineup" not in posted[eid]:
                        rosters = summ.get("rosters", [])
                        if rosters and len(rosters[0].get("roster", [])) > 10:
                            txt = f"📋 CONFIRMED LINEUPS!\n\n{hn} vs {an}\n{lname}\n{short}\n\n"
                            for team in rosters[:2]:
                                tname = team.get("team", {}).get("shortDisplayName", "")
                                txt += f"{tname} XI:\n"
                                starters = [x for x in team.get("roster", []) if x.get("starter")]
                                for p in starters[:11]:
                                    pname = p.get("athlete", {}).get("displayName", "")
                                    txt += f"• {pname}\n"
                                txt += "\n"
                            txt += "#Lineups #DeBanaLive"
                            post_text(txt)
                            posted[eid].append("lineup")
                            time.sleep(5)

                    # KICK OFF
                    if cstate == "in" and "kick" not in posted[eid]:
                        txt = f"🔴 KICK OFF!\n\n{hn} vs {an}\n{lname} is LIVE!\n\n#Live #DeBanaLive"
                        post_text(txt)
                        posted[eid].append("kick")
                        time.sleep(4)

                    # GOALS + RED CARDS
                    if cstate == "in":
                        for ev in summ.get("keyEvents", []):
                            ev_id = str(ev.get("id", ""))
                            if ev_id in posted[eid]:
                                continue
                            etype = ev.get("type", {}).get("text", "")
                            etext = ev.get("text", "")
                            clock = ev.get("clock", {}).get("displayValue", "") or short

                            if "Goal" in etype:
                                msg = f"GOOOAL!!! ⚽🔥\n\n{clock}' {etext}\n\n{hn} {score_now} {an}\n{lname}\n\n#Goal #DeBanaLive"
                                post_text(msg)
                                posted[eid].append(ev_id)
                                time.sleep(5)

                            if "Red Card" in etype:
                                msg = f"🟥 RED CARD!\n\n{clock}' {etext}\n{hn} {score_now} {an}\n{lname}"
                                post_text(msg)
                                posted[eid].append(ev_id)
                                time.sleep(5)

                        if state.get(eid) and state.get(eid)!= score_now:
                            if state.get(eid)!= "0-0":
                                if
