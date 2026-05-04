# 🚀 Guide déploiement — SportyPro CI v3.0
## GitHub + Render.com GRATUIT (sans mise en veille via UptimeRobot)

---

## ✅ Compétitions football disponibles gratuitement

Ces 12 compétitions sont **gratuites pour toujours** avec votre clé football-data.org :

| Compétition | Code | Disponible |
|-------------|------|-----------|
| Premier League | PL | ✅ |
| La Liga | PD | ✅ |
| Bundesliga | BL1 | ✅ |
| Serie A | SA | ✅ |
| Ligue 1 | FL1 | ✅ |
| Champions League | CL | ✅ |
| Eredivisie (Pays-Bas) | DED | ✅ |
| Primeira Liga (Portugal) | PPL | ✅ |
| Championship (Angleterre D2) | ELC | ✅ |
| Brasileirão | BSA | ✅ |
| Coupe du Monde FIFA | WC | ✅ |
| Championnat d'Europe | EC | ✅ |

> ⚠️ CAF/AFCON, MLS, Ligue 2 française, etc. = plan payant (€49/mois minimum)

---

## 1. POUSSER SUR GITHUB

### Initialiser Git et pousser

```bash
# Dans votre dossier sportypro-ci/
cd chemin/vers/sportypro-ci

git init
git add .
git commit -m "SportyPro CI v3.0 — Fix basket + navigation jour par jour"

# Créer d'abord le dépôt sur https://github.com > New repository
# Nom : sportypro-ci — Public — sans README

git remote add origin https://github.com/TON_USERNAME/sportypro-ci.git
git branch -M main
git push -u origin main
```

Si GitHub demande un mot de passe :
- Aller sur https://github.com/settings/tokens
- "Generate new token (classic)" → cocher `repo` → copier le token
- Utiliser ce token comme mot de passe dans le terminal

### Mises à jour futures
```bash
git add .
git commit -m "Description de vos changements"
git push
# Render redéploie automatiquement !
```

---

## 2. DÉPLOYER SUR RENDER.COM (GRATUIT)

1. Créer un compte sur https://render.com (avec GitHub)
2. Dashboard → **"New +"** → **"Web Service"**
3. Connecter GitHub → sélectionner `sportypro-ci`

### Configuration

| Paramètre | Valeur |
|-----------|--------|
| Region | Frankfurt EU |
| Branch | `main` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| Instance Type | **Free** |

### Variables d'environnement

| Key | Value |
|-----|-------|
| `FOOTBALLDATA_KEY` | `fc2aba02543e4baaa3fcdc91f7d39c7c` |
| `SECRET_KEY` | `sportypro-cedric-2026-secret` |

Cliquer **"Create Web Service"** → live en 5 min sur `https://sportypro-ci.onrender.com`

---

## 3. EMPÊCHER LA MISE EN VEILLE — UptimeRobot GRATUIT

1. Créer un compte sur https://uptimerobot.com
2. "Add New Monitor" :

| Champ | Valeur |
|-------|--------|
| Monitor Type | HTTP(s) |
| URL | `https://sportypro-ci.onrender.com/api/status` |
| Interval | **10 minutes** |

✅ Votre site reste actif en permanence gratuitement.

---

## 4. MODIFIER VOS TEMPLATES HTML

### Dans `templates/index.html` — Navigation par date
Ajoutez ce bloc après votre header, avant la liste des matchs :

```html
<div style="display:flex;align-items:center;justify-content:center;gap:1rem;
            padding:0.8rem 1.2rem;background:rgba(255,255,255,0.05);
            border-radius:12px;margin-bottom:1.5rem;flex-wrap:wrap;">
  <a href="/?date={{ prev_date }}"
     style="background:#333;color:#aaa;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;">
    ‹ Hier
  </a>
  <span style="color:#00e676;font-weight:700;font-size:1rem;">
    {% if is_today %}📅 Aujourd'hui · {{ target_date.strftime('%d/%m/%Y') }}
    {% else %}📅 {{ target_date.strftime('%A %d %B %Y') }}{% endif %}
  </span>
  <a href="/?date={{ next_date }}"
     style="background:#333;color:#aaa;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;">
    Demain ›
  </a>
  {% if not is_today %}
  <a href="/" style="background:#00e676;color:#000;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;font-weight:700;">
    ↩ Aujourd'hui
  </a>
  {% endif %}
</div>
```

### Dans `templates/sport.html` — Navigation par date
Même bloc, avec les URLs `/sport/{{ sport_key }}?date=...` :

```html
<div style="display:flex;align-items:center;justify-content:center;gap:1rem;
            padding:0.8rem 1.2rem;background:rgba(255,255,255,0.05);
            border-radius:12px;margin-bottom:1.5rem;flex-wrap:wrap;">
  <a href="/sport/{{ sport_key }}?date={{ prev_date }}"
     style="background:#333;color:#aaa;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;">
    ‹ Jour préc.
  </a>
  <span style="color:{{ sport_cfg.color }};font-weight:700;font-size:1rem;">
    {% if is_today %}📅 Aujourd'hui · {{ target_date.strftime('%d/%m/%Y') }}
    {% else %}📅 {{ target_date.strftime('%A %d %B %Y') }}{% endif %}
  </span>
  <a href="/sport/{{ sport_key }}?date={{ next_date }}"
     style="background:#333;color:#aaa;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;">
    Jour suiv. ›
  </a>
  {% if not is_today %}
  <a href="/sport/{{ sport_key }}"
     style="background:{{ sport_cfg.color }};color:#000;padding:0.4rem 0.9rem;border-radius:8px;text-decoration:none;font-weight:700;">
    ↩ Aujourd'hui
  </a>
  {% endif %}
</div>
```

---

## 5. VÉRIFIER LE DÉPLOIEMENT

```
https://sportypro-ci.onrender.com/api/status           ← Football + basket OK ?
https://sportypro-ci.onrender.com/api/basketball/today ← Matchs basket JSON
https://sportypro-ci.onrender.com/sport/basketball     ← Page basket corrigée
https://sportypro-ci.onrender.com/?date=2026-05-10     ← Matchs du 10 mai
```

---

Crédité par Kouakou Cedric — SportyPro CI v3.0 — 2026
