"""
SportyPro Football – Calendrier · Classements · Buteurs
========================================================
FOOTBALLDATA_KEY = fc2aba02543e4baaa3fcdc91f7d39c7c
SECRET_KEY       = une-chaine-aleatoire-longue-ici

Saison 2025-26 | Toutes competitions free-tier football-data.org v4
Aucune donnee fictive.
"""

import os, json, hashlib, logging, threading, time
from math import exp, factorial
from datetime import datetime, timedelta, date
import requests
from flask import Flask, render_template_string, jsonify, request as freq

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════
FD_KEY    = os.environ.get("FOOTBALLDATA_KEY", "fc2aba02543e4baaa3fcdc91f7d39c7c")
SK        = os.environ.get("SECRET_KEY",       "une-chaine-aleatoire-longue-ici")
FD_BASE   = "https://api.football-data.org/v4"
FD_HEADS  = {"X-Auth-Token": FD_KEY}
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
log = logging.getLogger("sportyPro")

app = Flask(__name__)
app.secret_key = SK

# Saison courante (2025-26)
SEASON = 2025

def get_season(comp_code):
    """Retourne la saison correcte selon la competition."""
    season_map = {
        "WC":        2026,  # FIFA World Cup 2026
        "EUR":       2024,  # UEFA Euro 2024
        "UNL":       2024,  # UEFA Nations League 2024-25
        "NL":        2024,  # alias Nations League
        "CA":        2024,  # Copa America 2024
        "ACN":       2023,  # Africa Cup of Nations (jan 2024)
        "QCAF":      2025,  # Qualif. WC Afrique (CAF)
        "QAFC":      2023,  # Qualif. WC Asie (AFC)
        "QCONMEBOL": 2025,  # Qualif. WC Amerique du Sud
        "QCONCACAF": 2022,  # Qualif. WC CONCACAF
        "WCQ":       2024,  # Qualif. WC Europe (UEFA)
        "ECQR":      2024,  # Qualif. Euro
        "CLI":       2025,  # Copa Libertadores
        "CS":        2025,  # Copa Sudamericana

        "FAC":       2025,  # FA Cup
        "DFB":       2025,  # DFB-Pokal
    }
    return season_map.get(comp_code, SEASON)

# ═══════════════════════════════════════════════════════════════════
# COMPETITIONS — codes officiels football-data.org v4
# Matchs amicaux : NON disponibles sur football-data.org (aucun tier)
# Source codes : https://docs.football-data.org/general/v4/lookup_tables.html
# ═══════════════════════════════════════════════════════════════════
COMPS = {
    # ── COUPE DU MONDE ───────────────────────────────────────────────
    "WC":        {"name": "Coupe du Monde 2026",   "flag": "🌍",  "country": "Monde",        "color": "#c8a400", "category": "national"},

    # ── GRANDES COMPETITIONS CONTINENTALES ───────────────────────────
    "EUR":       {"name": "Euro 2024",             "flag": "🇪🇺",  "country": "Europe",       "color": "#003399", "category": "national"},
    "UNL":       {"name": "Nations League UEFA",   "flag": "🏳️",  "country": "Europe",       "color": "#0052cc", "category": "national"},
    "CA":        {"name": "Copa America 2024",     "flag": "🌎",  "country": "Amer. Sud",    "color": "#006600", "category": "national"},
    "ACN":       {"name": "CAN Afrique",           "flag": "🌍",  "country": "Afrique",      "color": "#ff6600", "category": "national"},

    # ── QUALIFICATIONS COUPE DU MONDE ────────────────────────────────
    "WCQ":       {"name": "Qualif. WC - Europe",   "flag": "🇪🇺",  "country": "UEFA",         "color": "#223377", "category": "national"},
    "QCAF":      {"name": "Qualif. WC - Afrique",  "flag": "🌍",  "country": "CAF",          "color": "#994400", "category": "national"},
    "QAFC":      {"name": "Qualif. WC - Asie",     "flag": "🌏",  "country": "AFC",          "color": "#cc2200", "category": "national"},
    "QCONMEBOL": {"name": "Qualif. WC - Am. Sud",  "flag": "🌎",  "country": "CONMEBOL",     "color": "#004400", "category": "national"},
    "QCONCACAF": {"name": "Qualif. WC - CONCACAF", "flag": "🌎",  "country": "CONCACAF",     "color": "#770000", "category": "national"},

    # ── COUPES CLUBS ─────────────────────────────────────────────────
    "CL":        {"name": "Champions League",      "flag": "🏆",  "country": "Europe",       "color": "#0f3f8c", "category": "club"},
    "CLI":       {"name": "Copa Libertadores",     "flag": "🌎",  "country": "Amer. Sud",    "color": "#ffcc00", "category": "cup"},
    "CS":        {"name": "Copa Sudamericana",     "flag": "🌎",  "country": "Amer. Sud",    "color": "#0077cc", "category": "cup"},
    "FAC":       {"name": "FA Cup",                "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",  "country": "Angleterre",  "color": "#660066", "category": "cup"},
    "DFB":       {"name": "DFB-Pokal",             "flag": "🇩🇪",  "country": "Allemagne",    "color": "#990000", "category": "cup"},

    # ── LIGUES CLUBS – TOP 5 EUROPE ──────────────────────────────────
    "PL":        {"name": "Premier League",        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",  "country": "Angleterre",  "color": "#37003c", "category": "club"},
    "PD":        {"name": "La Liga",               "flag": "🇪🇸",  "country": "Espagne",      "color": "#ee8707", "category": "club"},
    "SA":        {"name": "Serie A",               "flag": "🇮🇹",  "country": "Italie",       "color": "#024494", "category": "club"},
    "BL1":       {"name": "Bundesliga",            "flag": "🇩🇪",  "country": "Allemagne",    "color": "#d3010c", "category": "club"},
    "FL1":       {"name": "Ligue 1",               "flag": "🇫🇷",  "country": "France",       "color": "#091c3e", "category": "club"},

    # ── AUTRES LIGUES CLUBS ───────────────────────────────────────────
    "ELC":       {"name": "Championship",          "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",  "country": "Angleterre",  "color": "#3d1a78", "category": "club"},
    "PPL":       {"name": "Primeira Liga",         "flag": "🇵🇹",  "country": "Portugal",     "color": "#006600", "category": "club"},
    "DED":       {"name": "Eredivisie",            "flag": "🇳🇱",  "country": "Pays-Bas",     "color": "#ff6600", "category": "club"},
    "BSA":       {"name": "Serie A Bresil",        "flag": "🇧🇷",  "country": "Bresil",       "color": "#009c3b", "category": "club"},

}

# Competitions avec classement disponible
STANDINGS_COMPS = [
    "WC","EUR","UNL","CA","ACN",
    "WCQ","QCAF","QAFC","QCONMEBOL","QCONCACAF",
    "CL","PL","PD","SA","BL1","FL1","ELC","PPL","DED","BSA",
]

# Filtres UI par categorie
NATIONAL_COMPS = ["WC","EUR","UNL","CA","ACN","WCQ","QCAF","QAFC","QCONMEBOL","QCONCACAF"]
CUP_COMPS      = ["CL","CLI","CS","FAC","DFB"]

# ═══════════════════════════════════════════════════════════════════
# CACHE
# ═══════════════════════════════════════════════════════════════════
_rate_lock = threading.Lock()
_last_req  = [0.0]

def _throttle():
    """Max 10 req/min pour le free tier → 6s entre requetes."""
    with _rate_lock:
        elapsed = time.time() - _last_req[0]
        if elapsed < 6.1:
            time.sleep(6.1 - elapsed)
        _last_req[0] = time.time()

def cpath(key):
    return os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")

def cget(key, ttl_h=2.0):
    p = cpath(key)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        if datetime.now() - datetime.fromisoformat(d["_ts"]) > timedelta(hours=ttl_h):
            return None
        return d["v"]
    except Exception:
        return None

def cset(key, val):
    try:
        with open(cpath(key), "w", encoding='utf-8') as f:
            json.dump({"_ts": datetime.now().isoformat(), "v": val}, f, ensure_ascii=False)
    except Exception as e:
        log.warning(f"Cache write: {e}")

# ═══════════════════════════════════════════════════════════════════
# HTTP
# ═══════════════════════════════════════════════════════════════════
def fd_get(path, params=None, ttl_h=2.0, throttle=True):
    """GET football-data.org avec cache + throttle."""
    ck = f"fd_{path}_{json.dumps(params or {}, sort_keys=True)}"
    cached = cget(ck, ttl_h)
    if cached is not None:
        return cached, None

    if throttle:
        _throttle()

    try:
        r = requests.get(f"{FD_BASE}{path}", headers=FD_HEADS, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            cset(ck, data)
            return data, None
        if r.status_code == 429:
            return None, "Limite de requetes API atteinte – reessayez dans 1 minute."
        return None, f"Erreur API {r.status_code} : {r.text[:120]}"
    except requests.Timeout:
        return None, "Timeout – l'API football-data.org ne repond pas."
    except Exception as e:
        return None, f"Erreur reseau : {e}"

# ═══════════════════════════════════════════════════════════════════
# HELPERS DATE / SEMAINE
# ═══════════════════════════════════════════════════════════════════
def week_bounds(iso_week: str):
    """'2026-W18' → (date_lundi, date_dimanche)"""
    year, w = iso_week.split("-W")
    monday = datetime.strptime(f"{year}-W{int(w):02d}-1", "%G-W%V-%u").date()
    return monday, monday + timedelta(days=6)

def date_to_week(d: date) -> str:
    return d.strftime("%G-W%V")

def season_weeks():
    """Liste des semaines ISO de la saison 2025-26 + Coupe du Monde 2026 (aout 2025 – juil 2026)."""
    start = date(2025, 8, 4)   # premiere semaine de matchs
    end   = date(2026, 7, 20)  # finale Coupe du Monde 2026 (19 juillet 2026)
    weeks = []
    cur   = start - timedelta(days=start.weekday())  # lundi
    while cur <= end:
        weeks.append(date_to_week(cur))
        cur += timedelta(weeks=1)
    return weeks

# ═══════════════════════════════════════════════════════════════════
# FETCH MATCHES
# ═══════════════════════════════════════════════════════════════════
def fetch_matches_week(iso_week: str, comp_filter: str = "ALL"):
    """Matchs d'une semaine. Retourne (list, error)."""
    monday, sunday = week_bounds(iso_week)

    if comp_filter == "ALL":
        comps = list(COMPS.keys())
    elif "," in comp_filter:
        # Filtre multi-compétitions (ex: filtrage par catégorie)
        comps = [c.strip() for c in comp_filter.split(",") if c.strip() in COMPS]
    else:
        comps = [comp_filter] if comp_filter in COMPS else list(COMPS.keys())

    all_matches, errors = [], []

    # football-data v4 : dateTo +1j car la borne haute est exclusive en pratique
    data, err = fd_get("/matches", {
        "competitions": ",".join(comps),
        "dateFrom": monday.strftime("%Y-%m-%d"),
        "dateTo":   (sunday + timedelta(days=1)).strftime("%Y-%m-%d"),
    }, ttl_h=1.0)

    if err:
        return [], err
    if not data or "matches" not in data:
        return [], "Reponse inattendue de l'API."

    for m in data.get("matches", []):
        if not isinstance(m, dict):
            continue
        ht   = m.get("homeTeam") or {}
        at   = m.get("awayTeam") or {}
        comp = m.get("competition") or {}
        sc   = (m.get("score") or {}).get("fullTime") or {}
        hts  = (m.get("score") or {}).get("halfTime") or {}

        utc_str  = m.get("utcDate", "")
        local_dt = None
        try:
            local_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass

        code = comp.get("code", "")
        info = COMPS.get(code, {"name": comp.get("name", code), "flag": "⚽", "color": "#444"})

        all_matches.append({
            "id":          m.get("id"),
            "comp_code":   code,
            "comp_name":   info["name"],
            "comp_flag":   info["flag"],
            "comp_color":  info.get("color", "#444"),
            "home":        ht.get("shortName") or ht.get("name") or "?",
            "away":        at.get("shortName") or at.get("name") or "?",
            "home_id":     ht.get("id"),
            "away_id":     at.get("id"),
            "home_crest":  ht.get("crest", ""),
            "away_crest":  at.get("crest", ""),
            "datetime":    local_dt.isoformat() if local_dt else None,
            "date":        local_dt.date().isoformat() if local_dt else None,
            "status":      m.get("status", "SCHEDULED"),
            "score_home":  sc.get("home"),
            "score_away":  sc.get("away"),
            "ht_home":     hts.get("home"),
            "ht_away":     hts.get("away"),
            "minute":      m.get("minute"),
            "stage":       m.get("stage", ""),
            "matchday":    m.get("matchday"),
        })

    all_matches.sort(key=lambda x: x.get("datetime") or "")
    return all_matches, None


# ═══════════════════════════════════════════════════════════════════
# MODÈLE POISSON — RATINGS ATTAQUE/DÉFENSE PAR COMPÉTITION
# ═══════════════════════════════════════════════════════════════════
HOME_ADV = 1.22          # +22% de buts à domicile (moyenne Europe)
DECAY    = 0.78          # décroissance exponentielle forme (plus récent = plus lourd)

# Cache ratings par compétition
_ratings_cache = {}
_ratings_lock  = threading.Lock()

def get_comp_ratings(comp_code):
    """
    Calcule l'indice d'attaque et de défense de chaque équipe dans une compétition.
    Basé sur le modèle Dixon-Coles : att = (buts_marqués/match) / moyenne_ligue
    Retourne ({team_id: {attack, defense, position, pts_pg}}, avg_goals_per_match)
    """
    with _ratings_lock:
        if comp_code in _ratings_cache:
            return _ratings_cache[comp_code]

    data, err = fd_get(f"/competitions/{comp_code}/standings",
                       {"season": get_season(comp_code)}, ttl_h=6.0)
    if err or not data:
        return None, None

    standings = data.get("standings", [])
    total = next((s for s in standings if s.get("type") == "TOTAL"),
                 standings[0] if standings else None)
    if not total:
        return None, None

    table = total.get("table", [])
    if not table:
        return None, None

    played_list = [r.get("playedGames", 0) for r in table]
    gf_list     = [r.get("goalsFor", 0)    for r in table]
    total_played = sum(played_list)
    total_gf     = sum(gf_list)

    if total_played == 0:
        return None, None

    # Buts marqués par équipe par match (moyenne ligue)
    avg_g = total_gf / total_played

    ratings, n = {}, len(table)
    for r in table:
        team  = r.get("team") or {}
        tid   = team.get("id")
        if not tid:
            continue
        played = max(r.get("playedGames", 1), 1)
        gf     = r.get("goalsFor",     0)
        ga     = r.get("goalsAgainst", 0)
        pts    = r.get("points",       0)
        pos    = r.get("position",     n // 2)

        att = (gf / played) / avg_g if avg_g > 0 else 1.0
        dfe = (ga / played) / avg_g if avg_g > 0 else 1.0

        ratings[tid] = {
            "attack":   max(0.15, min(att, 4.0)),
            "defense":  max(0.15, min(dfe, 4.0)),
            "position": pos,
            "n_teams":  n,
            "pts_pg":   round(pts / played, 2),
        }

    result = (ratings, avg_g)
    with _ratings_lock:
        _ratings_cache[comp_code] = result
    return result

# ═══════════════════════════════════════════════════════════════════
# FETCH FORM — VERSION DÉTAILLÉE (buts + contexte dom/ext)
# ═══════════════════════════════════════════════════════════════════
def fetch_form(team_id):
    """Derniers 10 matchs : résultat, buts, domicile/extérieur."""
    if not team_id:
        return []
    ck = f"form2_{team_id}_{date.today()}"
    cached = cget(ck, 8.0)
    if cached is not None:
        return cached

    # throttle=False : la form est en cache 8h, les appels réels sont rares
    data, _ = fd_get(f"/teams/{team_id}/matches",
                     {"status": "FINISHED", "limit": 10}, ttl_h=8.0, throttle=False)
    form = []
    if data and isinstance(data.get("matches"), list):
        for m in data["matches"]:
            if not isinstance(m, dict):
                continue
            ft = (m.get("score") or {}).get("fullTime") or {}
            h, a = ft.get("home"), ft.get("away")
            if h is None or a is None:
                continue
            is_home = (m.get("homeTeam") or {}).get("id") == team_id
            gf = int(h if is_home else a)
            ga = int(a if is_home else h)
            res = "D" if h == a else (
                "W" if (is_home and h > a) or (not is_home and a > h) else "L"
            )
            form.append({"result": res, "gf": gf, "ga": ga, "home": is_home})

    form = form[-10:]
    cset(ck, form)
    return form

# ═══════════════════════════════════════════════════════════════════
# MODÈLE POISSON
# ═══════════════════════════════════════════════════════════════════

# Compétitions de sélections nationales → pronostic désactivé
# (la forme des clubs ne reflète pas les performances nationales)
NATIONAL_COMP_CODES = {"WC", "EUR", "UNL", "NL", "CA", "ACN", "WCQ", "QCAF", "QAFC", "QCONMEBOL", "QCONCACAF"}

def _pois(lam, k):
    if k < 0 or lam <= 0:
        return 0.0
    return (lam ** k) * exp(-lam) / factorial(k)

def _match_probs(lam_h, lam_a, max_g=9):
    """P(1), P(X), P(2) par double-Poisson."""
    p1 = px = p2 = 0.0
    for i in range(max_g + 1):
        pi = _pois(lam_h, i)
        for j in range(max_g + 1):
            p = pi * _pois(lam_a, j)
            if   i > j: p1 += p
            elif i == j: px += p
            else:        p2 += p
    return p1, px, p2

def _form_factor(form_list, is_home_ctx):
    """
    Score de forme pondéré exponentiellement.
    Utilise préférentiellement les matchs dom/ext selon contexte.
    Retourne un facteur multiplicatif [0.68, 1.32].
    """
    relevant = [m for m in form_list if m["home"] == is_home_ctx]
    if len(relevant) < 3:
        relevant = form_list  # fallback si trop peu de matchs contextuels
    if not relevant:
        return 1.0
    pts = {"W": 1.0, "D": 0.35, "L": 0.0}
    n = len(relevant)
    weights = [DECAY ** (n - 1 - i) for i in range(n)]
    score   = sum(w * pts[m["result"]] for w, m in zip(weights, relevant))
    max_sc  = sum(weights)
    norm    = score / max_sc  # [0, 1]
    return 0.68 + norm * 0.64  # [0.68, 1.32]

def _goals_factor(form_list, is_home_ctx):
    """
    Facteur buts marqués/concédés (efficacité offensive et défensive récente).
    Retourne (facteur_attaque, facteur_defense) normalisés sur 1.3 buts/match.
    """
    relevant = [m for m in form_list if m["home"] == is_home_ctx]
    if len(relevant) < 3:
        relevant = form_list
    if not relevant:
        return 1.0, 1.0
    n = len(relevant)
    weights = [DECAY ** (n - 1 - i) for i in range(n)]
    w_sum   = sum(weights)
    avg_gf  = sum(w * m["gf"] for w, m in zip(weights, relevant)) / w_sum
    avg_ga  = sum(w * m["ga"] for w, m in zip(weights, relevant)) / w_sum
    # Normaliser sur une moyenne attendue de 1.3 buts
    att_f = max(0.4, min(avg_gf / 1.3, 2.5))
    def_f = max(0.4, min(avg_ga / 1.3, 2.5))  # plus ga est bas, meilleure la défense
    return att_f, def_f

# ── FIX 3 : Confrontations directes (H2H) ───────────────────────────
def fetch_h2h(home_id, away_id):
    """
    Récupère les 6 dernières confrontations directes entre les deux équipes.
    Retourne un facteur h2h_home entre [0.80, 1.20] basé sur l'historique.
    """
    if not home_id or not away_id:
        return 1.0
    ck = f"h2h_{min(home_id,away_id)}_{max(home_id,away_id)}_{date.today()}"
    cached = cget(ck, 24.0)
    if cached is not None:
        return cached

    data, _ = fd_get(f"/teams/{home_id}/matches",
                     {"status": "FINISHED", "limit": 20}, ttl_h=12.0, throttle=False)
    if not data or not isinstance(data.get("matches"), list):
        cset(ck, 1.0)
        return 1.0

    h2h = []
    for m in data["matches"]:
        if not isinstance(m, dict):
            continue
        ht_id = (m.get("homeTeam") or {}).get("id")
        at_id = (m.get("awayTeam") or {}).get("id")
        if not ({ht_id, at_id} == {home_id, away_id}):
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None:
            continue
        # résultat du point de vue de home_id
        is_home = (ht_id == home_id)
        gf = int(gh if is_home else ga)
        gc = int(ga if is_home else gh)
        res = "D" if gh == ga else (
            "W" if (is_home and gh > ga) or (not is_home and ga > gh) else "L"
        )
        h2h.append({"result": res, "gf": gf, "gc": gc})
        if len(h2h) >= 6:
            break

    if not h2h:
        cset(ck, 1.0)
        return 1.0

    pts = {"W": 1.0, "D": 0.4, "L": 0.0}
    n = len(h2h)
    weights = [DECAY ** (n - 1 - i) for i in range(n)]
    score   = sum(w * pts[m["result"]] for w, m in zip(weights, h2h))
    max_sc  = sum(weights)
    norm    = score / max_sc  # [0, 1]
    factor  = round(0.80 + norm * 0.40, 4)  # [0.80, 1.20]
    cset(ck, factor)
    return factor

def prono(home_id, away_id, comp_code=""):
    """
    Moteur de pronostic Double-Poisson (Dixon-Coles simplifié).
    
    Pipeline de calcul :
      1. Forme récente pondérée exp. (10 derniers matchs, DECAY=0.78)
         → facteur forme [0.68–1.32] séparé dom/ext
         → facteur buts marqués/concédés récents
      2. Ratings de classement (attack/defense) normalisés sur la ligue
      3. Confrontations directes H2H (6 derniers duels)
      4. Lambda (buts attendus) = att × def_adverse × avg_ligue × avantage_dom × forme × H2H
      5. Double-Poisson → distribution de scores → P(1), P(X), P(2)
      6. Confidence = max(P) plafonné à 76% (honnêteté statistique)
    
    Retourne toujours un résultat pour les clubs, même sans historique
    (fallback classement seul, puis fallback neutre 35/30/35).
    Retourne None uniquement pour les sélections nationales.
    """
    # Sélections nationales : modèle non applicable
    if comp_code in NATIONAL_COMP_CODES:
        return None

    home_form = fetch_form(home_id) if home_id else []
    away_form = fetch_form(away_id) if away_id else []

    # Ratings de classement (source principale)
    ratings, avg_g = get_comp_ratings(comp_code) if comp_code else (None, None)

    # ── Facteurs de forme (1.0 si pas d'historique)
    hff = _form_factor(home_form, True)  if home_form else 1.0
    aff = _form_factor(away_form, False) if away_form else 1.0
    hgf, hga = _goals_factor(home_form, True)  if home_form else (1.0, 1.0)
    agf, aga = _goals_factor(away_form, False) if away_form else (1.0, 1.0)

    # ── Confrontations directes H2H
    h2h_factor = fetch_h2h(home_id, away_id)
    h2h_inv    = round(1.0 / h2h_factor, 4) if h2h_factor > 0 else 1.0

    # ── Déterminer le modèle utilisé et les sources de données
    has_form     = bool(home_form or away_form)
    has_ratings  = bool(ratings and avg_g and avg_g > 0)
    has_h2h      = (h2h_factor != 1.0)

    if has_ratings:
        hr = ratings.get(home_id) or {"attack": 1.0, "defense": 1.0}
        ar = ratings.get(away_id) or {"attack": 1.0, "defense": 1.0}

        # Défense récente inversée : hga élevé = encaisse beaucoup = pénalise l'équipe
        home_def_rec = max(0.5, 2.0 - hga)
        away_def_rec = max(0.5, 2.0 - aga)

        # Lambda principal (modèle Dixon-Coles)
        lam_h = hr["attack"] * ar["defense"] * avg_g * HOME_ADV * hff * away_def_rec * h2h_factor
        lam_a = ar["attack"] * hr["defense"] * avg_g * aff       * home_def_rec      * h2h_inv

        # Lissage 10% avec buts récents offensifs pour ne pas double-compter la forme
        if has_form:
            lam_h = lam_h * 0.90 + hgf * avg_g * HOME_ADV * 0.10
            lam_a = lam_a * 0.90 + agf * avg_g             * 0.10

        sources = ["classement", "forme" if has_form else None, "H2H" if has_h2h else None]
        model   = "poisson+" + "+".join(s for s in sources[1:] if s) if any(sources[1:]) else "poisson"

    elif has_form:
        # Pas de classement mais forme disponible (coupe, début de saison)
        home_def_rec = max(0.5, 2.0 - hga)
        away_def_rec = max(0.5, 2.0 - aga)
        lam_h = max(0.4, hgf * 1.3 * HOME_ADV * hff * away_def_rec * h2h_factor)
        lam_a = max(0.4, agf * 1.3 *            aff * home_def_rec * h2h_inv)
        model = "forme+" + ("H2H" if has_h2h else "seule")

    else:
        # Aucune donnée : probabilités neutres légèrement biaisées domicile
        # Ce cas couvre le 6e match sans historique
        lam_h = 1.35 * HOME_ADV   # ~1.65 buts attendus domicile
        lam_a = 1.35              # ~1.35 buts attendus extérieur
        model = "neutre"

    lam_h = round(max(0.20, min(lam_h, 5.5)), 3)
    lam_a = round(max(0.20, min(lam_a, 5.5)), 3)

    p1, px, p2 = _match_probs(lam_h, lam_a)
    tot = (p1 + px + p2) or 1.0
    p1, px, p2 = p1/tot, px/tot, p2/tot

    best  = max(p1, px, p2)
    label = "1" if best == p1 else ("2" if best == p2 else "X")

    # Confidence selon la qualité des données
    raw_conf = round(best * 100)
    if   model == "neutre":           conf = min(raw_conf, 52)
    elif "forme" in model and "classement" not in model: conf = min(raw_conf, 60)
    else:                             conf = min(raw_conf, 76)

    # Cotes indicatives (marge 5.5%) — pas de value bet circulaire
    mg    = 1.055
    odd_h = round(min((1/p1)*mg, 25.0), 2) if p1 > 0.01 else None
    odd_x = round(min((1/px)*mg, 15.0), 2) if px > 0.01 else None
    odd_a = round(min((1/p2)*mg, 25.0), 2) if p2 > 0.01 else None

    # Détail pour explication dans l'UI
    detail = {
        "home_att":      round(ratings[home_id]["attack"],  2) if has_ratings and home_id in ratings else None,
        "home_def":      round(ratings[home_id]["defense"], 2) if has_ratings and home_id in ratings else None,
        "away_att":      round(ratings[away_id]["attack"],  2) if has_ratings and away_id in ratings else None,
        "away_def":      round(ratings[away_id]["defense"], 2) if has_ratings and away_id in ratings else None,
        "home_form_ff":  round(hff, 2),
        "away_form_ff":  round(aff, 2),
        "home_form_n":   len(home_form),
        "away_form_n":   len(away_form),
        "avg_g":         round(avg_g, 2) if avg_g else None,
        "home_adv":      HOME_ADV,
        "h2h_n":         None,  # rempli si H2H calculé
    }

    return {
        "label":    label,
        "conf":     conf,
        "p_home":   round(p1 * 100),
        "p_draw":   round(px * 100),
        "p_away":   round(p2 * 100),
        "odd_home": odd_h,
        "odd_draw": odd_x,
        "odd_away": odd_a,
        "xg_home":  round(lam_h, 2),
        "xg_away":  round(lam_a, 2),
        "h2h":      round(h2h_factor, 2),
        "model":    model,
        "detail":   detail,
    }

def enrich_match(m):
    hf  = fetch_form(m.get("home_id"))
    af  = fetch_form(m.get("away_id"))
    m["home_form"] = [x["result"] for x in hf]
    m["away_form"] = [x["result"] for x in af]
    m["prono"]     = prono(m.get("home_id"), m.get("away_id"), m.get("comp_code", ""))
    return m


# ═══════════════════════════════════════════════════════════════════
# FETCH STANDINGS
# ═══════════════════════════════════════════════════════════════════
def _parse_table_rows(rows, group_name=""):
    """Transforme une liste de rows API en liste de dicts normalisés."""
    out = []
    for row in rows:
        team = row.get("team") or {}
        frm  = row.get("form") or ""
        out.append({
            "position": row.get("position", 0),
            "team_id":  team.get("id"),
            "name":     team.get("shortName") or team.get("name") or "?",
            "crest":    team.get("crest", ""),
            "played":   row.get("playedGames", 0),
            "won":      row.get("won", 0),
            "draw":     row.get("draw", 0),
            "lost":     row.get("lost", 0),
            "gf":       row.get("goalsFor", 0),
            "ga":       row.get("goalsAgainst", 0),
            "gd":       row.get("goalDifference", 0),
            "pts":      row.get("points", 0),
            "form":     list(frm) if frm else [],
            "group":    group_name,
        })
    return out

def fetch_standings(comp_code):
    data, err = fd_get(f"/competitions/{comp_code}/standings",
                       {"season": get_season(comp_code)}, ttl_h=4.0)
    if err or not data:
        return None, err or "Classement indisponible."

    standings = data.get("standings", [])
    if not standings:
        return None, "Classement indisponible."

    # ── Détecter le format de l'API ──────────────────────────────────
    # Format 1 : une seule entrée type=TOTAL (PL, SA, BL1…)
    # Format 2 : plusieurs entrées type=TOTAL, une par groupe (WC, EC, NL…)
    # Format 3 : entrées avec group=GROUP_A/B/C (coupes, WC passé)
    # On détecte par le champ "group" non-nul

    has_groups = any(
        s.get("group") or (s.get("stage","") not in ("","REGULAR_SEASON","GROUP_STAGE"))
        for s in standings
    )

    if has_groups or len([s for s in standings if s.get("type")=="TOTAL"]) > 1:
        # Format avec groupes → on préserve le groupe de chaque équipe
        # Chaque stage = un groupe
        table = []
        seen  = set()
        for stage in standings:
            # Déterminer le label du groupe
            grp = stage.get("group") or stage.get("stage") or "?"
            # Nettoyer : "GROUP_A" → "Groupe A"
            grp_label = grp.replace("GROUP_","Groupe ").replace("_"," ").title()
            for row in _parse_table_rows(stage.get("table", []), grp_label):
                if row["team_id"] not in seen:
                    seen.add(row["team_id"])
                    table.append(row)
        return table, None

    # Format standard : une seule table TOTAL (ligues domestiques)
    total = next((s for s in standings if s.get("type") == "TOTAL"), standings[0])
    return _parse_table_rows(total.get("table", [])), None

# ═══════════════════════════════════════════════════════════════════
# FETCH TOP SCORERS
# ═══════════════════════════════════════════════════════════════════
def fetch_scorers(comp_code, limit=20):
    data, err = fd_get(f"/competitions/{comp_code}/scorers",
                       {"season": get_season(comp_code), "limit": limit}, ttl_h=4.0)
    if err or not data:
        return None, err or "Buteurs indisponibles."

    scorers = []
    for s in data.get("scorers", []):
        pl   = s.get("player") or {}
        team = s.get("team") or {}
        scorers.append({
            "name":      pl.get("name") or pl.get("firstName","") + " " + pl.get("lastName",""),
            "nat":       pl.get("nationality", ""),
            "team":      team.get("shortName") or team.get("name") or "?",
            "crest":     team.get("crest", ""),
            "goals":     s.get("goals", 0),
            "assists":   s.get("assists", 0) or 0,
            "penalties": s.get("penalties", 0) or 0,
            "matches":   s.get("playedMatches", 0) or 0,
        })
    return scorers, None

# ═══════════════════════════════════════════════════════════════════
# ROUTES API
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/comps")
def api_comps():
    return jsonify([{"code": k, **v} for k,v in COMPS.items()])

@app.route("/api/national_comps")
def api_national_comps():
    """Retourne uniquement les compétitions de sélections nationales."""
    return jsonify([{"code": k, **v} for k,v in COMPS.items() if v.get("category") == "national"])

@app.route("/api/status")
def api_status():
    data, err = fd_get("/competitions/PL", throttle=False)
    return jsonify({"ok": data is not None, "error": err})

@app.route("/api/weeks")
def api_weeks():
    """Liste des semaines de la saison avec nb de matchs (depuis cache si dispo)."""
    weeks = season_weeks()
    cur   = date_to_week(date.today())
    result = []
    for w in weeks:
        monday, sunday = week_bounds(w)
        result.append({
            "week":    w,
            "label":   f"{monday.strftime('%d %b')} – {sunday.strftime('%d %b')}",
            "current": w == cur,
            "past":    sunday < date.today(),
        })
    return jsonify(result)

@app.route("/api/matches")
def api_matches():
    iso_week = freq.args.get("week", date_to_week(date.today()))
    comp     = freq.args.get("comp", "ALL")
    cat      = freq.args.get("cat", "ALL")   # 'ALL' | 'national' | 'club'
    no_prono = freq.args.get("prono", "1") == "0"

    # Si un filtre par catégorie est actif (et pas de comp spécifique), filtrer les comp
    if comp == "ALL" and cat != "ALL":
        comp_filter = ",".join(k for k, v in COMPS.items() if v.get("category") == cat)
        if not comp_filter:
            return jsonify({"matches": [], "error": None})
        matches, err = fetch_matches_week(iso_week, comp_filter)
    else:
        matches, err = fetch_matches_week(iso_week, comp)
    if err:
        return jsonify({"matches": [], "error": err})

    if not no_prono and matches:
        today_str = date.today().isoformat()

        # Pronostics uniquement pour les matchs DU JOUR (pas toute la semaine)
        # Priorité : LIVE > SCHEDULED/TIMED > FINISHED du jour
        priority_order = {"IN_PLAY": 0, "LIVE": 1, "SCHEDULED": 2, "TIMED": 3, "FINISHED": 4}
        today_matches = [m for m in matches if m.get("date") == today_str]

        # Si aucun match aujourd'hui, on prend le prochain jour avec des matchs
        if not today_matches:
            future = sorted([m for m in matches if (m.get("date") or "") >= today_str],
                            key=lambda m: m.get("datetime") or "")
            if future:
                next_day = future[0]["date"]
                today_matches = [m for m in future if m.get("date") == next_day]

        to_enrich = sorted(today_matches,
                           key=lambda m: priority_order.get(m.get("status",""), 9))
        # Exclure les sélections nationales du calcul (prono=None de toute façon)
        # mais on les inclut quand même pour ne pas bloquer le chargement
        # Limite de sécurité : max 20 matchs par cycle (free tier API)
        to_enrich = to_enrich[:20]

        # ── Pré-chargement séquentiel des données (throttlé, mis en cache) ──
        team_ids = set()
        for m in to_enrich:
            if m.get("home_id"): team_ids.add(m["home_id"])
            if m.get("away_id"): team_ids.add(m["away_id"])
        comp_codes = {m.get("comp_code","") for m in to_enrich if m.get("comp_code")}

        for tid in team_ids:
            try: fetch_form(tid)
            except Exception: pass
        for code in comp_codes:
            try: get_comp_ratings(code)
            except Exception: pass

        # ── Threads d'enrichissement (cache chaud → rapides) ──
        enriched_map, lock = {}, threading.Lock()
        def worker(m):
            try:
                r = enrich_match(m)
            except Exception as e:
                log.error(f"Enrich {m.get('id')}: {e}")
                m["prono"] = None
                r = m
            with lock:
                enriched_map[r["id"]] = r

        threads = [threading.Thread(target=worker, args=(m,), daemon=True) for m in to_enrich]
        for t in threads: t.start()
        for t in threads: t.join(timeout=20)

        # Fusionner : matchs enrichis + matchs non-enrichis (sans prono)
        result = []
        for m in matches:
            result.append(enriched_map.get(m["id"], m))
        result.sort(key=lambda m: m.get("datetime") or "")
        return jsonify({"matches": result, "error": None})

    return jsonify({"matches": matches, "error": None})

@app.route("/api/wc_groups")
def api_wc_groups():
    """Route dédiée aux groupes WC — retourne la table avec champ 'group' préservé."""
    table, err = fetch_standings("WC")
    if err or not table:
        return jsonify({"groups": {}, "error": err or "Groupes indisponibles."})
    # Construire un dict groupe → [équipes triées par pts/gd/gf]
    groups = {}
    for row in table:
        g = row.get("group") or "Groupe ?"
        groups.setdefault(g, []).append(row)
    for g in groups:
        groups[g].sort(key=lambda r: (-r["pts"], -r["gd"], -r["gf"]))
    return jsonify({"groups": groups, "error": None})

@app.route("/api/standings")
def api_standings():
    comp = freq.args.get("comp", "PL")
    if comp not in STANDINGS_COMPS:
        return jsonify({"table": None, "error": f"Classement non disponible pour {comp}."})
    table, err = fetch_standings(comp)
    return jsonify({"table": table, "error": err})

@app.route("/api/scorers")
def api_scorers():
    comp = freq.args.get("comp", "PL")
    scorers, err = fetch_scorers(comp, 25)
    return jsonify({"scorers": scorers, "error": err})

@app.route("/")
def index():
    return render_template_string(HTML)

# ═══════════════════════════════════════════════════════════════════
# HTML – SPA
# ═══════════════════════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>SportyPro Football 2025-26</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --bg:#070b12;--bg2:#0c1220;--bg3:#101828;--card:#111d30;--card2:#162035;
  --b1:#1e2d45;--b2:#253550;--b3:#2d4060;
  --fg:#d8e8ff;--fg2:#a8c0e0;--muted:#5a7090;--dim:#374d68;
  --green:#00e87a;--blue:#3d9bff;--orange:#ff7a2f;--yellow:#ffd43b;
  --red:#ff4d4d;--purple:#9d60ff;
  --fh:'Oswald',sans-serif;--fb:'Inter',sans-serif;
  --r:8px;--r2:12px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--fg);font-family:var(--fb);min-height:100vh;
  background-image:
    radial-gradient(ellipse 60% 30% at 50% -5%,#0d2545 0%,transparent 70%),
    radial-gradient(ellipse 40% 20% at 90% 10%,#0a1f3a 0%,transparent 60%);}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--b2);border-radius:4px;}

/* ── HEADER ── */
header{background:rgba(7,11,18,.95);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--b1);position:sticky;top:0;z-index:300;}
.hdr{max-width:1480px;margin:auto;display:flex;align-items:center;
  height:56px;padding:0 20px;gap:16px;}
.logo{font-family:var(--fh);font-size:1.7rem;font-weight:700;letter-spacing:3px;
  background:linear-gradient(90deg,var(--blue),var(--green));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  flex-shrink:0;}
.season-tag{font-size:.68rem;letter-spacing:1px;color:var(--muted);
  border:1px solid var(--b2);padding:2px 8px;border-radius:4px;flex-shrink:0;}
.hdr-sep{flex:1;}
.api-indicator{display:flex;align-items:center;gap:5px;font-size:.68rem;color:var(--muted);}
.dot{width:7px;height:7px;border-radius:50%;background:var(--dim);flex-shrink:0;}
.dot.ok{background:var(--green);}
.dot.err{background:var(--red);}
.refresh-btn{font-family:var(--fb);font-size:.72rem;padding:5px 12px;
  border:1px solid var(--b2);border-radius:6px;background:transparent;
  color:var(--muted);cursor:pointer;transition:all .2s;flex-shrink:0;}
.refresh-btn:hover{color:var(--blue);border-color:var(--blue);}

/* ── NAV ── */
nav{background:var(--bg2);border-bottom:1px solid var(--b1);}
.nav-inner{max-width:1480px;margin:auto;display:flex;align-items:center;
  padding:0 20px;gap:2px;height:44px;}
.nav-btn{font-family:var(--fh);font-size:.9rem;font-weight:500;letter-spacing:1px;
  padding:6px 20px;border-radius:6px;border:none;background:transparent;
  color:var(--muted);cursor:pointer;transition:all .2s;text-transform:uppercase;}
.nav-btn:hover{color:var(--fg);}
.nav-btn.active{background:var(--card);color:var(--blue);}
.nav-btn .nav-icon{margin-right:6px;}

/* ── CATEGORY TABS ── */
.cat-tabs{background:var(--bg);border-bottom:1px solid var(--b1);overflow-x:auto;}
.cat-tabs::-webkit-scrollbar{height:3px;}
.ct-inner{max-width:1480px;margin:auto;display:flex;gap:4px;padding:6px 20px;}
.cat-btn{font-family:var(--fh);font-size:.72rem;font-weight:500;letter-spacing:.5px;
  padding:4px 14px;border-radius:16px;border:1px solid var(--b1);
  background:transparent;color:var(--muted);cursor:pointer;transition:all .15s;white-space:nowrap;}
.cat-btn:hover{border-color:var(--b2);color:var(--fg2);}
.cat-btn.active{color:#fff;border-color:transparent;background:var(--blue);}
.cat-btn.nat-active{background:var(--orange);}

/* ── COMP FILTER BAR ── */
.comp-bar{background:var(--bg2);border-bottom:1px solid var(--b1);
  overflow-x:auto;}
.comp-bar::-webkit-scrollbar{height:3px;}
.cb-inner{max-width:1480px;margin:auto;display:flex;gap:4px;
  padding:8px 20px;white-space:nowrap;}
.cb-btn{font-family:var(--fh);font-size:.78rem;font-weight:500;letter-spacing:.5px;
  padding:5px 14px;border-radius:20px;border:1px solid var(--b1);
  background:transparent;color:var(--muted);cursor:pointer;transition:all .15s;}
.cb-btn:hover{border-color:var(--b2);color:var(--fg2);}
.cb-btn.active{color:#fff;border-color:transparent;}

/* ── WEEK BAR ── */
.week-bar{background:var(--bg2);border-bottom:1px solid var(--b1);}
.wb-inner{max-width:1480px;margin:auto;display:flex;align-items:center;
  gap:8px;padding:8px 20px;}
.wb-nav{font-size:1.2rem;padding:4px 10px;border:1px solid var(--b1);
  border-radius:6px;background:transparent;color:var(--muted);cursor:pointer;transition:all .15s;}
.wb-nav:hover{color:var(--blue);border-color:var(--blue);}
.week-label{font-family:var(--fh);font-size:1rem;font-weight:500;letter-spacing:.5px;color:var(--fg2);flex:1;text-align:center;}
.today-btn{font-size:.72rem;padding:4px 12px;border:1px solid var(--blue)44;
  border-radius:6px;background:var(--blue)11;color:var(--blue);cursor:pointer;transition:all .15s;}
.today-btn:hover{background:var(--blue)22;}

/* ── MAIN ── */
main{max-width:1480px;margin:auto;padding:20px;}

/* ── LOADING / ERROR ── */
.loading{text-align:center;padding:80px 0;color:var(--muted);}
.spin{width:38px;height:38px;border-radius:50%;border:3px solid var(--b2);
  border-top-color:var(--green);animation:rot .7s linear infinite;margin:auto;}
@keyframes rot{to{transform:rotate(360deg);}}
.err-box{background:#1a0808;border:1px solid var(--red)33;border-radius:var(--r2);
  padding:14px 18px;color:var(--red);font-size:.85rem;margin-bottom:16px;
  display:flex;align-items:center;gap:10px;}
.empty{text-align:center;padding:80px 20px;color:var(--muted);
  font-family:var(--fh);font-size:1.1rem;letter-spacing:.5px;}
.empty p{font-family:var(--fb);font-size:.85rem;margin-top:8px;color:var(--dim);}

/* ── DATE GROUP (calendrier) ── */
.date-group{margin-bottom:28px;}
.dg-header{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.dg-date{font-family:var(--fh);font-size:1rem;font-weight:600;letter-spacing:.5px;color:var(--fg2);}
.dg-dot{flex:1;height:1px;background:var(--b1);}
.dg-count{font-size:.68rem;color:var(--dim);}

/* ── MATCH CARD ── */
.mc{
  background:var(--card);border:1px solid var(--b1);border-radius:var(--r2);
  margin-bottom:6px;padding:12px 16px;
  display:grid;grid-template-columns:auto 1fr 100px 1fr auto;
  gap:12px;align-items:center;
  transition:border-color .2s,transform .15s,box-shadow .2s;
  position:relative;overflow:hidden;
}
.mc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;}
.mc:hover{border-color:var(--b2);transform:translateX(2px);box-shadow:0 2px 16px #00000055;}
.mc.is-live{border-color:var(--blue)55;}
.mc.is-live::after{content:'LIVE';position:absolute;top:8px;right:10px;
  font-size:.55rem;font-weight:700;letter-spacing:1px;color:var(--blue);
  background:var(--blue)15;padding:2px 6px;border-radius:3px;
  animation:blink 1.5s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.4;}}
.mc.is-fin{opacity:.75;}

/* Comp badge */
.comp-badge{
  display:flex;flex-direction:column;align-items:center;gap:2px;
  width:34px;flex-shrink:0;
}
.cb-flag{font-size:1rem;}
.cb-code{font-size:.52rem;color:var(--muted);letter-spacing:.5px;font-family:var(--fh);}

/* Teams */
.team-col{display:flex;flex-direction:column;gap:6px;}
.team-row{display:flex;align-items:center;gap:8px;}
.team-crest{width:18px;height:18px;object-fit:contain;flex-shrink:0;}
.team-name{font-family:var(--fh);font-size:1rem;font-weight:600;letter-spacing:.2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.form-pills{display:flex;gap:2px;margin-left:auto;flex-shrink:0;}
.fp{width:16px;height:16px;border-radius:3px;font-size:.5rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;}
.fp.W{background:var(--green)20;color:var(--green);}
.fp.D{background:var(--yellow)20;color:var(--yellow);}
.fp.L{background:var(--red)20;color:var(--red);}

/* Score / VS center */
.match-center{display:flex;flex-direction:column;align-items:center;gap:3px;flex-shrink:0;}
.mc-time{font-size:.65rem;color:var(--muted);letter-spacing:.5px;}
.mc-vs{font-family:var(--fh);font-size:1.2rem;font-weight:500;color:var(--b3);letter-spacing:2px;}
.mc-score{font-family:var(--fh);font-size:1.5rem;font-weight:700;
  color:var(--fg);letter-spacing:4px;line-height:1;}
.mc-ht{font-size:.58rem;color:var(--dim);}
.mc-status{font-size:.6rem;color:var(--muted);}

/* Prono (right side) */
.mc-prono{display:flex;flex-direction:column;gap:5px;min-width:0;}
.odds-wrap{display:flex;gap:3px;}
.od{flex:1;border:1px solid var(--b1);border-radius:5px;padding:5px 3px;
  text-align:center;background:var(--bg3);}
.od.best-green{border-color:var(--green)55;background:linear-gradient(135deg,#002b14,#0d1c30);}
.od.best-orange{border-color:var(--orange)55;background:linear-gradient(135deg,#2b1000,#0d1c30);}
.od.best-yellow{border-color:var(--yellow)44;background:linear-gradient(135deg,#2b2300,#0d1c30);}
.od-lbl{font-size:.52rem;color:var(--muted);text-transform:uppercase;letter-spacing:.3px;}
.od-val{font-family:var(--fh);font-size:.92rem;font-weight:600;}
.od.best-green .od-val{color:var(--green);}
.od.best-orange .od-val{color:var(--orange);}
.od.best-yellow .od-val{color:var(--yellow);}
.od-pct{font-size:.5rem;color:var(--dim);}
.prono-hint{display:flex;align-items:center;gap:5px;}
.ph-pill{font-family:var(--fh);font-size:.7rem;padding:2px 8px;border-radius:3px;font-weight:600;}
.ph-1{background:var(--green)15;color:var(--green);}
.ph-X{background:var(--yellow)15;color:var(--yellow);}
.ph-2{background:var(--orange)15;color:var(--orange);}
.ph-conf{font-size:.6rem;color:var(--dim);margin-left:auto;}
.conf-line{height:2px;background:var(--b1);border-radius:2px;overflow:hidden;}
.cl-fill{height:100%;border-radius:2px;}
.no-prono{font-size:.72rem;color:var(--dim);font-style:italic;}

/* ── PRONO HEADER (model + value) ── */
.prono-header{display:flex;align-items:center;gap:5px;margin-bottom:4px;}
.model-badge{font-size:.5rem;color:var(--muted);border:1px solid var(--b2);
  padding:1px 5px;border-radius:3px;letter-spacing:.3px;white-space:nowrap;}
.form-badge{color:var(--yellow);border-color:var(--yellow)33;}
.value-badge{font-size:.55rem;color:var(--green);background:var(--green)12;
  border:1px solid var(--green)44;padding:1px 6px;border-radius:3px;
  font-weight:700;letter-spacing:.3px;animation:pulse 2s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.6;}}

/* ── xG ROW ── */
.xg-row{display:flex;align-items:center;justify-content:center;gap:4px;
  margin:3px 0;padding:2px 0;border-top:1px solid var(--b1);border-bottom:1px solid var(--b1);}
.xg-val{font-family:var(--fh);font-size:.75rem;font-weight:600;color:var(--blue);min-width:22px;text-align:center;}
.xg-lbl{font-size:.5rem;color:var(--dim);letter-spacing:.5px;text-transform:uppercase;}

/* ── CLASSEMENTS ── */
.comp-tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;}
.ct-btn{font-family:var(--fh);font-size:.8rem;font-weight:500;letter-spacing:.5px;
  padding:6px 16px;border-radius:6px;border:1px solid var(--b1);
  background:transparent;color:var(--muted);cursor:pointer;transition:all .15s;}
.ct-btn:hover{color:var(--fg2);border-color:var(--b2);}
.ct-btn.active{color:#fff;border-color:transparent;}

.standings-table{width:100%;border-collapse:collapse;font-size:.85rem;}
.standings-table th{
  font-family:var(--fh);font-size:.72rem;font-weight:500;letter-spacing:.5px;
  text-transform:uppercase;color:var(--muted);text-align:center;
  padding:8px 6px;border-bottom:1px solid var(--b1);}
.standings-table th.left{text-align:left;}
.standings-table td{padding:8px 6px;text-align:center;border-bottom:1px solid var(--b1)44;}
.standings-table td.left{text-align:left;}
.standings-table tr:hover td{background:var(--card2);}
.std-pos{font-family:var(--fh);font-weight:600;color:var(--muted);width:28px;}
.std-pos.champions{color:var(--blue);}
.std-pos.ucl{color:var(--green);}
.std-pos.uel{color:var(--orange);}
.std-pos.releg{color:var(--red);}
.std-team{display:flex;align-items:center;gap:8px;}
.std-crest{width:18px;height:18px;object-fit:contain;}
.std-name{font-family:var(--fh);font-size:.9rem;font-weight:600;}
.std-pts{font-family:var(--fh);font-size:1rem;font-weight:700;color:var(--blue);}
.std-gd{color:var(--fg2);}
.std-form{display:flex;gap:2px;justify-content:center;}
.sf{width:14px;height:14px;border-radius:2px;font-size:.45rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;}
.sf.W{background:var(--green)20;color:var(--green);}
.sf.D{background:var(--yellow)20;color:var(--yellow);}
.sf.L{background:var(--red)20;color:var(--red);}

/* ── BUTEURS ── */
.scorers-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;}
.scorer-card{
  background:var(--card);border:1px solid var(--b1);border-radius:var(--r2);
  padding:12px 14px;display:flex;align-items:center;gap:12px;
  transition:border-color .2s;}
.scorer-card:hover{border-color:var(--b2);}
.scorer-rank{font-family:var(--fh);font-size:1.5rem;font-weight:700;
  color:var(--b3);width:32px;flex-shrink:0;}
.scorer-rank.top3{color:var(--yellow);}
.scorer-info{flex:1;min-width:0;}
.scorer-name{font-family:var(--fh);font-size:.95rem;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.scorer-team{display:flex;align-items:center;gap:5px;margin-top:2px;}
.scorer-team-name{font-size:.72rem;color:var(--muted);}
.scorer-stats{display:flex;gap:10px;flex-shrink:0;}
.ss-item{text-align:center;}
.ss-val{font-family:var(--fh);font-size:1.1rem;font-weight:700;color:var(--fg);}
.ss-val.goals{color:var(--green);}
.ss-lbl{font-size:.55rem;color:var(--muted);text-transform:uppercase;letter-spacing:.3px;}

/* ── GROUPES WC ── */
.wc-groups-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:4px;}
.wc-group-card{background:var(--card);border:1px solid var(--b1);border-radius:var(--r2);overflow:hidden;}
.wc-group-header{
  padding:8px 14px;font-family:var(--fh);font-size:.85rem;font-weight:700;
  letter-spacing:1px;display:flex;align-items:center;gap:8px;
  background:linear-gradient(90deg,var(--card2),var(--card));
  border-bottom:1px solid var(--b1);color:var(--yellow);}
.wc-group-table{width:100%;border-collapse:collapse;font-size:.8rem;}
.wc-group-table th{font-family:var(--fh);font-size:.65rem;font-weight:500;
  letter-spacing:.5px;text-transform:uppercase;color:var(--muted);
  text-align:center;padding:5px 4px;border-bottom:1px solid var(--b1);}
.wc-group-table th.left{text-align:left;padding-left:10px;}
.wc-group-table td{padding:6px 4px;text-align:center;border-bottom:1px solid var(--b1)22;}
.wc-group-table td.left{text-align:left;padding-left:10px;}
.wc-group-table tr:last-child td{border-bottom:none;}
.wc-group-table tr:hover td{background:var(--card2);}
.wc-team-row{display:flex;align-items:center;gap:6px;}
.wc-crest{width:16px;height:16px;object-fit:contain;}
.wc-team-name{font-family:var(--fh);font-size:.82rem;font-weight:600;}
.wc-pts{font-family:var(--fh);font-size:.9rem;font-weight:700;color:var(--blue);}
.wc-qual{color:var(--green);}
.wc-elim{color:var(--red);opacity:.5;}


/* ── SOURCES BADGES ── */
.prono-src{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;}
.src-badge{font-family:var(--fh);font-size:.6rem;font-weight:600;letter-spacing:.4px;
  padding:2px 7px;border-radius:10px;border:1px solid;cursor:help;}
.src-poi{color:var(--blue);border-color:var(--blue)44;background:var(--blue)11;}
.src-frm{color:var(--green);border-color:var(--green)44;background:var(--green)11;}
.src-h2h{color:var(--purple);border-color:var(--purple)44;background:var(--purple)11;}
.src-neu{color:var(--yellow);border-color:var(--yellow)44;background:var(--yellow)11;}

/* ── BARRE PROBABILITÉ TRICOLORE ── */
.prob-bar{display:flex;width:100%;height:14px;border-radius:7px;overflow:hidden;margin:7px 0;cursor:help;}
.pb-h{background:var(--blue);display:flex;align-items:center;justify-content:center;
  font-size:.55rem;font-weight:700;color:#fff;transition:width .4s;}
.pb-x{background:var(--muted);display:flex;align-items:center;justify-content:center;
  font-size:.55rem;font-weight:700;color:#fff;}
.pb-a{background:var(--orange);display:flex;align-items:center;justify-content:center;
  font-size:.55rem;font-weight:700;color:#fff;}

/* ── RATINGS ATT/DEF ── */
.ratings-row{display:flex;align-items:center;gap:6px;justify-content:center;
  padding:5px 0;margin:4px 0;border-top:1px solid var(--b1);border-bottom:1px solid var(--b1);}
.rat-wrap{display:flex;flex-direction:column;align-items:center;gap:1px;}
.rat-lbl{font-size:.55rem;color:var(--muted);font-family:var(--fh);letter-spacing:.5px;cursor:help;}
.rat-val{font-size:.78rem;font-weight:700;font-family:var(--fh);}
.rat-pos{color:var(--green);}
.rat-neg{color:var(--red);}
.rat-sep{font-size:.65rem;color:var(--dim);font-weight:500;margin:0 2px;}

/* ── BOUTON EXPLICATION ── */
.prono-explain-btn{width:100%;margin-top:6px;padding:4px 0;background:none;
  border:1px solid var(--b1);border-radius:6px;color:var(--muted);font-size:.65rem;
  cursor:pointer;transition:all .15s;text-align:center;}
.prono-explain-btn:hover{border-color:var(--blue);color:var(--blue);}

/* ── SÉLECTION NATIONALE (prono désactivé) ── */
.nat-no-prono{text-align:center;padding:10px 8px;}
.nat-prono-icon{font-size:1.2rem;margin-bottom:4px;}
.nat-prono-txt{font-family:var(--fh);font-size:.72rem;font-weight:600;color:var(--fg2);}
.nat-prono-sub{font-size:.6rem;color:var(--dim);margin-top:4px;line-height:1.4;}

/* ── MODAL EXPLICATION PRONOSTIC ── */
.prono-modal-bg{position:fixed;inset:0;background:#000a;z-index:9999;
  display:flex;align-items:center;justify-content:center;padding:16px;}
.prono-modal{background:var(--card);border:1px solid var(--b2);border-radius:16px;
  max-width:480px;width:100%;max-height:90vh;overflow-y:auto;padding:24px;}
.pm-title{font-family:var(--fh);font-size:1rem;font-weight:700;color:var(--yellow);
  margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;}
.pm-close{cursor:pointer;color:var(--muted);font-size:1.2rem;line-height:1;}
.pm-close:hover{color:var(--fg);}
.pm-section{margin-bottom:14px;}
.pm-section-title{font-family:var(--fh);font-size:.72rem;font-weight:600;
  letter-spacing:.8px;text-transform:uppercase;color:var(--blue);margin-bottom:8px;}
.pm-row{display:flex;justify-content:space-between;align-items:center;
  padding:5px 0;border-bottom:1px solid var(--b1)11;font-size:.78rem;}
.pm-row:last-child{border-bottom:none;}
.pm-label{color:var(--muted);}
.pm-value{font-weight:600;font-family:var(--fh);}
.pm-formula{background:var(--bg3);border-radius:8px;padding:10px 12px;
  font-family:monospace;font-size:.72rem;color:var(--fg2);margin:8px 0;line-height:1.8;}
.pm-note{font-size:.68rem;color:var(--dim);margin-top:8px;line-height:1.5;
  border-left:2px solid var(--b2);padding-left:8px;}
.pm-disclaimer{font-size:.65rem;color:var(--dim);text-align:center;margin-top:16px;
  padding-top:12px;border-top:1px solid var(--b1);}

/* ── RESPONSIVE ── */
@media(max-width:900px){
  .mc{grid-template-columns:auto 1fr 80px 1fr;gap:8px;}
  .mc-prono{display:none;}
}
@media(max-width:600px){
  .mc{grid-template-columns:auto 1fr 70px 1fr;gap:6px;padding:10px 12px;}
  .team-name{font-size:.9rem;}
  .mc-score{font-size:1.2rem;}
  .scorers-grid{grid-template-columns:1fr;}
}
</style>
</head>
<body>

<!-- ╔═ HEADER ════════════════════════════════════════════════════╗ -->
<header>
  <div class="hdr">
    <div class="logo">SPORTY<span style="-webkit-text-fill-color:var(--orange)">PRO</span></div>
    <div class="season-tag">SAISON 2025–26 · WC 2026</div>
    <div class="hdr-sep"></div>
    <div class="api-indicator">
      <span class="dot" id="apiDot"></span>
      <span id="apiTxt">Connexion...</span>
    </div>
    <button class="refresh-btn" onclick="refresh()">↻ Actualiser</button>
    <div style="font-size:.6rem;color:var(--muted);letter-spacing:.5px;flex-shrink:0;text-align:right;line-height:1.4;">
      <span style="color:var(--dim);">par</span><br/>
      <span style="color:var(--fg2);font-family:var(--fh);font-weight:500;">KOUAKOU CEDRIC</span>
    </div>
  </div>
</header>

<!-- ╔═ WC BANNER ══════════════════════════════════════════════════╗ -->
<div id="wcBanner" style="
  background:linear-gradient(90deg,#1a1200,#2a1f00,#1a1200);
  border-bottom:1px solid #c8a40044;
  padding:7px 20px;display:flex;align-items:center;justify-content:center;gap:12px;
  font-size:.78rem;color:#f0d060;font-family:var(--font-h,Oswald),sans-serif;
  letter-spacing:.5px;">
  🌍 <span>FIFA WORLD CUP 2026</span>
  <span style="color:#888;font-size:.7rem;">|</span>
  <span id="wcCountdown" style="color:#ffd43b;font-weight:700;"></span>
  <span style="color:#888;font-size:.7rem;">|</span>
  <span>USA · CANADA · MEXIQUE</span>
  <button onclick="setCat('national');setComp('WC','#c8a400');showPage('cal')"
    style="margin-left:8px;font-family:inherit;font-size:.72rem;padding:3px 12px;
    border:1px solid #c8a40066;border-radius:4px;background:#c8a40015;
    color:#ffd43b;cursor:pointer;">
    Voir les matchs →
  </button>
</div>
<script>
(function(){
  const wc = new Date('2026-06-12T00:00:00');
  function tick(){
    const diff = wc - new Date();
    if(diff < 0){ document.getElementById('wcCountdown').textContent='En cours !'; return; }
    const days = Math.floor(diff/864e5);
    const hrs  = Math.floor((diff%864e5)/36e5);
    document.getElementById('wcCountdown').textContent = `J-${days} (${hrs}h)`;
  }
  tick(); setInterval(tick, 60000);
})();
</script>

<!-- ╔═ NAV ═══════════════════════════════════════════════════════╗ -->
<nav>
  <div class="nav-inner">
    <button class="nav-btn active" data-page="cal"       onclick="showPage('cal')">
      <span class="nav-icon">📅</span>Calendrier
    </button>
    <button class="nav-btn"        data-page="wc"        onclick="showPage('wc')">
      <span class="nav-icon">🌍</span>Groupes WC
    </button>
    <button class="nav-btn"        data-page="standings" onclick="showPage('standings')">
      <span class="nav-icon">🏆</span>Classements
    </button>
    <button class="nav-btn"        data-page="scorers"   onclick="showPage('scorers')">
      <span class="nav-icon">⚽</span>Buteurs
    </button>
  </div>
</nav>

<!-- ╔═ CATEGORY FILTER ═══════════════════════════════════════════╗ -->
<div class="cat-tabs" id="catTabs">
  <div class="ct-inner">
    <button class="cat-btn active" onclick="setCat('ALL')">🌐 Tout</button>
    <button class="cat-btn" onclick="setCat('national')">🏳️ Sélections</button>
    <button class="cat-btn" onclick="setCat('club')">🏟️ Clubs</button>
    <button class="cat-btn" onclick="setCat('cup')">🏆 Coupes</button>
  </div>
</div>

<!-- ╔═ COMP FILTER (partagé) ═════════════════════════════════════╗ -->
<div class="comp-bar" id="compBar">
  <div class="cb-inner" id="compBtns">
    <div class="spin" style="width:16px;height:16px;border-width:2px;margin:4px 0;"></div>
  </div>
</div>

<!-- ╔═ WEEK BAR (cal seulement) ══════════════════════════════════╗ -->
<div class="week-bar" id="weekBar">
  <div class="wb-inner">
    <button class="wb-nav" onclick="changeWeek(-1)">&#8249;</button>
    <div class="week-label" id="weekLabel">Chargement...</div>
    <button class="wb-nav" onclick="changeWeek(+1)">&#8250;</button>
    <button class="today-btn" onclick="goToday()">Aujourd'hui</button>
  </div>
</div>

<!-- ╔═ MAIN ══════════════════════════════════════════════════════╗ -->
<main id="main">
  <div class="loading"><div class="spin"></div><p style="margin-top:16px">Chargement...</p></div>
</main>

<script>
// ══ STATE ══════════════════════════════════════════════════════════
let page    = 'cal';
let comp    = 'ALL';
let cat     = 'ALL';   // 'ALL' | 'national' | 'club'
let allWeeks = [];
let weekIdx  = -1;
let comps    = [];
let calVersion = 0;  // incrémenté à chaque loadCalendar pour ignorer les pronos obsolètes

// ══ INIT ═══════════════════════════════════════════════════════════
(async () => {
  await Promise.all([loadComps(), loadWeeks(), checkApi()]);
  showPage('cal');
  setInterval(() => { checkApi(); if(page==='cal') loadCalendar(); }, 5*60*1000);
})();

// ══ API STATUS ══════════════════════════════════════════════════════
async function checkApi(){
  try {
    const d = await fetch('/api/status').then(r=>r.json());
    document.getElementById('apiDot').className = 'dot ' + (d.ok?'ok':'err');
    document.getElementById('apiTxt').textContent = d.ok ? 'API connectée' : 'API erreur';
  } catch(_){}
}

// ══ COMPETITIONS ════════════════════════════════════════════════════
async function loadComps(){
  comps = await fetch('/api/comps').then(r=>r.json());
  renderCompBtns();
}

function renderCompBtns(){
  const all = [{code:'ALL', name:'Toutes', flag:'🌐', color:'#3d9bff', category:'ALL'}];
  // Filtrer par catégorie sélectionnée
  const filtered = cat === 'ALL' ? comps : comps.filter(c => c.category === cat || (cat === 'club' && c.category === 'cup'));
  const list = all.concat(filtered);
  document.getElementById('compBtns').innerHTML = list.map(c => {
    const isActive = c.code === comp;
    return `<button class="cb-btn ${isActive?'active':''}"
      style="${isActive ? 'background:'+c.color+';border-color:'+c.color : ''}"
      onclick="setComp('${c.code}','${c.color||'#3d9bff'}')">
      ${c.flag} ${c.name}
    </button>`;
  }).join('');
}

function setCat(c){
  cat = c;
  // Si comp actuel n'est plus dans le filtre, reset à ALL
  if(cat !== 'ALL'){
    const visible = comps.filter(x => x.category === cat);
    if(comp !== 'ALL' && !visible.find(x => x.code === comp)){
      comp = 'ALL';
    }
  }
  // Mettre à jour les boutons de catégorie
  document.querySelectorAll('.cat-btn').forEach(b => {
    const txt = b.textContent.trim();
    const map = {'🌐 Tout':'ALL','🏳️ Sélections':'national','🏟️ Clubs':'club','🏆 Coupes':'cup'};
    const bc = Object.entries(map).find(([k])=>txt.includes(k.slice(2)))?.[1] || 'ALL';
    b.classList.toggle('active', bc === cat);
    if(cat === 'national') b.style.background = bc==='national' ? 'var(--orange)' : '';
    else b.style.background = '';
  });
  renderCompBtns();
  loadCurrentPage();
}

function setComp(code, color){
  comp = code;
  // Si on sélectionne une compétition nationale directement, activer le filtre nat
  if(code !== 'ALL'){
    const c = comps.find(x => x.code === code);
    if(c && c.category === 'national' && cat === 'club'){
      cat = 'national';
    } else if(c && c.category === 'club' && cat === 'national'){
      cat = 'club';
    }
  }
  renderCompBtns();
  loadCurrentPage();
}

// ══ WEEKS ═══════════════════════════════════════════════════════════
async function loadWeeks(){
  allWeeks = await fetch('/api/weeks').then(r=>r.json());
  // Trouver la semaine courante
  weekIdx = allWeeks.findIndex(w => w.current);
  if(weekIdx < 0) weekIdx = Math.max(0, allWeeks.findIndex(w => !w.past) - 1);
  if(weekIdx < 0) weekIdx = 0;
  updateWeekLabel();
}

function updateWeekLabel(){
  if(!allWeeks.length) return;
  const w = allWeeks[weekIdx];
  document.getElementById('weekLabel').textContent = w ? w.label : '—';
}

function changeWeek(delta){
  weekIdx = Math.max(0, Math.min(allWeeks.length-1, weekIdx + delta));
  updateWeekLabel();
  loadCalendar();
}

function goToday(){
  weekIdx = allWeeks.findIndex(w => w.current);
  if(weekIdx < 0) weekIdx = 0;
  updateWeekLabel();
  loadCalendar();
}

// ══ PAGES ═══════════════════════════════════════════════════════════
function showPage(p){
  page = p;
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.toggle('active', b.dataset.page===p));
  document.getElementById('weekBar').style.display   = p==='cal' ? '' : 'none';
  document.getElementById('catTabs').style.display   = p==='cal' ? '' : 'none';
  document.getElementById('compBar').style.display   = (p==='cal'||p==='standings'||p==='scorers') ? '' : 'none';
  loadCurrentPage();
}

function loadCurrentPage(){
  if(page==='cal')            loadCalendar();
  else if(page==='wc')        loadWCGroups();
  else if(page==='standings') loadStandings();
  else if(page==='scorers')   loadScorers();
}

function refresh(){ checkApi(); loadCurrentPage(); }

// ══ CALENDRIER ══════════════════════════════════════════════════════
async function loadCalendar(){
  const myVersion = ++calVersion;
  setLoading('Chargement des matchs...');
  const week = allWeeks[weekIdx]?.week || '';
  const compParam = comp === 'ALL' ? 'ALL' : comp;
  const catParam  = cat  === 'ALL' ? 'ALL' : cat;
  let data;
  try {
    // Étape 1 : charger les matchs sans pronos (rapide ~1-2s)
    data = await fetch(`/api/matches?week=${week}&comp=${compParam}&cat=${catParam}&prono=0`).then(r=>r.json());
  } catch(e) {
    setError('Erreur réseau. Vérifiez votre connexion.');
    return;
  }
  if(myVersion !== calVersion) return;  // l'utilisateur a changé de comp entre temps
  if(data.error){ setError(data.error); return; }
  const matches = data.matches || [];
  renderCalendar(matches);

  // Étape 2 : charger les pronos en arrière-plan (peut prendre du temps)
  if(matches.length > 0){
    loadPronosBackground(week, compParam, catParam, matches, myVersion);
  }
}

async function loadPronosBackground(week, compParam, catParam, matchesSansProno, myVersion){
  // Affiche un bandeau discret
  const pronoBar = document.createElement('div');
  pronoBar.id = 'prono-bar';
  pronoBar.style.cssText = 'text-align:center;padding:8px;font-size:.75rem;color:var(--muted);';
  pronoBar.innerHTML = '<span class="spin" style="display:inline-block;width:10px;height:10px;border-width:2px;vertical-align:middle;margin-right:6px;"></span>Calcul des pronostics en cours...';
  const mainEl = document.getElementById('main');
  if(mainEl) mainEl.prepend(pronoBar);

  try {
    const data2 = await fetch(`/api/matches?week=${week}&comp=${compParam}&cat=${catParam}&prono=1`).then(r=>r.json());
    const bar = document.getElementById('prono-bar');
    if(bar) bar.remove();
    // Si l'utilisateur a changé de comp/semaine, on ignore ce résultat obsolète
    if(myVersion !== calVersion) return;
    if(!data2.error && data2.matches && data2.matches.length > 0){
      renderCalendar(data2.matches);
    }
  } catch(e) {
    const bar = document.getElementById('prono-bar');
    if(bar) bar.remove();
  }
}

function renderCalendar(matches){
  if(!matches.length){
    document.getElementById('main').innerHTML =
      `<div class="empty">📭 Aucun match cette semaine<p>Changez de semaine ou de compétition.</p></div>`;
    return;
  }

  // Grouper par date
  const byDate = {};
  matches.forEach(m => {
    const d = m.date || 'Inconnue';
    if(!byDate[d]) byDate[d] = [];
    byDate[d].push(m);
  });

  let html = '';
  Object.entries(byDate).sort().forEach(([d, ms]) => {
    const label = fmtDate(d);
    html += `<div class="date-group">
      <div class="dg-header">
        <span class="dg-date">${label}</span>
        <span class="dg-dot"></span>
        <span class="dg-count">${ms.length} match${ms.length>1?'s':''}</span>
      </div>`;
    ms.forEach(m => { html += matchCard(m); });
    html += `</div>`;
  });

  document.getElementById('main').innerHTML = html;
}

function matchCard(m){
  const status = (m.status||'').toUpperCase();
  const isLive = status.includes('LIVE')||status.includes('IN_PLAY')||status.includes('INPLAY');
  const isFin  = status.includes('FINISH')||status.includes('FT')||status.includes('FINAL');

  let timeStr = '—';
  if(m.datetime){ try{ timeStr = new Date(m.datetime).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}); }catch(_){} }

  // Center block
  let centerHtml;
  if(isFin && m.score_home!=null && m.score_away!=null){
    const ht = (m.ht_home!=null && m.ht_away!=null) ? `<div class="mc-ht">(${m.ht_home}–${m.ht_away} MT)</div>` : '';
    centerHtml = `<div class="mc-score">${m.score_home}–${m.score_away}</div>${ht}<div class="mc-status">Terminé</div>`;
  } else if(isLive){
    const min = m.minute ? `${m.minute}'` : '';
    centerHtml = `<div class="mc-score">${m.score_home??0}–${m.score_away??0}</div><div class="mc-time" style="color:var(--blue)">${min}</div>`;
  } else {
    const md = m.matchday ? `<div class="mc-ht">J.${m.matchday}</div>` : '';
    centerHtml = `<div class="mc-time">${timeStr}</div><div class="mc-vs">–</div>${md}`;
  }

  // Forme
  const fmtF = f => (f||[]).map(r=>`<div class="fp ${r}">${r}</div>`).join('');

  // Crests
  const hImg = m.home_crest ? `<img class="team-crest" src="${m.home_crest}" onerror="this.style.display='none'" loading="lazy"/>` : '';
  const aImg = m.away_crest ? `<img class="team-crest" src="${m.away_crest}" onerror="this.style.display='none'" loading="lazy"/>` : '';

  // ── PRONOSTIC ─────────────────────────────────────────────────
  const NATIONAL = ['WC','EUR','UNL','NL','CA','ACN','WCQ','QCAF','QAFC','QCONMEBOL','QCONCACAF'];
  let pronoHtml;

  if(NATIONAL.includes(m.comp_code)){
    pronoHtml = `<div class="mc-prono nat-no-prono">
      <div class="nat-prono-icon">🏳️</div>
      <div class="nat-prono-txt">Sélection nationale</div>
      <div class="nat-prono-sub">Le modèle utilise les stats de championnat (buts/match, classement). Non applicable pour les équipes nationales.</div>
    </div>`;
  } else {
    const p = m.prono;
    if(!p){
      pronoHtml = `<div class="mc-prono"><div class="no-prono">Calcul en cours…</div></div>`;
    } else {
      const best      = p.label;
      const bestName  = best==='1' ? m.home : (best==='2' ? m.away : 'Match nul');
      const cls       = {1:'best-green',2:'best-orange','X':'best-yellow'}[best] || '';
      const confColor = p.conf>=65?'var(--green)':p.conf>=50?'var(--yellow)':'var(--red)';

      // Badges sources
      const badges = [];
      if(p.model.includes('poisson')) badges.push(`<span class="src-badge src-poi" title="Modèle Double-Poisson : ratings attaque/défense du classement">⚙ Poisson</span>`);
      if(p.model.includes('forme'))   badges.push(`<span class="src-badge src-frm" title="Forme récente : ${(p.detail&&p.detail.home_form_n)||0} matchs pondérés (plus récent = plus de poids)">📈 Forme</span>`);
      if(p.h2h && p.h2h !== 1.0)      badges.push(`<span class="src-badge src-h2h" title="H2H : historique des duels directs (6 derniers matchs)">⚔ H2H ${p.h2h>1?'+':''}${Math.round((p.h2h-1)*100)}%</span>`);
      if(p.model==='neutre')           badges.push(`<span class="src-badge src-neu" title="Données insuffisantes — estimation par défaut + avantage domicile">⚠ Estimation</span>`);

      // Ratings att/def
      let ratHtml = '';
      if(p.detail && p.detail.home_att != null){
        const d = p.detail;
        const vc = v => v>1.1?'rat-pos':v<0.9?'rat-neg':'';
        const dc = v => v<0.9?'rat-pos':v>1.1?'rat-neg':'';
        ratHtml = `<div class="ratings-row">
          <div class="rat-wrap">
            <span class="rat-lbl" title="Force offensive normalisée (1.0 = moyenne ligue)">ATT</span>
            <span class="rat-val ${vc(d.home_att)}">${d.home_att}</span>
          </div>
          <div class="rat-wrap">
            <span class="rat-lbl" title="Perméabilité défensive (bas = bonne défense)">DEF</span>
            <span class="rat-val ${dc(d.home_def)}">${d.home_def}</span>
          </div>
          <span class="rat-sep">vs</span>
          <div class="rat-wrap">
            <span class="rat-lbl">ATT</span>
            <span class="rat-val ${vc(d.away_att)}">${d.away_att}</span>
          </div>
          <div class="rat-wrap">
            <span class="rat-lbl">DEF</span>
            <span class="rat-val ${dc(d.away_def)}">${d.away_def}</span>
          </div>
        </div>`;
      }

      // Barre probabilité tricolore
      const probBar = `<div class="prob-bar" title="Probabilités : ${m.home} ${p.p_home}% | Nul ${p.p_draw}% | ${m.away} ${p.p_away}%">
        <div class="pb-h" style="width:${p.p_home}%">${p.p_home>16?p.p_home+'%':''}</div>
        <div class="pb-x" style="width:${p.p_draw}%">${p.p_draw>10?p.p_draw+'%':''}</div>
        <div class="pb-a" style="width:${p.p_away}%">${p.p_away>16?p.p_away+'%':''}</div>
      </div>`;

      pronoHtml = `<div class="mc-prono">
        <div class="prono-src">${badges.join(' ')}</div>
        <div class="odds-wrap">
          <div class="od ${best==='1'?cls:''}" title="Victoire ${m.home} — ${p.p_home}% de chances">
            <div class="od-lbl">1</div>
            <div class="od-val">${p.odd_home??'—'}</div>
            <div class="od-pct">${p.p_home}%</div>
          </div>
          <div class="od ${best==='X'?cls:''}" title="Match nul — ${p.p_draw}% de chances">
            <div class="od-lbl">X</div>
            <div class="od-val">${p.odd_draw??'—'}</div>
            <div class="od-pct">${p.p_draw}%</div>
          </div>
          <div class="od ${best==='2'?cls:''}" title="Victoire ${m.away} — ${p.p_away}% de chances">
            <div class="od-lbl">2</div>
            <div class="od-val">${p.odd_away??'—'}</div>
            <div class="od-pct">${p.p_away}%</div>
          </div>
        </div>
        ${probBar}
        <div class="xg-row" title="xG = buts attendus selon Double-Poisson. Reflète la force offensive et la faiblesse défensive adverse.">
          <span class="xg-val">${p.xg_home}</span>
          <span class="xg-lbl">xG attendus</span>
          <span class="xg-val">${p.xg_away}</span>
        </div>
        ${ratHtml}
        <div class="prono-hint">
          <span class="ph-pill ph-${best}">▶ ${bestName}</span>
          <span class="ph-conf" style="color:${confColor}" title="Confiance : ${p.conf>=65?'Bonne':p.conf>=50?'Modérée':'Limitée'} (max 76% — honnêteté du modèle)">${p.conf}%</span>
        </div>
        <div class="conf-line"><div class="cl-fill" style="width:${p.conf}%;background:${confColor}"></div></div>
        <button class="prono-explain-btn" onclick="showPronoModal(event,${JSON.stringify(JSON.stringify(p))}, '${(m.home||'').replace(/'/g,"\\'")}','${(m.away||'').replace(/'/g,"\\'")}')">ℹ️ Comment c'est calculé ?</button>
      </div>`;
    }
  }
  return `<div class="mc ${isLive?'is-live':''} ${isFin?'is-fin':''}" style="--comp-color:${m.comp_color||'#444'}">
    <style>.mc[style*="${m.comp_color||'#444'}"]::before{background:${m.comp_color||'var(--b2)'}!important;}</style>
    <div class="comp-badge">
      <span class="cb-flag">${m.comp_flag||'⚽'}</span>
      <span class="cb-code">${m.comp_code||''}</span>
    </div>
    <div class="team-col">
      <div class="team-row">
        ${hImg}
        <div class="team-name">${m.home||'?'}</div>
        <div class="form-pills">${fmtF(m.home_form)}</div>
      </div>
      <div class="team-row">
        ${aImg}
        <div class="team-name">${m.away||'?'}</div>
        <div class="form-pills">${fmtF(m.away_form)}</div>
      </div>
    </div>
    <div class="match-center">${centerHtml}</div>
    <div style="display:flex;flex-direction:column;justify-content:center;opacity:.3;">
      <div style="font-family:var(--fh);font-size:.7rem;letter-spacing:.3px;color:var(--muted);">${m.stage||''}</div>
    </div>
    ${pronoHtml}
  </div>`;
}

// ══ GROUPES COUPE DU MONDE ══════════════════════════════════════════
async function loadWCGroups(){
  setLoading('Chargement des groupes Coupe du Monde...');
  let data;
  try {
    data = await fetch('/api/wc_groups').then(r=>r.json());
  } catch(e) {
    setError('Erreur réseau.');
    return;
  }

  if(data.error){
    document.getElementById('main').innerHTML = `
      <div style="text-align:center;padding:60px 20px;">
        <div style="font-size:3rem;margin-bottom:16px;">🌍</div>
        <div style="font-family:var(--fh);font-size:1.2rem;color:var(--yellow);letter-spacing:1px;margin-bottom:8px;">FIFA WORLD CUP 2026</div>
        <div style="font-size:.85rem;color:var(--muted);margin-bottom:20px;">USA · CANADA · MEXIQUE · 11 juin – 19 juillet 2026</div>
        <div class="err-box" style="max-width:500px;margin:0 auto;">⚠️ ${data.error}</div>
        <div style="margin-top:20px;font-size:.78rem;color:var(--dim);">
          Les groupes et points seront disponibles dès le coup d'envoi de la compétition (11 juin 2026).<br/>
          En attendant, le calendrier des matchs est accessible via l'onglet 📅 Calendrier → 🏳️ Sélections.
        </div>
      </div>`;
    return;
  }

  if(!data.groups || !Object.keys(data.groups).length){
    document.getElementById('main').innerHTML = `
      <div style="text-align:center;padding:60px 20px;">
        <div style="font-size:3rem;margin-bottom:16px;">🌍</div>
        <div style="font-family:var(--fh);font-size:1.2rem;color:var(--yellow);letter-spacing:1px;margin-bottom:8px;">FIFA WORLD CUP 2026</div>
        <div style="font-size:.85rem;color:var(--muted);margin-bottom:16px;">USA · CANADA · MEXIQUE · 11 juin – 19 juillet 2026</div>
        <div style="font-size:.78rem;color:var(--dim);max-width:460px;margin:0 auto;">
          Les 48 équipes qualifiées sont réparties en <strong style="color:var(--fg2)">12 groupes de 4</strong>.<br/>
          Les 2 premiers de chaque groupe + 8 meilleurs 3ᵉs se qualifient pour les 1/8.<br/><br/>
          <span style="color:var(--muted)">Les classements seront mis à jour en temps réel dès le début du tournoi.</span>
        </div>
      </div>`;
    return;
  }

  // Les groupes arrivent déjà triés depuis /api/wc_groups
  const groupMap = data.groups;
  const groups   = Object.keys(groupMap).sort();

  let html = `
    <div style="margin-bottom:16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <div style="font-family:var(--fh);font-size:1.1rem;font-weight:700;color:var(--yellow);letter-spacing:1px;">🌍 FIFA WORLD CUP 2026</div>
      <div style="font-size:.75rem;color:var(--muted);">USA · CANADA · MEXIQUE · ${groups.length} groupes · 48 nations</div>
      <div style="margin-left:auto;display:flex;gap:12px;font-size:.7rem;">
        <span><span style="color:var(--green)">■</span> Qualifié (top 2)</span>
        <span><span style="color:var(--yellow)">■</span> Meilleur 3ᵉ</span>
        <span><span style="color:var(--muted)">■</span> Éliminé</span>
      </div>
    </div>
    <div class="wc-groups-grid">`;

  groups.forEach(g => {
    const rows = groupMap[g];
    const label = g;  // déjà formaté côté serveur
    html += `<div class="wc-group-card">
      <div class="wc-group-header">🏆 ${label}</div>
      <table class="wc-group-table">
        <thead>
          <tr>
            <th class="left" colspan="2">Équipe</th>
            <th>MJ</th><th>G</th><th>N</th><th>P</th>
            <th>BP</th><th>BC</th>
            <th style="color:var(--blue)">Pts</th>
            <th>Forme</th>
          </tr>
        </thead>
        <tbody>`;
    rows.forEach((row, i) => {
      // Top 2 = qualifiés directement, 3e = potentiellement qualifié
      const posClass = i===0||i===1 ? 'wc-qual' : i===2 ? '' : 'wc-elim';
      const posIcon  = i===0||i===1 ? '✅' : i===2 ? '⚪' : '';
      const gd = row.gd > 0 ? '+'+row.gd : row.gd;
      const crest = row.crest ? `<img class="wc-crest" src="${row.crest}" onerror="this.style.display='none'" loading="lazy"/>` : '';
      const frmHtml = (row.form||[]).slice(-3).map(r=>`<div class="sf ${r}">${r}</div>`).join('');
      html += `<tr>
        <td class="left" style="width:10px;padding-right:0">${posIcon}</td>
        <td class="left">
          <div class="wc-team-row">${crest}<span class="wc-team-name ${posClass}">${row.name}</span></div>
        </td>
        <td>${row.played}</td>
        <td style="color:var(--green)">${row.won}</td>
        <td style="color:var(--yellow)">${row.draw}</td>
        <td style="color:var(--red)">${row.lost}</td>
        <td>${row.gf}</td>
        <td>${row.ga}</td>
        <td class="wc-pts">${row.pts}</td>
        <td><div class="std-form">${frmHtml}</div></td>
      </tr>`;
    });
    html += `</tbody></table></div>`;
  });

  html += `</div>`;
  document.getElementById('main').innerHTML = html;
}

// ══ CLASSEMENTS ═════════════════════════════════════════════════════
const STANDINGS_COMPS = ['WC','EUR','UNL','CA','ACN','WCQ','QCAF','QAFC','QCONMEBOL','QCONCACAF','CL','CLI','CS','PL','PD','SA','BL1','FL1','ELC','PPL','DED','BSA'];

async function loadStandings(){
  // Si comp sélectionné n'a pas de classement → prendre PL
  const sc = STANDINGS_COMPS.includes(comp) ? comp : 'PL';
  setLoading('Chargement du classement...');

  // Render comp tabs for standings
  let tabHtml = `<div class="comp-tabs">`;
  STANDINGS_COMPS.forEach(c => {
    const info = comps.find(x=>x.code===c) || {flag:'⚽', name:c, color:'#444'};
    const isA  = c === sc;
    tabHtml += `<button class="ct-btn ${isA?'active':''}"
      style="${isA?'background:'+info.color+';border-color:'+info.color:''}"
      onclick="selectStandingsComp('${c}')">
      ${info.flag} ${info.name}
    </button>`;
  });
  tabHtml += `</div>`;

  let data;
  try{
    data = await fetch(`/api/standings?comp=${sc}`).then(r=>r.json());
  }catch(e){
    setError('Erreur réseau.');
    return;
  }
  if(data.error){ document.getElementById('main').innerHTML = tabHtml + `<div class="err-box">⚠️ ${data.error}</div>`; return; }
  if(!data.table){ document.getElementById('main').innerHTML = tabHtml + `<div class="empty">Classement indisponible.</div>`; return; }

  const info = comps.find(x=>x.code===sc) || {name:sc, flag:'⚽'};
  let html = tabHtml + `<div style="overflow-x:auto;">
    <table class="standings-table">
      <thead>
        <tr>
          <th class="left">#</th>
          <th class="left">Equipe</th>
          <th>MJ</th><th>G</th><th>N</th><th>P</th>
          <th>BP</th><th>BC</th><th>DB</th>
          <th style="color:var(--blue)">Pts</th>
          <th>Forme</th>
        </tr>
      </thead>
      <tbody>`;

  data.table.forEach((row, i) => {
    const pos   = row.position;
    const posClass = pos===1?'champions':pos<=4?'ucl':pos<=6?'uel':pos>=data.table.length-2?'releg':'';
    const gd    = row.gd > 0 ? '+'+row.gd : row.gd;
    const frmHtml = (row.form||[]).slice(-5).map(r=>`<div class="sf ${r}">${r}</div>`).join('');
    const crest = row.crest ? `<img class="std-crest" src="${row.crest}" onerror="this.style.display='none'" loading="lazy"/>` : '';
    html += `<tr>
      <td class="std-pos ${posClass} left">${pos}</td>
      <td class="left">
        <div class="std-team">
          ${crest}
          <span class="std-name">${row.name}</span>
        </div>
      </td>
      <td>${row.played}</td>
      <td style="color:var(--green)">${row.won}</td>
      <td style="color:var(--yellow)">${row.draw}</td>
      <td style="color:var(--red)">${row.lost}</td>
      <td>${row.gf}</td>
      <td>${row.ga}</td>
      <td class="std-gd">${gd}</td>
      <td class="std-pts">${row.pts}</td>
      <td><div class="std-form">${frmHtml}</div></td>
    </tr>`;
  });

  html += `</tbody></table></div>`;

  // Legende
  html += `<div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;font-size:.7rem;color:var(--muted);">
    <span><span style="color:var(--blue)">■</span> Champion</span>
    <span><span style="color:var(--green)">■</span> Ligue des Champions</span>
    <span><span style="color:var(--orange)">■</span> Europa League</span>
    <span><span style="color:var(--red)">■</span> Relegation</span>
  </div>`;

  document.getElementById('main').innerHTML = html;
}

function selectStandingsComp(c){
  comp = c;
  renderCompBtns();
  loadStandings();
}

// ══ BUTEURS ═════════════════════════════════════════════════════════
async function loadScorers(){
  const sc = STANDINGS_COMPS.includes(comp) ? comp : 'PL';
  setLoading('Chargement des meilleurs buteurs...');

  let tabHtml = `<div class="comp-tabs">`;
  STANDINGS_COMPS.forEach(c => {
    const info = comps.find(x=>x.code===c) || {flag:'⚽', name:c, color:'#444'};
    const isA  = c === sc;
    tabHtml += `<button class="ct-btn ${isA?'active':''}"
      style="${isA?'background:'+info.color+';border-color:'+info.color:''}"
      onclick="selectScorersComp('${c}')">
      ${info.flag} ${info.name}
    </button>`;
  });
  tabHtml += `</div>`;

  let data;
  try{
    data = await fetch(`/api/scorers?comp=${sc}`).then(r=>r.json());
  }catch(e){
    setError('Erreur réseau.');
    return;
  }
  if(data.error){ document.getElementById('main').innerHTML = tabHtml + `<div class="err-box">⚠️ ${data.error}</div>`; return; }
  if(!data.scorers||!data.scorers.length){
    document.getElementById('main').innerHTML = tabHtml + `<div class="empty">Aucun buteur disponible.<p>Les données peuvent ne pas encore être disponibles pour cette compétition.</p></div>`;
    return;
  }

  let html = tabHtml + `<div class="scorers-grid">`;
  data.scorers.forEach((s, i) => {
    const rank = i + 1;
    const crest = s.crest ? `<img class="std-crest" src="${s.crest}" onerror="this.style.display='none'" loading="lazy"/>` : '';
    html += `<div class="scorer-card">
      <div class="scorer-rank ${rank<=3?'top3':''}">${rank<=3?['🥇','🥈','🥉'][rank-1]:rank}</div>
      <div class="scorer-info">
        <div class="scorer-name">${s.name}</div>
        <div class="scorer-team">${crest}<span class="scorer-team-name">${s.team}</span></div>
      </div>
      <div class="scorer-stats">
        <div class="ss-item">
          <div class="ss-val goals">${s.goals}</div>
          <div class="ss-lbl">Buts</div>
        </div>
        <div class="ss-item">
          <div class="ss-val">${s.assists}</div>
          <div class="ss-lbl">Passes</div>
        </div>
        <div class="ss-item">
          <div class="ss-val" style="color:var(--muted)">${s.matches}</div>
          <div class="ss-lbl">MJ</div>
        </div>
      </div>
    </div>`;
  });
  html += `</div>`;
  document.getElementById('main').innerHTML = html;
}

function selectScorersComp(c){
  comp = c;
  renderCompBtns();
  loadScorers();
}

// ══ UTILS ═══════════════════════════════════════════════════════════
function setLoading(msg='Chargement...'){
  document.getElementById('main').innerHTML =
    `<div class="loading"><div class="spin"></div><p style="margin-top:14px;font-size:.85rem">${msg}</p></div>`;
}
function setError(msg){
  document.getElementById('main').innerHTML = `<div class="err-box">⚠️ ${msg}</div>`;
}
function fmtDate(iso){
  if(!iso) return '—';
  try{
    const d   = new Date(iso + 'T12:00:00');
    const jrs = ['Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'];
    const mss = ['jan.','fév.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'];
    const today = new Date().toISOString().slice(0,10);
    const tmrw  = new Date(Date.now()+86400000).toISOString().slice(0,10);
    const pref  = iso===today ? 'Aujourd\'hui – ' : iso===tmrw ? 'Demain – ' : '';
    return pref + jrs[d.getDay()] + ' ' + d.getDate() + ' ' + mss[d.getMonth()] + ' ' + d.getFullYear();
  }catch(_){ return iso; }
}

// ══ MODAL EXPLICATION PRONOSTIC ════════════════════════════════════
function showPronoModal(e, pJson, home, away){
  e.stopPropagation();
  let p;
  try { p = JSON.parse(pJson); } catch(_){ return; }
  const d = p.detail || {};

  const srcLabels = {
    'poisson':       '⚙️ Double-Poisson + classement',
    'poisson+forme': '⚙️ Poisson + 📈 Forme récente',
    'poisson+forme+H2H': '⚙️ Poisson + 📈 Forme + ⚔ H2H',
    'forme+seule':   '📈 Forme récente uniquement',
    'forme+H2H':     '📈 Forme + ⚔ H2H',
    'neutre':        '⚠️ Estimation par défaut',
  };
  const srcLabel = srcLabels[p.model] || p.model || '?';

  const confLabel = p.conf>=65 ? '🟢 Bonne fiabilité' : p.conf>=50 ? '🟡 Modérée' : '🔴 Limitée (données insuffisantes)';

  let ratSection = '';
  if(d.home_att != null){
    ratSection = `
    <div class="pm-section">
      <div class="pm-section-title">📊 Ratings de classement</div>
      <div class="pm-row"><span class="pm-label">${home} — Attaque</span><span class="pm-value">${d.home_att} <small style="color:var(--dim)">(1.0 = moy. ligue)</small></span></div>
      <div class="pm-row"><span class="pm-label">${home} — Défense</span><span class="pm-value">${d.home_def} <small style="color:var(--dim)">(bas = solide)</small></span></div>
      <div class="pm-row"><span class="pm-label">${away} — Attaque</span><span class="pm-value">${d.away_att}</span></div>
      <div class="pm-row"><span class="pm-label">${away} — Défense</span><span class="pm-value">${d.away_def}</span></div>
      <div class="pm-row"><span class="pm-label">Moyenne buts / match (ligue)</span><span class="pm-value">${d.avg_g ?? '—'}</span></div>
      <div class="pm-row"><span class="pm-label">Avantage domicile</span><span class="pm-value">×${d.home_adv}</span></div>
    </div>`;
  }

  let formSection = '';
  if(d.home_form_n > 0 || d.away_form_n > 0){
    formSection = `
    <div class="pm-section">
      <div class="pm-section-title">📈 Forme récente</div>
      <div class="pm-row"><span class="pm-label">${home} — Matchs analysés</span><span class="pm-value">${d.home_form_n}</span></div>
      <div class="pm-row"><span class="pm-label">${home} — Facteur forme</span><span class="pm-value">${d.home_form_ff} <small style="color:var(--dim)">(1.0 = neutre)</small></span></div>
      <div class="pm-row"><span class="pm-label">${away} — Matchs analysés</span><span class="pm-value">${d.away_form_n}</span></div>
      <div class="pm-row"><span class="pm-label">${away} — Facteur forme</span><span class="pm-value">${d.away_form_ff}</span></div>
      <p class="pm-note">Les matchs récents ont plus de poids que les anciens (coefficient DECAY = 0.78). Victoire = 1.0 pt, Nul = 0.35 pt, Défaite = 0 pt.</p>
    </div>`;
  }

  let h2hSection = '';
  if(p.h2h && p.h2h !== 1.0){
    h2hSection = `
    <div class="pm-section">
      <div class="pm-section-title">⚔️ Confrontations directes (H2H)</div>
      <div class="pm-row"><span class="pm-label">Facteur H2H pour ${home}</span><span class="pm-value">${p.h2h} (${p.h2h>1?'+':''} ${Math.round((p.h2h-1)*100)}%)</span></div>
      <p class="pm-note">Basé sur les 6 derniers duels directs entre les deux équipes. Un facteur > 1.0 signifie que ${home} a dominé historiquement ${away}.</p>
    </div>`;
  }

  const html = `<div class="prono-modal-bg" onclick="this.remove()">
    <div class="prono-modal" onclick="event.stopPropagation()">
      <div class="pm-title">
        <span>🧮 Comment ce pronostic est calculé</span>
        <span class="pm-close" onclick="this.closest('.prono-modal-bg').remove()">✕</span>
      </div>

      <div class="pm-section">
        <div class="pm-section-title">🔬 Modèle utilisé</div>
        <div class="pm-row"><span class="pm-label">Méthode</span><span class="pm-value">${srcLabel}</span></div>
        <div class="pm-row"><span class="pm-label">Niveau de confiance</span><span class="pm-value">${p.conf}% — ${confLabel}</span></div>
      </div>

      <div class="pm-section">
        <div class="pm-section-title">⚽ Buts attendus (xG)</div>
        <div class="pm-row"><span class="pm-label">${home}</span><span class="pm-value">${p.xg_home} buts attendus</span></div>
        <div class="pm-row"><span class="pm-label">${away}</span><span class="pm-value">${p.xg_away} buts attendus</span></div>
        <div class="pm-formula">λ_dom = ATT_dom × DEF_ext × avg_ligue × 1.22 × forme × H2H
λ_ext = ATT_ext × DEF_dom × avg_ligue × forme × (1/H2H)</div>
        <p class="pm-note">λ (lambda) représente le nombre moyen de buts attendus. La distribution de Poisson calcule ensuite la probabilité de chaque score exact (0-0, 1-0, 0-1, 1-1...) jusqu'à 9-9.</p>
      </div>

      ${ratSection}${formSection}${h2hSection}

      <div class="pm-section">
        <div class="pm-section-title">📐 Probabilités finales</div>
        <div class="pm-row"><span class="pm-label">Victoire ${home}</span><span class="pm-value" style="color:var(--blue)">${p.p_home}%</span></div>
        <div class="pm-row"><span class="pm-label">Match nul</span><span class="pm-value" style="color:var(--muted)">${p.p_draw}%</span></div>
        <div class="pm-row"><span class="pm-label">Victoire ${away}</span><span class="pm-value" style="color:var(--orange)">${p.p_away}%</span></div>
        <div class="pm-row"><span class="pm-label">Cote indicative 1</span><span class="pm-value">${p.odd_home ?? '—'}</span></div>
        <div class="pm-row"><span class="pm-label">Cote indicative X</span><span class="pm-value">${p.odd_draw ?? '—'}</span></div>
        <div class="pm-row"><span class="pm-label">Cote indicative 2</span><span class="pm-value">${p.odd_away ?? '—'}</span></div>
        <p class="pm-note">Les cotes sont calculées depuis nos probabilités avec une marge de 5.5%. Ce sont des cotes théoriques indicatives, pas celles d'un bookmaker.</p>
      </div>

      <div class="pm-disclaimer">
        ⚠️ Ce pronostic est un outil statistique indicatif.<br>
        Il ne constitue pas un conseil de pari. Les matchs de football restent imprévisibles.<br>
        <strong>Jouez de manière responsable.</strong>
      </div>
    </div>
  </div>`;

  document.body.insertAdjacentHTML('beforeend', html);
}

</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
