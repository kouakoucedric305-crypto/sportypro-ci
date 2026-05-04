"""
SportyPro CI — Site de pronostics sportifs
Crédité par Kouakou Cedric
Propulsé par football-data.org — Vrais matchs + scores en direct + classements
"""
from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
import random
import os
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sportytrader-cedric-2026")

# ─── Clé football-data.org ───────────────────────────────────────────────────
API_KEY = os.environ.get("FOOTBALLDATA_KEY", "fc2aba02543e4baaa3fcdc91f7d39c7c")
HEADERS = {"X-Auth-Token": API_KEY}
FOOTBALL_API = "https://api.football-data.org/v4"

# ─── Cache intelligent : 2 min si match en cours, 1h sinon ──────────────────
_CACHE = {}
CACHE_TTL_LIVE   = 120    # 2 minutes pour matchs en direct
CACHE_TTL_NORMAL = 3600   # 1 heure pour matchs programmés / classements

def _cached_get(url, params=None, headers=None, live=False):
    key = url + str(sorted((params or {}).items()))
    now = time.time()
    ttl = CACHE_TTL_LIVE if live else CACHE_TTL_NORMAL
    if key in _CACHE and now - _CACHE[key]["ts"] < ttl:
        return _CACHE[key]["data"]
    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        data = r.json()
        _CACHE[key] = {"data": data, "ts": now}
        return data
    except Exception as e:
        print(f"[football-data] Erreur {url}: {e}")
        return {}

# ─── Configuration sports ─────────────────────────────────────────────────────
SPORT_CONFIGS = {
    "football": {
        "name": "Football", "icon": "⚽", "color": "#00e676",
        "leagues": [
            {"id": "PL",  "name": "Premier League",   "country": "🏴 Angleterre", "logo": "https://crests.football-data.org/770.png"},
            {"id": "PD",  "name": "La Liga",           "country": "🇪🇸 Espagne",   "logo": "https://crests.football-data.org/760.png"},
            {"id": "BL1", "name": "Bundesliga",        "country": "🇩🇪 Allemagne", "logo": "https://crests.football-data.org/BL1.png"},
            {"id": "SA",  "name": "Serie A",           "country": "🇮🇹 Italie",    "logo": "https://crests.football-data.org/SA.png"},
            {"id": "FL1", "name": "Ligue 1",           "country": "🇫🇷 France",    "logo": "https://crests.football-data.org/FL1.png"},
            {"id": "CL",  "name": "Champions League",  "country": "🏆 Europe",     "logo": "https://crests.football-data.org/CL.png"},
            {"id": "EL",  "name": "Europa League",     "country": "🏆 Europe",     "logo": "https://crests.football-data.org/EL.png"},
        ],
    },
    "basketball": {
        "name": "Basketball", "icon": "🏀", "color": "#ff6d00",
        "leagues": [
            {"id": "NBA",        "name": "NBA",       "country": "🇺🇸 USA",    "logo": ""},
            {"id": "euroleague", "name": "Euroleague", "country": "🇪🇺 Europe", "logo": ""},
        ],
    },
    "tennis": {
        "name": "Tennis", "icon": "🎾", "color": "#c6ff00",
        "leagues": [
            {"id": "atp", "name": "ATP Tour", "country": "🌍 Mondial", "logo": ""},
            {"id": "wta", "name": "WTA Tour",  "country": "🌍 Mondial", "logo": ""},
        ],
    },
    "mma": {
        "name": "MMA / UFC", "icon": "🥊", "color": "#ff1744",
        "leagues": [
            {"id": "ufc", "name": "UFC",          "country": "🌍 Mondial", "logo": ""},
            {"id": "bel", "name": "Bellator MMA", "country": "🌍 Mondial", "logo": ""},
        ],
    },
}

# Ligues avec classement disponibles (plan gratuit football-data.org)
STANDING_LEAGUES = ["PL", "PD", "BL1", "SA", "FL1"]

# ─── Données de fallback ──────────────────────────────────────────────────────
FALLBACK_EVENTS = {
    "basketball": [
        {"idEvent":"b001","strHomeTeam":"Oklahoma City Thunder","strAwayTeam":"Denver Nuggets","dateEvent":"2026-05-04","strTime":"02:30:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b002","strHomeTeam":"Boston Celtics","strAwayTeam":"Cleveland Cavaliers","dateEvent":"2026-05-05","strTime":"01:00:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b003","strHomeTeam":"New York Knicks","strAwayTeam":"Indiana Pacers","dateEvent":"2026-05-06","strTime":"01:00:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b004","strHomeTeam":"Golden State Warriors","strAwayTeam":"Houston Rockets","dateEvent":"2026-05-07","strTime":"03:30:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b005","strHomeTeam":"TBD Est","strAwayTeam":"TBD Ouest","dateEvent":"2026-06-03","strTime":"02:30:00","strLeague":"NBA Finals","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "tennis": [
        {"idEvent":"t001","strHomeTeam":"Carlos Alcaraz","strAwayTeam":"Jannik Sinner","dateEvent":"2026-06-07","strTime":"15:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t002","strHomeTeam":"Novak Djokovic","strAwayTeam":"Holger Rune","dateEvent":"2026-06-05","strTime":"13:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t003","strHomeTeam":"Iga Swiatek","strAwayTeam":"Coco Gauff","dateEvent":"2026-06-06","strTime":"15:00:00","strLeague":"Roland Garros WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "mma": [
        {"idEvent":"m001","strHomeTeam":"Khamzat Chimaev","strAwayTeam":"Sean Strickland","dateEvent":"2026-05-09","strTime":"03:00:00","strLeague":"UFC 328","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m002","strHomeTeam":"Ilia Topuria","strAwayTeam":"Justin Gaethje","dateEvent":"2026-06-14","strTime":"02:00:00","strLeague":"UFC Freedom 250","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "football": [],
}

PRONOSTICS_TYPES = [
    "1 (Victoire domicile)", "N (Nul)", "2 (Victoire extérieur)",
    "Over 2.5 buts", "Under 2.5 buts", "BTTS (Les deux équipes marquent)",
    "Double chance 1/N", "Double chance N/2", "Handicap -1",
]
FIABILITE  = ["★★★★★ Très haute", "★★★★☆ Haute", "★★★☆☆ Moyenne", "★★☆☆☆ Modérée"]
BOOKMAKERS = ["Bet365", "Winamax", "Betclic", "Unibet", "1xBet", "Melbet"]

# ─── Statuts en direct ────────────────────────────────────────────────────────
LIVE_STATUSES = {"IN_PLAY", "PAUSED", "EXTRA_TIME", "PENALTY"}

# ─── Adaptateur football-data.org → format interne ───────────────────────────
def _fdorg_match_to_event(match, league_name):
    utc_date = match.get("utcDate", "")
    try:
        dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
    except Exception:
        date_str = utc_date[:10] if len(utc_date) >= 10 else ""
        time_str = "00:00:00"

    home  = match.get("homeTeam", {})
    away  = match.get("awayTeam", {})
    score = match.get("score", {})
    full  = score.get("fullTime", {})
    half  = score.get("halfTime", {})
    competition = match.get("competition", {})
    status = match.get("status", "")

    return {
        "idEvent":          str(match.get("id", "")),
        "strHomeTeam":      home.get("shortName") or home.get("name", "?"),
        "strAwayTeam":      away.get("shortName") or away.get("name", "?"),
        "strHomeTeamBadge": home.get("crest", ""),
        "strAwayTeamBadge": away.get("crest", ""),
        "dateEvent":        date_str,
        "strTime":          time_str,
        "strLeague":        competition.get("name", league_name),
        "strSeason":        str(match.get("season", {}).get("startDate", "")[:4]),
        "intHomeScore":     full.get("home"),
        "intAwayScore":     full.get("away"),
        "intHomeScoreHT":   half.get("home"),
        "intAwayScoreHT":   half.get("away"),
        "strStatus":        status,
        "isLive":           status in LIVE_STATUSES,
        "strVenue":         match.get("venue", "") or "",
        "matchday":         match.get("matchday", ""),
    }

# ─── Récupération des matchs ──────────────────────────────────────────────────
def get_next_events(sport_key, league, n=10):
    if sport_key != "football":
        return FALLBACK_EVENTS.get(sport_key, [])[:n]

    league_id = league["id"]
    date_from = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    date_to   = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    all_matches = []
    for status in ("SCHEDULED", "TIMED", "IN_PLAY", "PAUSED", "EXTRA_TIME", "PENALTY"):
        is_live = status in ("IN_PLAY", "PAUSED", "EXTRA_TIME", "PENALTY")
        data = _cached_get(
            f"{FOOTBALL_API}/competitions/{league_id}/matches",
            params={"status": status, "dateFrom": date_from, "dateTo": date_to},
            headers=HEADERS,
            live=is_live
        )
        all_matches.extend(data.get("matches", []))

    seen = set()
    unique = []
    for m in all_matches:
        mid = m.get("id")
        if mid not in seen:
            seen.add(mid)
            unique.append(m)
    unique.sort(key=lambda m: m.get("utcDate", ""))

    if unique:
        return [_fdorg_match_to_event(m, league["name"]) for m in unique[:n]]
    return []


def get_past_events(sport_key, league, n=10):
    if sport_key != "football":
        return []
    league_id = league["id"]
    past  = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    data = _cached_get(
        f"{FOOTBALL_API}/competitions/{league_id}/matches",
        params={"status": "FINISHED", "dateFrom": past, "dateTo": today},
        headers=HEADERS
    )
    matches = data.get("matches", [])
    matches.reverse()
    return [_fdorg_match_to_event(m, league["name"]) for m in matches[:n]]


def get_standings(league_id):
    """Récupère le classement d'une ligue. Cache 1h."""
    data = _cached_get(
        f"{FOOTBALL_API}/competitions/{league_id}/standings",
        headers=HEADERS
    )
    standings = data.get("standings", [])
    # On prend le classement "TOTAL" (pas domicile/extérieur)
    for s in standings:
        if s.get("type") == "TOTAL":
            return s.get("table", [])
    # Fallback : premier tableau disponible
    if standings:
        return standings[0].get("table", [])
    return []


def has_live_matches():
    """Vérifie s'il y a des matchs en direct toutes ligues confondues."""
    for league in SPORT_CONFIGS["football"]["leagues"]:
        data = _cached_get(
            f"{FOOTBALL_API}/competitions/{league['id']}/matches",
            params={"status": "IN_PLAY"},
            headers=HEADERS,
            live=True
        )
        if data.get("matches"):
            return True
    return False


def enrich_event(ev, league_name, sport):
    cote_1 = round(random.uniform(1.30, 4.50), 2)
    cote_n = round(random.uniform(2.80, 4.20), 2)
    cote_2 = round(random.uniform(1.25, 5.00), 2)
    return {**ev,
            "league_name": league_name or ev.get("strLeague", ""),
            "sport": sport,
            "cote_1": cote_1, "cote_n": cote_n, "cote_2": cote_2,
            "pronostic": random.choice(PRONOSTICS_TYPES),
            "fiabilite": random.choice(FIABILITE),
            "bookmaker": random.choice(BOOKMAKERS)}


def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        mois = ["","jan","fév","mar","avr","mai","juin","juil","aoû","sep","oct","nov","déc"]
        return f"{dt.day} {mois[dt.month]} {dt.year}"
    except Exception:
        return date_str or "—"

app.jinja_env.filters["format_date"] = format_date

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/sport/<sport_key>")
def sport_page(sport_key):
    cfg = SPORT_CONFIGS.get(sport_key)
    if not cfg:
        return "Sport non trouvé", 404
    leagues_data = []
    any_live = False
    for league in cfg["leagues"]:
        evts = get_next_events(sport_key, league, n=8)
        enriched = [enrich_event(ev, league["name"], sport_key) for ev in evts]
        if any(e.get("isLive") for e in enriched):
            any_live = True
        if enriched:
            leagues_data.append({"league": league, "events": enriched})
    return render_template("sport.html", sport_key=sport_key, sport_cfg=cfg,
                           leagues_data=leagues_data, sport_configs=SPORT_CONFIGS,
                           now=datetime.now(), has_live=any_live)

@app.route("/classements")
def classements():
    """Page classements en temps réel."""
    standings_data = []
    for league in SPORT_CONFIGS["football"]["leagues"]:
        if league["id"] not in STANDING_LEAGUES:
            continue
        table = get_standings(league["id"])
        if table:
            standings_data.append({"league": league, "table": table})
    return render_template("classements.html",
                           standings_data=standings_data,
                           sport_configs=SPORT_CONFIGS,
                           now=datetime.now())

@app.route("/match/<event_id>")
def match_detail(event_id):
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    ev  = {}
    if sport_key == "football":
        data = _cached_get(f"{FOOTBALL_API}/matches/{event_id}", headers=HEADERS,
                           live=True)
        if data and "id" in data:
            ev = _fdorg_match_to_event(data, cfg["leagues"][0]["name"])
    if not ev:
        for fb_ev in FALLBACK_EVENTS.get(sport_key, []):
            if fb_ev.get("idEvent") == event_id:
                ev = fb_ev
                break
    enriched = enrich_event(ev, ev.get("strLeague", ""), sport_key)
    return render_template("match.html",
                           event=enriched,
                           sport_cfg=cfg, sport_configs=SPORT_CONFIGS,
                           now=datetime.now(),
                           has_live=enriched.get("isLive", False))

@app.route("/api/live")
def api_live():
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    events = []
    for league in cfg["leagues"][:2]:
        events.extend(get_next_events(sport_key, league, n=5)[:5])
    return jsonify({"events": events[:15]})

@app.route("/api/scores")
def api_scores():
    """Endpoint JSON des scores en direct — appelé par le JS toutes les 60s."""
    league_id = request.args.get("league", "PL")
    data = _cached_get(
        f"{FOOTBALL_API}/competitions/{league_id}/matches",
        params={"status": "IN_PLAY"},
        headers=HEADERS,
        live=True
    )
    matches = data.get("matches", [])
    events = [_fdorg_match_to_event(m, league_id) for m in matches]
    return jsonify({"live": events, "count": len(events),
                    "updated": datetime.now().strftime("%H:%M:%S")})

@app.route("/api/standings/<league_id>")
def api_standings(league_id):
    """Endpoint JSON classement — appelé par le JS."""
    table = get_standings(league_id)
    return jsonify({"league": league_id, "table": table,
                    "updated": datetime.now().strftime("%H:%M:%S")})

@app.route("/pronostics")
def pronostics():
    all_events = []
    for sport_key, sport_cfg in SPORT_CONFIGS.items():
        for league in sport_cfg["leagues"][:3]:
            for ev in get_next_events(sport_key, league, n=4)[:4]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    return render_template("pronostics.html", events=all_events,
                           sport_configs=SPORT_CONFIGS, now=datetime.now())

@app.route("/resultats")
def resultats():
    all_events = []
    for sport_key in ("football", "basketball"):
        for league in SPORT_CONFIGS[sport_key]["leagues"][:2]:
            for ev in get_past_events(sport_key, league, n=5)[:3]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    return render_template("resultats.html", events=all_events,
                           sport_configs=SPORT_CONFIGS, now=datetime.now())

@app.route("/api/status")
def api_status():
    data = _cached_get(f"{FOOTBALL_API}/competitions/PL", headers=HEADERS)
    return jsonify({
        "api": "football-data.org",
        "status": "ok" if "id" in data else "error",
        "competition_test": data.get("name", "?"),
        "current_season": data.get("currentSeason", {})
    })

@app.route("/api/debug")
def api_debug():
    today  = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    past   = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    results = {}
    d1 = requests.get(f"{FOOTBALL_API}/competitions/PL", headers=HEADERS, timeout=12)
    r1 = d1.json()
    results["competition_PL"] = {"http_status": d1.status_code, "name": r1.get("name"), "current_season": r1.get("currentSeason", {})}
    d2 = requests.get(f"{FOOTBALL_API}/competitions/PL/matches",
                      params={"status": "SCHEDULED", "dateFrom": today, "dateTo": future},
                      headers=HEADERS, timeout=12)
    r2 = d2.json()
    results["PL_scheduled"] = {"http_status": d2.status_code, "count": len(r2.get("matches", [])), "error": r2.get("message")}
    d3 = requests.get(f"{FOOTBALL_API}/competitions/PL/standings", headers=HEADERS, timeout=12)
    r3 = d3.json()
    standings = r3.get("standings", [])
    total = next((s for s in standings if s.get("type") == "TOTAL"), {})
    results["PL_standings"] = {"http_status": d3.status_code, "rows": len(total.get("table", [])), "error": r3.get("message")}
    d4 = requests.get(f"{FOOTBALL_API}/competitions/PL/matches",
                      params={"status": "IN_PLAY"},
                      headers=HEADERS, timeout=12)
    r4 = d4.json()
    results["PL_live"] = {"http_status": d4.status_code, "count": len(r4.get("matches", [])), "error": r4.get("message")}
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
