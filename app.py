"""
SportyPro CI — Site de pronostics sportifs
Crédité par Kouakou Cedric
Propulsé par API-Sports (api-sports.io) — Vrais matchs en temps réel
"""
from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime
import random
import os
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sportytrader-cedric-2026")

# ─── Clé API-Sports ──────────────────────────────────────────────────────────
# ⚠️  Sur Render.com : Settings → Environment → ajouter APISPORTS_KEY = ta_clé
API_KEY = os.environ.get("APISPORTS_KEY", "04c7c3b7344e0823b3c23dbf69dc7bc2")
HEADERS = {"x-apisports-key": API_KEY}

FOOTBALL_API   = "https://v3.football.api-sports.io"
BASKETBALL_API = "https://v1.basketball.api-sports.io"

# ─── Cache mémoire (protège les 100 req/jour du plan gratuit) ────────────────
_CACHE    = {}
CACHE_TTL = 3600  # 1 heure

def _cached_get(url, params=None, headers=None):
    key = url + str(sorted((params or {}).items()))
    now = time.time()
    if key in _CACHE and now - _CACHE[key]["ts"] < CACHE_TTL:
        return _CACHE[key]["data"]
    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        data = r.json()
        _CACHE[key] = {"data": data, "ts": now}
        return data
    except Exception as e:
        print(f"[API-Sports] Erreur {url}: {e}")
        return {}

# ─── Configuration sports ────────────────────────────────────────────────────
# CORRECTION CRITIQUE : season=2025 = saison 2025/2026 (en cours en mai 2026)
SPORT_CONFIGS = {
    "football": {
        "name": "Football", "icon": "⚽", "color": "#00e676",
        "leagues": [
            {"id": "39",  "name": "Premier League",      "country": "🏴 Angleterre", "season": "2025", "logo": "https://media.api-sports.io/football/leagues/39.png"},
            {"id": "140", "name": "La Liga",              "country": "🇪🇸 Espagne",   "season": "2025", "logo": "https://media.api-sports.io/football/leagues/140.png"},
            {"id": "78",  "name": "Bundesliga",           "country": "🇩🇪 Allemagne", "season": "2025", "logo": "https://media.api-sports.io/football/leagues/78.png"},
            {"id": "135", "name": "Serie A",              "country": "🇮🇹 Italie",    "season": "2025", "logo": "https://media.api-sports.io/football/leagues/135.png"},
            {"id": "61",  "name": "Ligue 1",              "country": "🇫🇷 France",    "season": "2025", "logo": "https://media.api-sports.io/football/leagues/61.png"},
            {"id": "2",   "name": "Champions League",     "country": "🏆 Europe",     "season": "2025", "logo": "https://media.api-sports.io/football/leagues/2.png"},
            {"id": "3",   "name": "Europa League",        "country": "🏆 Europe",     "season": "2025", "logo": "https://media.api-sports.io/football/leagues/3.png"},
            {"id": "253", "name": "MLS",                  "country": "🇺🇸 USA",       "season": "2026", "logo": "https://media.api-sports.io/football/leagues/253.png"},
            {"id": "12",  "name": "CAF Champions League", "country": "🌍 Afrique",    "season": "2025", "logo": "https://media.api-sports.io/football/leagues/12.png"},
        ],
    },
    "basketball": {
        "name": "Basketball", "icon": "🏀", "color": "#ff6d00",
        "leagues": [
            {"id": "12",  "name": "NBA",       "country": "🇺🇸 USA",    "season": "2025-2026", "logo": "https://media.api-sports.io/basketball/leagues/12.png"},
            {"id": "120", "name": "Euroleague", "country": "🇪🇺 Europe", "season": "2025-2026", "logo": "https://media.api-sports.io/basketball/leagues/120.png"},
        ],
    },
    "tennis": {
        "name": "Tennis", "icon": "🎾", "color": "#c6ff00",
        "leagues": [
            {"id": "atp", "name": "ATP Tour", "country": "🌍 Mondial", "season": "2026", "logo": ""},
            {"id": "wta", "name": "WTA Tour",  "country": "🌍 Mondial", "season": "2026", "logo": ""},
        ],
    },
    "mma": {
        "name": "MMA / UFC", "icon": "🥊", "color": "#ff1744",
        "leagues": [
            {"id": "ufc", "name": "UFC",          "country": "🌍 Mondial", "season": "2026", "logo": ""},
            {"id": "bel", "name": "Bellator MMA", "country": "🌍 Mondial", "season": "2026", "logo": ""},
        ],
    },
}

# ─── Données de fallback (si API échoue ou quota épuisé) ─────────────────────
FALLBACK_EVENTS = {
    "football": [
        {"idEvent":"f001","strHomeTeam":"Real Madrid","strAwayTeam":"Arsenal","dateEvent":"2026-05-07","strTime":"21:00:00","strLeague":"Champions League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/541.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/42.png"},
        {"idEvent":"f002","strHomeTeam":"Paris Saint-Germain","strAwayTeam":"Bayern Munich","dateEvent":"2026-05-08","strTime":"21:00:00","strLeague":"Champions League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/85.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/157.png"},
        {"idEvent":"f003","strHomeTeam":"Manchester United","strAwayTeam":"Liverpool","dateEvent":"2026-05-10","strTime":"17:30:00","strLeague":"Premier League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/33.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/40.png"},
        {"idEvent":"f004","strHomeTeam":"Arsenal","strAwayTeam":"Manchester City","dateEvent":"2026-05-10","strTime":"16:00:00","strLeague":"Premier League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/42.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/50.png"},
        {"idEvent":"f005","strHomeTeam":"Chelsea","strAwayTeam":"Tottenham","dateEvent":"2026-05-17","strTime":"16:00:00","strLeague":"Premier League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/49.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/47.png"},
        {"idEvent":"f006","strHomeTeam":"FC Barcelone","strAwayTeam":"Atletico Madrid","dateEvent":"2026-05-09","strTime":"21:00:00","strLeague":"La Liga","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/529.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/530.png"},
        {"idEvent":"f007","strHomeTeam":"Real Madrid","strAwayTeam":"Villarreal","dateEvent":"2026-05-16","strTime":"21:00:00","strLeague":"La Liga","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/541.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/533.png"},
        {"idEvent":"f008","strHomeTeam":"PSG","strAwayTeam":"Olympique de Marseille","dateEvent":"2026-05-10","strTime":"21:00:00","strLeague":"Ligue 1","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/85.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/81.png"},
        {"idEvent":"f009","strHomeTeam":"Olympique Lyonnais","strAwayTeam":"Monaco","dateEvent":"2026-05-16","strTime":"17:00:00","strLeague":"Ligue 1","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/80.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/91.png"},
        {"idEvent":"f010","strHomeTeam":"Bayern Munich","strAwayTeam":"Bayer Leverkusen","dateEvent":"2026-05-09","strTime":"18:30:00","strLeague":"Bundesliga","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/157.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/168.png"},
        {"idEvent":"f011","strHomeTeam":"Inter Milan","strAwayTeam":"AC Milan","dateEvent":"2026-05-10","strTime":"20:45:00","strLeague":"Serie A","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/505.png","strAwayTeamBadge":"https://media.api-sports.io/football/teams/489.png"},
        {"idEvent":"f012","strHomeTeam":"TBD Europa League","strAwayTeam":"TBD Europa League","dateEvent":"2026-05-20","strTime":"21:00:00","strLeague":"Europa League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f013","strHomeTeam":"TBD Champions League","strAwayTeam":"TBD Champions League","dateEvent":"2026-05-30","strTime":"21:00:00","strLeague":"Champions League","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f014","strHomeTeam":"Real Madrid","strAwayTeam":"Al Hilal","dateEvent":"2026-06-15","strTime":"21:00:00","strLeague":"Coupe du Monde des Clubs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/541.png","strAwayTeamBadge":""},
        {"idEvent":"f015","strHomeTeam":"Manchester City","strAwayTeam":"Flamengo","dateEvent":"2026-06-18","strTime":"00:00:00","strLeague":"Coupe du Monde des Clubs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/football/teams/50.png","strAwayTeamBadge":""},
    ],
    "basketball": [
        {"idEvent":"b001","strHomeTeam":"Oklahoma City Thunder","strAwayTeam":"San Antonio Spurs","dateEvent":"2026-05-04","strTime":"02:30:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/basketball/teams/140.png","strAwayTeamBadge":"https://media.api-sports.io/basketball/teams/26.png"},
        {"idEvent":"b002","strHomeTeam":"Los Angeles Lakers","strAwayTeam":"Houston Rockets","dateEvent":"2026-05-05","strTime":"02:30:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/basketball/teams/13.png","strAwayTeamBadge":"https://media.api-sports.io/basketball/teams/8.png"},
        {"idEvent":"b003","strHomeTeam":"Boston Celtics","strAwayTeam":"Philadelphia 76ers","dateEvent":"2026-05-06","strTime":"01:00:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/basketball/teams/2.png","strAwayTeamBadge":"https://media.api-sports.io/basketball/teams/21.png"},
        {"idEvent":"b004","strHomeTeam":"New York Knicks","strAwayTeam":"Minnesota Timberwolves","dateEvent":"2026-05-07","strTime":"01:00:00","strLeague":"NBA Playoffs","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"https://media.api-sports.io/basketball/teams/20.png","strAwayTeamBadge":"https://media.api-sports.io/basketball/teams/16.png"},
        {"idEvent":"b005","strHomeTeam":"TBD Est","strAwayTeam":"TBD Ouest","dateEvent":"2026-06-03","strTime":"02:30:00","strLeague":"NBA Finals","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b006","strHomeTeam":"Real Madrid","strAwayTeam":"Panathinaikos","dateEvent":"2026-05-08","strTime":"20:00:00","strLeague":"Euroleague","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b007","strHomeTeam":"Fenerbahce","strAwayTeam":"Olympiacos","dateEvent":"2026-05-09","strTime":"19:00:00","strLeague":"Euroleague","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "tennis": [
        {"idEvent":"t001","strHomeTeam":"Carlos Alcaraz","strAwayTeam":"Jannik Sinner","dateEvent":"2026-06-07","strTime":"15:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t002","strHomeTeam":"Novak Djokovic","strAwayTeam":"Holger Rune","dateEvent":"2026-06-05","strTime":"13:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t003","strHomeTeam":"Iga Swiatek","strAwayTeam":"Coco Gauff","dateEvent":"2026-06-06","strTime":"15:00:00","strLeague":"Roland Garros WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t004","strHomeTeam":"Aryna Sabalenka","strAwayTeam":"Elena Rybakina","dateEvent":"2026-06-04","strTime":"13:00:00","strLeague":"Roland Garros WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t005","strHomeTeam":"Jannik Sinner","strAwayTeam":"Carlos Alcaraz","dateEvent":"2026-07-12","strTime":"15:00:00","strLeague":"Wimbledon","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t006","strHomeTeam":"Iga Swiatek","strAwayTeam":"Aryna Sabalenka","dateEvent":"2026-07-11","strTime":"14:00:00","strLeague":"Wimbledon WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "mma": [
        {"idEvent":"m001","strHomeTeam":"Jack Della Maddalena","strAwayTeam":"Carlos Prates","dateEvent":"2026-05-02","strTime":"13:00:00","strLeague":"UFC Fight Night","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m002","strHomeTeam":"Khamzat Chimaev","strAwayTeam":"Sean Strickland","dateEvent":"2026-05-09","strTime":"03:00:00","strLeague":"UFC 328","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m003","strHomeTeam":"Ilia Topuria","strAwayTeam":"Justin Gaethje","dateEvent":"2026-06-14","strTime":"02:00:00","strLeague":"UFC Freedom 250","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m004","strHomeTeam":"Islam Makhachev","strAwayTeam":"TBD","dateEvent":"2026-08-01","strTime":"22:00:00","strLeague":"UFC 329","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m005","strHomeTeam":"Alexandre Pantoja","strAwayTeam":"Joshua Van","dateEvent":"2026-08-15","strTime":"03:00:00","strLeague":"UFC 330","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
}

PRONOSTICS_TYPES = [
    "1 (Victoire domicile)", "N (Nul)", "2 (Victoire extérieur)",
    "Over 2.5 buts", "Under 2.5 buts", "BTTS (Les deux équipes marquent)",
    "Double chance 1/N", "Double chance N/2", "Handicap -1",
]
FIABILITE  = ["★★★★★ Très haute", "★★★★☆ Haute", "★★★☆☆ Moyenne", "★★☆☆☆ Modérée"]
BOOKMAKERS = ["Bet365", "Winamax", "Betclic", "Unibet", "1xBet", "Melbet"]

# ─── Adaptateurs API → format interne ────────────────────────────────────────

def _parse_date(date_iso):
    try:
        dt = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
    except Exception:
        return (date_iso[:10] if len(date_iso) >= 10 else ""), "00:00:00"

def _football_fixture_to_event(fix, league_name):
    f   = fix.get("fixture", {})
    tms = fix.get("teams", {})
    gls = fix.get("goals", {})
    lg  = fix.get("league", {})
    date_str, time_str = _parse_date(f.get("date", ""))
    return {
        "idEvent":          str(f.get("id", "")),
        "strHomeTeam":      tms.get("home", {}).get("name", "?"),
        "strAwayTeam":      tms.get("away", {}).get("name", "?"),
        "strHomeTeamBadge": tms.get("home", {}).get("logo", ""),
        "strAwayTeamBadge": tms.get("away", {}).get("logo", ""),
        "dateEvent":        date_str,
        "strTime":          time_str,
        "strLeague":        lg.get("name", league_name),
        "strSeason":        str(lg.get("season", "")),
        "intHomeScore":     gls.get("home"),
        "intAwayScore":     gls.get("away"),
        "strStatus":        f.get("status", {}).get("long", ""),
        "strVenue":         f.get("venue", {}).get("name", ""),
    }

def _basketball_game_to_event(game, league_name):
    tms = game.get("teams", {})
    sc  = game.get("scores", {})
    lg  = game.get("league", {})
    date_str, time_str = _parse_date(game.get("date", ""))
    return {
        "idEvent":          str(game.get("id", "")),
        "strHomeTeam":      tms.get("home", {}).get("name", "?"),
        "strAwayTeam":      tms.get("away", {}).get("name", "?"),
        "strHomeTeamBadge": tms.get("home", {}).get("logo", ""),
        "strAwayTeamBadge": tms.get("away", {}).get("logo", ""),
        "dateEvent":        date_str,
        "strTime":          time_str,
        "strLeague":        lg.get("name", league_name),
        "strSeason":        str(lg.get("season", "")),
        "intHomeScore":     sc.get("home", {}).get("total"),
        "intAwayScore":     sc.get("away", {}).get("total"),
        "strStatus":        game.get("status", {}).get("long", ""),
        "strVenue":         "",
    }

# ─── Récupération des données ─────────────────────────────────────────────────

def get_next_events(sport_key, league, n=10):
    """Vrais matchs via API-Sports — fallback automatique si API vide/quota épuisé."""
    lid = league["id"]
    sea = league.get("season", "2025")
    today = datetime.now().strftime("%Y-%m-%d")
    # Chercher les matchs sur les 30 prochains jours
    from datetime import timedelta
    future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    if sport_key == "football":
        # Essai 1 : avec "next"
        data = _cached_get(f"{FOOTBALL_API}/fixtures",
                           params={"league": lid, "season": sea, "next": n},
                           headers=HEADERS)
        raw = data.get("response", [])
        if not raw:
            # Essai 2 : avec plage de dates from/to
            data = _cached_get(f"{FOOTBALL_API}/fixtures",
                               params={"league": lid, "season": sea, "from": today, "to": future},
                               headers=HEADERS)
            raw = data.get("response", [])
        if not raw:
            # Essai 3 : toute la saison (sans filtre de date)
            data = _cached_get(f"{FOOTBALL_API}/fixtures",
                               params={"league": lid, "season": sea},
                               headers=HEADERS)
            raw = data.get("response", [])
            # Filtrer les matchs futurs
            raw = [f for f in raw if f.get("fixture", {}).get("date", "") >= today]
        if raw:
            return [_football_fixture_to_event(f, league["name"]) for f in raw[:n]]
        # Fallback : filtrer par ligue ou retourner tout
        fb = [ev for ev in FALLBACK_EVENTS["football"]
              if league["name"].lower() in ev.get("strLeague","").lower()
              or ev.get("strLeague","").lower() in league["name"].lower()]
        return fb[:n] if fb else FALLBACK_EVENTS["football"][:n]

    if sport_key == "basketball":
        # Essai 1 : avec "next"
        data = _cached_get(f"{BASKETBALL_API}/games",
                           params={"league": lid, "season": sea, "next": n},
                           headers=HEADERS)
        raw = data.get("response", [])
        if not raw:
            # Essai 2 : avec plage de dates
            data = _cached_get(f"{BASKETBALL_API}/games",
                               params={"league": lid, "season": sea, "date": today},
                               headers=HEADERS)
            raw = data.get("response", [])
        if not raw:
            # Essai 3 : toute la saison
            data = _cached_get(f"{BASKETBALL_API}/games",
                               params={"league": lid, "season": sea},
                               headers=HEADERS)
            raw = data.get("response", [])
            raw = [g for g in raw if g.get("date", "") >= today]
        if raw:
            return [_basketball_game_to_event(g, league["name"]) for g in raw[:n]]
        return FALLBACK_EVENTS["basketball"][:n]

    return FALLBACK_EVENTS.get(sport_key, [])[:n]


def get_past_events(sport_key, league, n=10):
    lid = league["id"]
    sea = league.get("season", "2025")
    if sport_key == "football":
        data = _cached_get(f"{FOOTBALL_API}/fixtures",
                           params={"league": lid, "season": sea, "last": n},
                           headers=HEADERS)
        return [_football_fixture_to_event(f, league["name"]) for f in data.get("response", [])]
    if sport_key == "basketball":
        data = _cached_get(f"{BASKETBALL_API}/games",
                           params={"league": lid, "season": sea, "last": n},
                           headers=HEADERS)
        return [_basketball_game_to_event(g, league["name"]) for g in data.get("response", [])]
    return []


def enrich_event(ev, league_name, sport):
    cote_1 = round(random.uniform(1.30, 4.50), 2)
    cote_n = round(random.uniform(2.80, 4.20), 2)
    cote_2 = round(random.uniform(1.25, 5.00), 2)
    return {**ev, "league_name": league_name or ev.get("strLeague", ""), "sport": sport,
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
def index():
    all_events = []
    for league in SPORT_CONFIGS["football"]["leagues"][:2]:
        for ev in get_next_events("football", league, n=3)[:3]:
            all_events.append(enrich_event(ev, league["name"], "football"))
    nba = SPORT_CONFIGS["basketball"]["leagues"][0]
    for ev in get_next_events("basketball", nba, n=3)[:3]:
        all_events.append(enrich_event(ev, nba["name"], "basketball"))
    for sport_key in ("tennis", "mma"):
        for ev in FALLBACK_EVENTS.get(sport_key, [])[:2]:
            all_events.append(enrich_event(ev, ev.get("strLeague", ""), sport_key))
    random.shuffle(all_events)
    return render_template("index.html", events=all_events[:20],
                           sport_configs=SPORT_CONFIGS, now=datetime.now())

@app.route("/sport/<sport_key>")
def sport_page(sport_key):
    cfg = SPORT_CONFIGS.get(sport_key)
    if not cfg:
        return "Sport non trouvé", 404
    leagues_data = []
    for league in cfg["leagues"]:
        evts = get_next_events(sport_key, league, n=8)
        enriched = [enrich_event(ev, league["name"], sport_key) for ev in evts]
        if enriched:
            leagues_data.append({"league": league, "events": enriched})
    return render_template("sport.html", sport_key=sport_key, sport_cfg=cfg,
                           leagues_data=leagues_data, sport_configs=SPORT_CONFIGS,
                           now=datetime.now())

@app.route("/match/<event_id>")
def match_detail(event_id):
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    ev  = {}
    if sport_key == "football":
        data = _cached_get(f"{FOOTBALL_API}/fixtures", params={"id": event_id}, headers=HEADERS)
        raw  = data.get("response", [])
        if raw:
            ev = _football_fixture_to_event(raw[0], cfg["leagues"][0]["name"])
    elif sport_key == "basketball":
        data = _cached_get(f"{BASKETBALL_API}/games", params={"id": event_id}, headers=HEADERS)
        raw  = data.get("response", [])
        if raw:
            ev = _basketball_game_to_event(raw[0], cfg["leagues"][0]["name"])
    if not ev:
        for fb_ev in FALLBACK_EVENTS.get(sport_key, []):
            if fb_ev.get("idEvent") == event_id:
                ev = fb_ev
                break
    return render_template("match.html", event=enrich_event(ev, ev.get("strLeague",""), sport_key),
                           sport_cfg=cfg, sport_configs=SPORT_CONFIGS, now=datetime.now())

@app.route("/api/live")
def api_live():
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    events = []
    for league in cfg["leagues"][:2]:
        events.extend(get_next_events(sport_key, league, n=5)[:5])
    return jsonify({"events": events[:15]})

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
    data = _cached_get(f"{FOOTBALL_API}/status", headers=HEADERS)
    return jsonify(data)

@app.route("/api/debug")
def api_debug():
    """Diagnostic complet : teste chaque méthode d'appel API pour trouver laquelle marche."""
    today = datetime.now().strftime("%Y-%m-%d")
    from datetime import timedelta
    future = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    results = {}

    # Test 1 : status
    results["status"] = _cached_get(f"{FOOTBALL_API}/status", headers=HEADERS)

    # Test 2 : fixtures avec "next"
    d = requests.get(f"{FOOTBALL_API}/fixtures",
                     params={"league": "39", "season": "2025", "next": 5},
                     headers=HEADERS, timeout=12)
    r2 = d.json()
    results["fixtures_next"] = {"params_used": "league=39&season=2025&next=5",
                                 "count": len(r2.get("response", [])),
                                 "errors": r2.get("errors", []),
                                 "sample": r2.get("response", [])[:1]}

    # Test 3 : fixtures avec from/to
    d = requests.get(f"{FOOTBALL_API}/fixtures",
                     params={"league": "39", "season": "2025", "from": today, "to": future},
                     headers=HEADERS, timeout=12)
    r3 = d.json()
    results["fixtures_from_to"] = {"params_used": f"league=39&season=2025&from={today}&to={future}",
                                    "count": len(r3.get("response", [])),
                                    "errors": r3.get("errors", []),
                                    "sample": r3.get("response", [])[:1]}

    # Test 4 : fixtures saison entière (sans filtre date)
    d = requests.get(f"{FOOTBALL_API}/fixtures",
                     params={"league": "39", "season": "2025"},
                     headers=HEADERS, timeout=12)
    r4 = d.json()
    results["fixtures_season_only"] = {"params_used": "league=39&season=2025",
                                        "count": len(r4.get("response", [])),
                                        "errors": r4.get("errors", [])}

    # Test 5 : basketball NBA
    d = requests.get(f"{BASKETBALL_API}/games",
                     params={"league": "12", "season": "2025-2026", "next": 5},
                     headers=HEADERS, timeout=12)
    r5 = d.json()
    results["basketball_next"] = {"params_used": "league=12&season=2025-2026&next=5",
                                   "count": len(r5.get("response", [])),
                                   "errors": r5.get("errors", []),
                                   "sample": r5.get("response", [])[:1]}

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
