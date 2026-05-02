"""
SportyTrader CI — Site de pronostics sportifs
Crédité par Kouakou Cedric
"""
from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sportytrader-cedric-2026")

THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"

# ─── Configuration des sports et championnats ────────────────────────────────
SPORT_CONFIGS = {
    "football": {
        "name": "Football",
        "icon": "⚽",
        "color": "#00e676",
        "leagues": [
            {"id": "4328", "name": "Premier League",        "country": "🏴 Angleterre",  "logo": "https://www.thesportsdb.com/images/media/league/badge/uwhs4s1549879062.png"},
            {"id": "4335", "name": "La Liga",               "country": "🇪🇸 Espagne",    "logo": "https://www.thesportsdb.com/images/media/league/badge/7onmyv1534768460.png"},
            {"id": "4331", "name": "Bundesliga",            "country": "🇩🇪 Allemagne",  "logo": "https://www.thesportsdb.com/images/media/league/badge/0j55yv1534764358.png"},
            {"id": "4332", "name": "Serie A",               "country": "🇮🇹 Italie",     "logo": "https://www.thesportsdb.com/images/media/league/badge/teywop1473257502.png"},
            {"id": "4334", "name": "Ligue 1",               "country": "🇫🇷 France",     "logo": "https://www.thesportsdb.com/images/media/league/badge/7onmyv1534768460.png"},
            {"id": "4480", "name": "Champions League",      "country": "🏆 Europe",      "logo": "https://www.thesportsdb.com/images/media/league/badge/cc5mjl1515942594.png"},
            {"id": "4399", "name": "MLS",                   "country": "🇺🇸 USA",        "logo": ""},
            {"id": "4346", "name": "AFCON",                 "country": "🌍 Afrique",     "logo": ""},
            {"id": "4347", "name": "Ligue des Champions CAF", "country": "🌍 Afrique",  "logo": ""},
        ],
    },
    "basketball": {
        "name": "Basketball",
        "icon": "🏀",
        "color": "#ff6d00",
        "leagues": [
            {"id": "4387", "name": "NBA",         "country": "🇺🇸 USA",    "logo": ""},
            {"id": "4391", "name": "Euroleague",  "country": "🇪🇺 Europe", "logo": ""},
            {"id": "4966", "name": "WNBA",        "country": "🇺🇸 USA",    "logo": ""},
        ],
    },
    "tennis": {
        "name": "Tennis",
        "icon": "🎾",
        "color": "#c6ff00",
        "leagues": [
            {"id": "4424", "name": "ATP Tour",   "country": "🌍 Mondial", "logo": ""},
            {"id": "4597", "name": "WTA Tour",   "country": "🌍 Mondial", "logo": ""},
        ],
    },
    "mma": {
        "name": "MMA / UFC",
        "icon": "🥊",
        "color": "#ff1744",
        "leagues": [
            {"id": "4443", "name": "UFC",         "country": "🌍 Mondial", "logo": ""},
            {"id": "4584", "name": "Bellator MMA","country": "🌍 Mondial", "logo": ""},
        ],
    },
}

# ─── Données de fallback (si API indisponible) ────────────────────────────────
FALLBACK_EVENTS = {
    "football": [
        {"idEvent":"f001","strHomeTeam":"Arsenal","strAwayTeam":"Chelsea","dateEvent":"2026-08-16","strTime":"16:00:00","strLeague":"Premier League","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f002","strHomeTeam":"PSG","strAwayTeam":"Olympique de Marseille","dateEvent":"2026-08-17","strTime":"20:45:00","strLeague":"Ligue 1","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f003","strHomeTeam":"Real Madrid","strAwayTeam":"FC Barcelone","dateEvent":"2026-08-22","strTime":"21:00:00","strLeague":"La Liga","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f004","strHomeTeam":"Bayern Munich","strAwayTeam":"Borussia Dortmund","dateEvent":"2026-08-23","strTime":"18:30:00","strLeague":"Bundesliga","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f005","strHomeTeam":"Juventus","strAwayTeam":"AC Milan","dateEvent":"2026-08-24","strTime":"20:45:00","strLeague":"Serie A","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f006","strHomeTeam":"Manchester City","strAwayTeam":"Liverpool","dateEvent":"2026-08-30","strTime":"17:30:00","strLeague":"Premier League","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f007","strHomeTeam":"Atletico Madrid","strAwayTeam":"Sevilla","dateEvent":"2026-08-29","strTime":"21:00:00","strLeague":"La Liga","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"f008","strHomeTeam":"Inter Milan","strAwayTeam":"AS Roma","dateEvent":"2026-08-31","strTime":"20:45:00","strLeague":"Serie A","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "basketball": [
        {"idEvent":"b001","strHomeTeam":"Los Angeles Lakers","strAwayTeam":"Boston Celtics","dateEvent":"2026-10-23","strTime":"01:30:00","strLeague":"NBA","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b002","strHomeTeam":"Golden State Warriors","strAwayTeam":"Miami Heat","dateEvent":"2026-10-24","strTime":"04:00:00","strLeague":"NBA","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"b003","strHomeTeam":"Real Madrid","strAwayTeam":"CSKA Moscou","dateEvent":"2026-10-10","strTime":"20:00:00","strLeague":"Euroleague","strSeason":"2026-2027","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "tennis": [
        {"idEvent":"t001","strHomeTeam":"Carlos Alcaraz","strAwayTeam":"Jannik Sinner","dateEvent":"2026-09-06","strTime":"17:00:00","strLeague":"US Open","strSeason":"2026","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t002","strHomeTeam":"Novak Djokovic","strAwayTeam":"Daniil Medvedev","dateEvent":"2026-09-07","strTime":"17:00:00","strLeague":"US Open","strSeason":"2026","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"t003","strHomeTeam":"Iga Swiatek","strAwayTeam":"Coco Gauff","dateEvent":"2026-09-06","strTime":"19:00:00","strLeague":"US Open WTA","strSeason":"2026","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
    "mma": [
        {"idEvent":"m001","strHomeTeam":"Jon Jones","strAwayTeam":"Tom Aspinall","dateEvent":"2026-09-19","strTime":"03:00:00","strLeague":"UFC 315","strSeason":"2026","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
        {"idEvent":"m002","strHomeTeam":"Israel Adesanya","strAwayTeam":"Alex Pereira","dateEvent":"2026-10-03","strTime":"03:00:00","strLeague":"UFC 316","strSeason":"2026","intHomeScore":None,"intAwayScore":None,"strHomeTeamBadge":"","strAwayTeamBadge":""},
    ],
}

PRONOSTICS_TYPES = ["1 (Victoire domicile)", "N (Nul)", "2 (Victoire extérieur)",
                    "Over 2.5 buts", "Under 2.5 buts", "BTTS (Les deux équipes marquent)",
                    "Double chance 1/N", "Double chance N/2", "Handicap -1"]
FIABILITE = ["★★★★★ Très haute", "★★★★☆ Haute", "★★★☆☆ Moyenne", "★★☆☆☆ Modérée"]
BOOKMAKERS = ["Bet365", "Winamax", "Betclic", "Unibet", "1xBet", "Melbet"]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_events_next_league(league_id: str) -> list:
    """Récupère les prochains matchs d'une ligue via TheSportsDB."""
    try:
        r = requests.get(f"{THESPORTSDB}/eventsnextleague.php", params={"id": league_id}, timeout=8)
        data = r.json()
        return data.get("events") or []
    except Exception as e:
        print(f"API error league {league_id}: {e}")
        return []

def get_events_next_league_with_fallback(league_id: str, sport: str) -> list:
    """Récupère les matchs réels, avec fallback sur données démo si API indisponible."""
    events = get_events_next_league(league_id)
    if events:
        return events
    # Retourner les données de fallback filtrées par sport
    return [ev for ev in FALLBACK_EVENTS.get(sport, [])
            if ev.get("strLeague","").lower() in ["premier league","la liga","bundesliga","serie a","ligue 1","nba","euroleague","ufc","us open","us open wta","uefa champions league"]][:4]

def get_events_last_league(league_id: str) -> list:
    try:
        r = requests.get(f"{THESPORTSDB}/eventspastleague.php", params={"id": league_id}, timeout=8)
        data = r.json()
        return data.get("events") or []
    except Exception as e:
        print(f"API error past {league_id}: {e}")
        return []

def enrich_event(ev: dict, league_name: str, sport: str) -> dict:
    """Ajoute des données de pronostic synthétique à un match."""
    cote_1 = round(random.uniform(1.30, 4.50), 2)
    cote_n = round(random.uniform(2.80, 4.20), 2)
    cote_2 = round(random.uniform(1.25, 5.00), 2)
    return {
        **ev,
        "league_name": league_name,
        "sport": sport,
        "cote_1": cote_1,
        "cote_n": cote_n,
        "cote_2": cote_2,
        "pronostic": random.choice(PRONOSTICS_TYPES),
        "fiabilite": random.choice(FIABILITE),
        "bookmaker": random.choice(BOOKMAKERS),
    }

def format_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        mois = ["","jan","fév","mar","avr","mai","juin","juil","aoû","sep","oct","nov","déc"]
        return f"{dt.day} {mois[dt.month]} {dt.year}"
    except:
        return date_str or "—"

app.jinja_env.filters["format_date"] = format_date

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    all_events = []
    # D'abord essayer l'API, sinon utiliser les fallback
    api_worked = False
    for sport_key, sport_cfg in SPORT_CONFIGS.items():
        for league in sport_cfg["leagues"][:2]:
            evts = get_events_next_league(league["id"])
            if evts:
                api_worked = True
                for ev in evts[:3]:
                    all_events.append(enrich_event(ev, league["name"], sport_key))

    # Si aucune donnée API, utiliser les fallback
    if not all_events:
        for sport_key, fallback_evts in FALLBACK_EVENTS.items():
            for ev in fallback_evts:
                all_events.append(enrich_event(ev, ev.get("strLeague",""), sport_key))

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
        evts = get_events_next_league(league["id"])
        if not evts:
            # Fallback : données de démo filtrées pour ce sport
            evts = FALLBACK_EVENTS.get(sport_key, [])
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
    try:
        r = requests.get(f"{THESPORTSDB}/lookupevent.php", params={"id": event_id}, timeout=8)
        ev = r.json().get("events", [{}])[0]
    except:
        ev = {}
    sport_key = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport_key, SPORT_CONFIGS["football"])
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
    """Endpoint API JSON pour les scores en direct (simulés avec prochains matchs)."""
    sport = request.args.get("sport", "football")
    cfg = SPORT_CONFIGS.get(sport, SPORT_CONFIGS["football"])
    events = []
    for league in cfg["leagues"][:3]:
        evts = get_events_next_league(league["id"])
        events.extend(evts[:5])
    return jsonify({"events": events[:15]})

@app.route("/pronostics")
def pronostics():
    all_events = []
    for sport_key, sport_cfg in SPORT_CONFIGS.items():
        for league in sport_cfg["leagues"]:
            evts = get_events_next_league(league["id"])
            for ev in evts[:4]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    # Fallback si aucune donnée API
    if not all_events:
        for sport_key, fallback_evts in FALLBACK_EVENTS.items():
            for ev in fallback_evts:
                all_events.append(enrich_event(ev, ev.get("strLeague",""), sport_key))
    return render_template(
        "pronostics.html",
        events=all_events,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )

@app.route("/resultats")
def resultats():
    all_events = []
    for sport_key, sport_cfg in SPORT_CONFIGS.items():
        for league in sport_cfg["leagues"][:2]:
            evts = get_events_last_league(league["id"])
            for ev in evts[:3]:
                all_events.append(enrich_event(ev, league["name"], sport_key))
    return render_template(
        "resultats.html",
        events=all_events,
        sport_configs=SPORT_CONFIGS,
        now=datetime.now(),
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
