# 🌍 World Dominion — Discord Bot de Stratégie & Panel Web Ultime

Bot Discord multijoueur où chaque joueur dirige un pays : gestion avancée de l’économie, de la politique, des guerres, alliances, le tout piloté par un panel web admin moderne et sécurisé.

---

## 🎯 Fonctionnalités Principales

### 🏛️ Politique
- **8 niveaux hiérarchiques** — Recrue à Chef d’État
- **Élections & coups d’État** — Gouvernance dynamique
- **Promotions** — Progression selon expérience & influence

### 💰 Économie
- **6 ressources** — Argent, Nourriture, Métal, Pétrole, Énergie, Matériaux
- **Production, commerce, impôts** — Moteur économique avancé
- **Gestion du budget national et individuel**

### ⚔️ Militaire
- **Cinq types d’unités** — Soldats, Blindés, Avions, Missiles, Flotte
- **Guerres stratégiques** — Déroulement et résolution réalistes
- **Espionnage & territoires**

### 🕊️ Diplomatie
- **Alliances, traités, embargos**
- **Négociation, coopération, compétition**

---

## 🚀 Démarrage Rapide

### Prérequis & Installation

```bash
python start.py               # Démarre Discord Bot & Panel Web
pip install -r requirements.txt
```

### Configuration rapide

- Copiez les variables d’environnement requises dans `.env` :
  - `DISCORD_TOKEN`, `DISCORD_GUILD_ID`
  - `SUPABASE_URL`, `SUPABASE_KEY`
  - `ADMIN_ROLE_IDS`
  - `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `WEB_SECRET_KEY`, `WEB_PANEL_URL`

(Exemple fourni en documentation / ci-dessous)

---

## 📋 Commandes Discord

### Pays
- `/rejoindre`, `/pays`, `/classement`, `/lock-pays`

### Économie
- `/produire`, `/commerce`, `/taxe`, `/banque`, `/travail`

### Politique
- `/profil`, `/promouvoir`, `/élection`

### Militaire
- `/armée`, `/attaquer`, `/espionner`, `/défendre`, `/territoire`

### Diplomatie
- `/alliance`, `/négocier`, `/embargo`

### Admin & Outils
- `/create`, `/own`, `/admin-list`, `/delete`, `/web-panel`

### Événements
- `/events`, `/trigger-event`

---

## 🌐 Panel d’Administration Web

Accessible uniquement aux admins Discord via `/web-panel`  
**Interface moderne et responsive — thème dark, sécurité OAuth2, tableau de bord temps réel !**

### Fonctionnalités majeures :
- **Statistiques graphiques en temps réel**
- **Gestion avancée pays, joueurs, guerre, événements**
- **Outils d’admin (reset, backup, logs Discord riches)**
- **Optimisation performance (Socket.IO, cache, rate limiting, monitoring healthz)**

---

## ⚙️ Configuration (exemple)

```env
# Discord
DISCORD_TOKEN=YOUR_TOKEN
DISCORD_GUILD_ID=123456789012345678

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Admin
ADMIN_ROLE_IDS=111222333,444555666

# Panel Web
DISCORD_CLIENT_ID=clientid
DISCORD_CLIENT_SECRET=secret
DISCORD_REDIRECT_URI=http://localhost:5000/callback
WEB_SECRET_KEY=xxxx   # Long et random !
WEB_PANEL_URL=http://localhost:5000
```

---

## 🗄️ Base de Données (Supabase)

- `countries` : infos pays
- `players` : joueurs
- `wars` : guerres
- `events` : logs historiques
- `alliances` : alliances (optionnel)

---

## 🏗️ Architecture

```
World Dominion/
├── start.py               # Point d’entrée unique
├── config.py              # Config centralisée et typage
├── cogs/                  # Modules Discord (commandes thématiques)
├── db/                    # Couche Supabase
├── utils/                 # Helpers, logs, embeds Discord
└── web/                   # Panel d’admin (Flask, Socket.IO, UI, statique)
```
- **Séparation claire backend / frontend / bot**
- **Code DRY et décorateurs pour la sécurité/optimisation**

---

## 🛡️ Sécurité, Monitoring et Qualité

- **OAuth2 Discord** — accès restreint admin
- **Rate limiting natif** — protection sur tous les endpoints API
- **Caching intelligent** — performance et économie du back
- **Healthcheck** — `/healthz` monitoring déploiement/cloud
- **Logs enrichis** — Discord/console/riches pour debug

---

## 🚨 Dépannage Rapide

- **Erreur de démarrage ?** → Vérifiez `.env`, les rôles Discord, la DB.
- **Panel web inaccessible** ? → Check port 5000, OAuth, autorisations Discord.
- **Erreurs DB** ? → Tables existantes, clés SUPABASE ?

---

## 🤝 Support et Contribution

1. Vérifiez les logs sur Render.com, Discord et la console Python
2. Consultez la documentation du code
3. Ouvrez une Issue ou une PR sur GitHub
4. Contact direct via le serveur Discord World Dominion

---

## 📜 Licence

MIT License  
**Développé avec ❤️ pour la stratégie et la diplomatie sur Discord**

---

**World Dominion** — Dominez le monde… ou coopérez pour survivre. 🌍👑

---

*README prêt à être copié/collé et à valoriser ton projet sur GitHub/render !*
Tu veux des sections de badges, GIFs, screenshots ou doc avancée ? Demande 😉