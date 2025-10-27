# � World Dominion - Bot Discord de Stratégie

Bot Discord multijoueur de stratégie, économie et politique mondiale. Chaque joueur dirige un pays et doit équilibrer économie, politique et guerre pour dominer le monde.

## � Fonctionnalités Principales

### �️ Système Politique
- **8 niveaux hiérarchiques** : De Recrue à Chef d'État
- **Élections et coups d'État** : Démocratie et autoritarisme
- **Promotions** : Évolution selon l'expérience et la loyauté

### � Économie Complexe
- **6 ressources** : Argent, Nourriture, Métal, Pétrole, Énergie, Matériaux
- **Production et commerce** : Système d'échange entre pays
- **Impôts et budget** : Gestion financière nationale

### ⚔️ Système Militaire
- **5 types d'unités** : Soldats, Blindés, Avions, Missiles, Flotte
- **Guerres et espionnage** : Conflits stratégiques
- **Territoires** : Expansion et défense

### �️ Diplomatie
- **Alliances** : Coopération entre nations
- **Négociations** : Traités et accords
- **Embargos** : Guerre économique

## � Démarrage Rapide

### Option 1 : Démarrage Simple (Recommandé)
```bash
python start.py
```
Ce script démarre automatiquement le bot Discord ET le panel web d'administration.

### Option 2 : Démarrage Manuel

1. **Installer les dépendances** :
```bash
pip install -r requirements.txt
cd web
pip install -r requirements.txt
```

2. **Configuration** :
   - Copier `ENV_EXAMPLE.txt` vers `.env`
   - Remplir les variables d'environnement
   - Configurer Supabase
   - Configurer Discord OAuth pour le panel web

3. **Démarrer le bot** :
```bash
python main.py
```

4. **Démarrer le panel web** (dans un autre terminal) :
```bash
cd web
python run.py
```

## � Commandes Disponibles

### �️ Gestion des Pays
- `/rejoindre` - Rejoindre un pays (menu déroulant)
- `/pays` - Consulter les informations d'un pays
- `/classement` - Afficher le classement mondial
- `/lock-pays` - Verrouiller/déverrouiller un pays (Chef/Vice-Chef)

### � Économie
- `/produire` - Produire des ressources
- `/commerce` - Échanger avec d'autres pays
- `/taxe` - Fixer les impôts (Chef d'État)
- `/banque` - Consulter le budget national
- `/travail` - Travailler pour gagner de l'argent

### �️ Politique
- `/profil` - Consulter votre profil
- `/promouvoir` - Promouvoir un joueur (Chef d'État)
- `/élection` - Organiser une élection

### ⚔️ Militaire
- `/armée` - Consulter les forces armées
- `/attaquer` - Attaquer un pays (Chef d'État)
- `/espionner` - Espionner un pays
- `/défendre` - Renforcer les défenses
- `/territoire` - Consulter les territoires

### �️ Diplomatie
- `/alliance` - Gérer les alliances
- `/négocier` - Négocier avec un pays
- `/embargo` - Mettre un embargo (Chef d'État)

### � Administration
- `/create` - Créer un pays (Admin)
- `/own` - Assigner un pays à un joueur (Admin)
- `/admin-list` - Lister tous les pays (Admin)
- `/delete` - Supprimer des éléments d'un pays (Admin)
- `/web-panel` - Obtenir l'URL du panel web (Admin)

### � Événements
- `/events` - Consulter les événements récents
- `/trigger-event` - Déclencher un événement (Admin)

## � Panel d'Administration Web

Le bot inclut un **panel d'administration web complet** accessible via `/web-panel` :

### � Fonctionnalités du Panel
- **Dashboard en temps réel** : Statistiques et graphiques
- **Gestion complète des pays** : CRUD avec interface graphique
- **Administration des joueurs** : Modification des rôles et ressources
- **Contrôle des guerres** : Suivi et gestion des conflits
- **Outils avancés** : Réinitialisation, sauvegarde, logs

### � Accès
- **URL** : http://localhost:5000 (par défaut)
- **Authentification** : Discord OAuth2
- **Permissions** : Seuls les administrateurs Discord

## ⚙️ Configuration

### Variables d'Environnement Requises

```env
# Bot Discord
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Admin
ADMIN_ROLE_IDS=1234567890123456789,9876543210987654321

# Panel Web
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:5000/callback
WEB_SECRET_KEY=wd_admin_2024_secure_key_9f8e7d6c5b4a3928f1e0d9c8b7a6958473625140
WEB_PANEL_URL=http://localhost:5000
```

### Configuration Discord OAuth

1. Aller sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Sélectionner votre application
3. Aller dans "OAuth2" → "General"
4. Ajouter `http://localhost:5000/callback` dans "Redirects"
5. Copier le Client ID et Client Secret

## �️ Base de Données

Le bot utilise **Supabase** (PostgreSQL) avec les tables suivantes :
- `countries` - Informations des pays
- `players` - Données des joueurs
- `wars` - Historique des guerres
- `events` - Événements du jeu
- `alliances` - Alliances entre pays

## �️ Architecture

```
World Dominion/
├── main.py              # Point d'entrée du bot
├── start.py             # Script de démarrage complet
├── config.py            # Configuration
├── cogs/                # Modules du bot
│   ├── economy.py       # Commandes économiques
│   ├── politics.py      # Commandes politiques
│   ├── military.py      # Commandes militaires
│   ├── diplomacy.py     # Commandes diplomatiques
│   ├── country.py       # Gestion des pays
│   ├── admin.py         # Commandes admin
│   ├── events.py        # Système d'événements
│   └── web_panel.py     # Commande panel web
├── db/                  # Base de données
│   └── supabase.py      # Interface Supabase
├── utils/               # Utilitaires
│   ├── embeds.py        # Embeds Discord
│   └── logger.py        # Système de logs
└── web/                 # Panel d'administration
    ├── app.py           # Application Flask
    ├── run.py           # Démarrage du panel
    └── templates/       # Interface web
```

## � Dépannage

### Problèmes Courants

**Bot ne démarre pas** :
- Vérifier les variables d'environnement
- S'assurer que le token Discord est valide
- Vérifier la connexion Supabase

**Panel web inaccessible** :
- Vérifier que le port 5000 est libre
- Configurer correctement Discord OAuth
- Vérifier les permissions admin

**Erreurs de base de données** :
- Vérifier la connexion Supabase
- S'assurer que les tables existent
- Vérifier les permissions de l'API

### Logs
Les logs sont disponibles dans le dossier `logs/` et dans la console.

## � Support

Pour toute question ou problème :
1. Vérifier les logs de la console
2. Consulter la documentation Discord
3. Vérifier la configuration Supabase
4. Contacter l'équipe de développement

---

**World Dominion** - Dominez le monde par la stratégie ! ��
