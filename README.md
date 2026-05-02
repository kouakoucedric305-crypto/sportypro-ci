# ⚡ SportyPro CI — Site de Pronostics Sportifs

**Crédité par Kouakou Cedric · Saison 2026/2027**

Site de pronostics sportifs professionnel en Python/Flask, inspiré de SportyTrader.
Données réelles via **TheSportsDB API** (gratuit, sans clé API).

---

## 🏟️ Sports couverts

| Sport | Championnats |
|-------|-------------|
| ⚽ Football | Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions League, MLS, AFCON, CAF |
| 🏀 Basketball | NBA, Euroleague, WNBA |
| 🎾 Tennis | ATP Tour, WTA Tour |
| 🥊 MMA | UFC, Bellator MMA |

---

## 🚀 Lancer en local

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer le serveur
python app.py

# 3. Ouvrir dans le navigateur
# http://localhost:5000
```

---

## 🌐 Déploiement sur Render.com (GRATUIT)

**Render.com** est le meilleur hébergeur gratuit pour Python/Flask.

### Étapes :

1. **Créer un compte** sur [render.com](https://render.com) (gratuit)

2. **Créer un dépôt GitHub** et y uploader ce dossier :
   ```bash
   git init
   git add .
   git commit -m "SportyPro CI by Kouakou Cedric"
   git branch -M main
   git remote add origin https://github.com/TON_USERNAME/sportypro-ci.git
   git push -u origin main
   ```

3. **Sur Render.com** :
   - Cliquer sur **"New Web Service"**
   - Connecter votre compte GitHub
   - Sélectionner le dépôt `sportypro-ci`
   - Render détecte automatiquement Python + le `render.yaml`
   - Cliquer **"Deploy"**

4. **Votre site sera live sur** : `https://sportypro-ci.onrender.com`

### Plan gratuit Render :
- ✅ 512 MB RAM
- ✅ Domaine automatique `*.onrender.com`
- ✅ HTTPS gratuit
- ✅ Auto-déploiement depuis GitHub
- ⚠️ Le service "s'endort" après 15 min d'inactivité (plan gratuit)

---

## 🔧 Autres hébergeurs compatibles

| Hébergeur | Gratuit | Remarque |
|-----------|---------|----------|
| **Render.com** ⭐ | ✅ | Recommandé — facile, Python natif |
| **Railway.app** | ✅ (limité) | $5/mois après quota |
| **PythonAnywhere** | ✅ | Spécialisé Python, très simple |
| **Fly.io** | ✅ | Plus technique |
| **Heroku** | ❌ | Plus de plan gratuit |

---

## 📡 API utilisée

**TheSportsDB** (https://www.thesportsdb.com/api.php)
- Gratuit, sans inscription
- Multi-sports : Football, Basketball, Tennis, MMA
- Calendrier réel 2026/2027
- Pas de limite sévère pour usage personnel

---

## 📁 Structure du projet

```
sportytrader_cedric/
├── app.py                  # Application Flask principale
├── requirements.txt        # Dépendances Python
├── Procfile               # Config déploiement
├── render.yaml            # Config Render.com
├── templates/
│   ├── base.html          # Template de base (header/footer)
│   ├── index.html         # Page d'accueil
│   ├── sport.html         # Page par sport (Football, Basket…)
│   ├── match.html         # Détail d'un match
│   ├── pronostics.html    # Tous les pronostics
│   └── resultats.html     # Résultats récents
└── static/
    ├── css/style.css      # Design complet (dark sports theme)
    └── js/main.js         # Interactions JS
```

---

## 👤 Crédits

**Développé par Kouakou Cedric** — 2026  
Données : [TheSportsDB](https://www.thesportsdb.com)  
Design : Dark Sports / Néon Green — inspiré de SportyTrader.com

---

⚠️ *Les jeux d'argent peuvent être dangereux. Jouez de façon responsable. +18 uniquement.*
