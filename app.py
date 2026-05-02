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
# Sur Render.com : Settings → Environment → Add APISPORTS_KEY = ta_clé
API_KEY  = os.environ.get("APISPORTS_KEY", "04c7c3b7344e0823b3c23dbf69dc7bc2")
HEADERS  = {"x-apisports-key": API_KEY}

FOOTBALL_API   = "https://v3.football.api-sports.io"
BASKETBALL_API = "https://v1.basketball.api-sports.io"

# ─── Cache mémoire — protège les 100 requêtes/jour du plan gratuit ───────────
_CACHE    = {}
CACHE_TTL = 3600  # 1 heure

def _cached_get(url: str, params: dict = None, headers: dict = None) -> dict:
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

# ─── Configuration des sports ────────────────────────────────────────────────
# Les IDs football/basketball correspondent à api-sports.io
SPORT_CONFIGS = {
    "football": {
        "name": "Football",
        "icon": "⚽",
        "color": "#00e676",
        "leagues": [
            {"id": "39",  "name": "Premier League",      "country": "🏴 Angleterre", "season": "2024", "logo": "https://media.api-sports.io/football/leagues/39.png"},
            {"id": "140", "name": "La Liga",              "country": "🇪🇸 Espagne",   "season": "2024", "logo": "https://media.api-sports.io/football/leagues/140.png"},
            {"id": "78",  "name": "Bundesliga",           "country": "🇩🇪 Allemagne", "season": "2024", "logo": "https://media.api-sports.io/football/leagues/78.png"},
            {"id": "135", "name": "Serie A",              "country": "🇮🇹 Italie",    "season": "2024", "logo": "https://media.api-sports.io/football/leagues/135.png"},
            {"id": "61",  "name": "Ligue 1",              "country": "🇫🇷 France",    "season": "2024", "logo": "https://media.api-sports.io/football/leagues/61.png"},
            {"id": "2",   "name": "Champions League",     "country": "🏆 Europe",     "season": "2024", "logo": "https://media.api-sports.io/football/leagues/2.png"},
            {"id": "3",   "name": "Europa League",        "country": "🏆 Europe",     "season": "2024", "logo": "https://media.api-sports.io/football/leagues/3.png"},
            {"id": "253", "name": "MLS",                  "country": "🇺🇸 USA",       "season": "2025", "logo": "https://media.api-sports.io/football/leagues/253.png"},
            {"id": "12",  "name": "CAF Champions League", "country": "🌍 Afrique",    "season": "2024", "logo": "https://media.api-sports.io/football/leagues/12.png"},
        ],
    },
    "basketball": {
        "name": "Basketball",
        "icon": "🏀",
        "color": "#ff6d00",
        "leagues": [
            {"id": "12",  "name": "NBA",       "country": "🇺🇸 USA",    "season": "2024-2025", "logo": "https://media.api-sports.io/basketball/leagues/12.png"},
            {"id": "120", "name": "Euroleague", "country": "🇪🇺 Europe", "season": "2024-2025", "logo": "https://media.api-sports.io/basketball/leagues/120.png"},
        ],
    },
    "tennis": {
        "name": "Tennis",
        "icon": "🎾",
        "color": "#c6ff00",
        "leagues": [
            {"id": "atp", "name": "ATP Tour", "country": "🌍 Mondial", "season": "2026", "logo": ""},
            {"id": "wta", "name": "WTA Tour",  "country": "🌍 Mondial", "season": "2026", "logo": ""},
        ],
    },
    "mma": {
        "name": "MMA / UFC",
        "icon": "🥊",
        "color": "#ff1744",
        "leagues": [
            {"id": "ufc", "name": "UFC",          "country": "🌍 Mondial", "season": "2026", "logo": ""},
            {"id": "bel", "name": "Bellator MMA", "country": "🌍 Mondial", "season": "2026", "logo": ""},
        ],
    },
}

# ─── Données de fallback Tennis / MMA (non dispo sur plan gratuit API-Sports) ─
FALLBACK_EVENTS = {
    "tennis": [
        {"idEvent":"t001","strHomeTeam":"Carlos Alcaraz","strAwayTeam":"Jannik Sinner","dateEvent":"2026-06-07","strTime":"15:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t002","strHomeTeam":"Novak Djokovic","strAwayTeam":"Holger Rune","dateEvent":"2026-06-05","strTime":"13:00:00","strLeague":"Roland Garros","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t003","strHomeTeam":"Iga Swiatek","strAwayTeam":"Coco Gauff","dateEvent":"2026-06-06","strTime":"15:00:00","strLeague":"Roland Garros WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t004","strHomeTeam":"Aryna Sabalenka","strAwayTeam":"Elena Rybakina","dateEvent":"2026-06-04","strTime":"13:00:00","strLeague":"Roland Garros WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t005","strHomeTeam":"Jannik Sinner","strAwayTeam":"Carlos Alcaraz","dateEvent":"2026-07-12","strTime":"15:00:00","strLeague":"Wimbledon","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t006","strHomeTeam":"Iga Swiatek","strAwayTeam":"Aryna Sabalenka","dateEvent":"2026-07-11","strTime":"14:00:00","strLeague":"Wimbledon WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t007","strHomeTeam":"Carlos Alcaraz","strAwayTeam":"Daniil Medvedev","dateEvent":"2026-09-13","strTime":"22:00:00","strLeague":"US Open","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t008","strHomeTeam":"Coco Gauff","strAwayTeam":"Iga Swiatek","dateEvent":"2026-09-12","strTime":"22:00:00","strLeague":"US Open WTA","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
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

# ─── Adaptateurs API-Sports → format interne ─────────────────────────────────

def _parse_fixture_date(date_iso: str):
    """Extrait YYYY-MM-DD et HH:MM:SS depuis une date ISO 8601."""
    try:
        dt = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
    except Exception:
        return date_iso[:10] if len(date_iso) >= 10 else "", "00:00:00"


def _football_fixture_to_event(fix: dict, league_name: str) -> dict:
    """Convertit un fixture API-Football en format interne."""
    f   = fix.get("fixture", {})
    tms = fix.get("teams", {})
    gls = fix.get("goals", {})
    lg  = fix.get("league", {})
    date_str, time_str = _parse_fixture_date(f.get("date", ""))
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


def _basketball_game_to_event(game: dict, league_name: str) -> dict:
    """Convertit un game API-Basketball en format interne."""
    tms = game.get("teams", {})
    sc  = game.get("scores", {})
    lg  = game.get("league", {})
    date_str, time_str = _parse_fixture_date(game.get("date", ""))
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

# ─── Fonctions de récupération de données ────────────────────────────────────

def get_football_fixtures(league_id: str, season: str, mode: str = "next", n: int = 10) -> list:
    """
    mode='next'  → prochains matchs
    mode='last'  → derniers matchs joués
    """
    params = {"league": league_id, "season": season}
    params[mode] = n
    data = _cached_get(f"{FOOTBALL_API}/fixtures", params=params, headers=HEADERS)
    return data.get("response", [])


def get_basketball_games(league_id: str, season: str, mode: str = "next", n: int = 10) -> list:
    params = {"league": league_id, "season": season}
    params[mode] = n
    data = _cached_get(f"{BASKETBALL_API}/games", params=params, headers=HEADERS)
    return data.get("response", [])


def get_next_events(sport_key: str, league: dict, n: int = 10) -> list:
    """Récupère les prochains matchs selon le sport. Retourne une liste d'events normalisés."""
    lid = league["id"]
    sea = league.get("season", "2024")

    if sport_key == "football":
        raw = get_football_fixtures(lid, sea, "next", n)
        return [_football_fixture_to_event(f, league["name"]) for f in raw]

    if sport_key == "basketball":
        raw = get_basketball_games(lid, sea, "next", n)
        return [_basketball_game_to_event(g, league["name"]) for g in raw]

    # Tennis / MMA → fallback données curatées
    return [ev for ev in FALLBACK_EVENTS.get(sport_key, [])]


def get_past_events(sport_key: str, league: dict, n: int = 10) -> list:
    """Récupère les derniers matchs joués."""
    lid = league["id"]
    sea = league.get("season", "2024")

    if sport_key == "football":
        raw = get_football_fixtures(lid, sea, "last", n)
        return [_football_fixture_to_event(f, league["name"]) for f in raw]

    if sport_key == "basketball":
        raw = get_basketball_games(lid, sea, "last", n)
        return [_basketball_game_to_event(g, league["name"]) for g in raw]

    return []


def enrich_event(ev: dict, league_name: str, sport: str) -> dict:
    """Ajoute les données de pronostic à un match."""
    cote_1 = round(random.uniform(1.30, 4.50), 2)
    cote_n = round(random.uniform(2.80, 4.20), 2)
    cote_2 = round(random.uniform(1.25, 5.00), 2)
    return {
        **ev,
        "league_name": league_name or ev.get("strLeague", ""),
        "sport":       sport,
        "cote_1":      cote_1,
        "cote_n":      cote_n,
        "cote_2":      cote_2,
        "pronostic":   random.choice(PRONOSTICS_TYPES),
        "fiabilite":   random.choice(FIABILITE),
        "bookmaker":   random.choice(BOOKMAKERS),
    }


def format_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        mois = ["", "jan", "fév", "mar", "avr", "mai", "juin",
                "juil", "aoû", "sep", "oct", "nov", "déc"]
        return f"{dt.day} {mois[dt.month]} {dt.year}"
    except Exception:
        return date_str or "—"


app.jinja_env.filters["format_date"] = format_date

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    all_events = []
    # Football : 2 premières ligues → 3 matchs chacune
    for league in SPORT_CONFIGS["football"]["leagues"][:2]:
        evts = get_next_events("football", league, n=3)
        for ev in evts[:3]:
            all_events.append(enrich_event(ev, league["name"], "football"))

    # Basketball : NBA → 3 matchs
    nba = SPORT_CONFIGS["basketball"]["leagues"][0]
    for ev in get_next_events("basketball", nba, n=3)[:3]:
        all_events.append(enrich_event(ev, nba["name"], "basketball"))

    # Tennis / MMA : fallback
    for sport_key in ("tennis", "mma"):
        for ev in FALLBACK_EVENTS.get(sport_key, [])[:2]:
            all_events.append(enrich_event(ev, ev.get("strLeague", ""), sport_key))

    random.shuffle(all_events)
    return render_template(
        "index.html",
        events=all_events[:20],
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )


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

    return render_template(
        "sport.html",
        sport_key=sport_key,
        sport_cfg=cfg,
        leagues_data=leagues_data,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )


@app.route("/match/<event_id>")
def match_detail(event_id):
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    ev = {}

    if sport_key == "football":
        data = _cached_get(f"{FOOTBALL_API}/fixtures", params={"id": event_id}, headers=HEADERS)
        fixtures = data.get("response", [])
        if fixtures:
            league = cfg["leagues"][0]
            ev = _football_fixture_to_event(fixtures[0], league["name"])
    elif sport_key == "basketball":
        data = _cached_get(f"{BASKETBALL_API}/games", params={"id": event_id}, headers=HEADERS)
        games = data.get("response", [])
        if games:
            league = cfg["leagues"][0]
            ev = _basketball_game_to_event(games[0], league["name"])

    enriched = enrich_event(ev, ev.get("strLeague", ""), sport_key)
    return render_template(
        "match.html",
        event=enriched,
        sport_cfg=cfg,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )


@app.route("/api/live")
def api_live():
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
    events = []
    for league in cfg["leagues"][:2]:
        evts = get_next_events(sport_key, league, n=5)
        events.extend(evts[:5])
    return jsonify({"events": events[:15]})


@app.route("/pronostics")
def pronostics():
    all_events = []
    for sport_key, sport_cfg in SPORT_CONFIGS.items():
        for league in sport_cfg["leagues"][:3]:
            evts = get_next_events(sport_key, league, n=4)
            for ev in evts[:4]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    return render_template(
        "pronostics.html",
        events=all_events,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )


@app.route("/resultats")
def resultats():
    all_events = []
    for sport_key in ("football", "basketball"):
        cfg = SPORT_CONFIGS[sport_key]
        for league in cfg["leagues"][:2]:
            evts = get_past_events(sport_key, league, n=5)
            for ev in evts[:3]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    return render_template(
        "resultats.html",
        events=all_events,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )


@app.route("/api/status")
def api_status():
    """Vérifie le statut et le quota restant de l'API."""
    data = _cached_get(f"{FOOTBALL_API}/status", headers=HEADERS)
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)