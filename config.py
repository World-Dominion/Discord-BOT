import os
from dotenv import load_dotenv

load_dotenv()

# Configuration Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))

# Configuration Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Configuration Admin
ADMIN_ROLE_IDS = [int(x) for x in os.getenv('ADMIN_ROLE_IDS', '').split(',') if x.strip()]

# Configuration du jeu
GAME_CONFIG = {
    'roles': {
        'chief': {'name': '👑 Chef d\'État', 'level': 1},
        'vice_chief': {'name': '⚖️ Vice-Chef', 'level': 2},
        'economy_minister': {'name': '💰 Ministre de l\'Économie', 'level': 3},
        'defense_minister': {'name': '🪖 Ministre de la Défense', 'level': 4},
        'governor': {'name': '🏙️ Gouverneur', 'level': 5},
        'officer': {'name': '⚙️ Officier', 'level': 6},
        'citizen': {'name': '👤 Citoyen', 'level': 7},
        'recruit': {'name': '🧒 Recrue', 'level': 8}
    },
    'resources': {
        'money': {'name': '💵 Argent', 'emoji': '💵'},
        'food': {'name': '🌾 Nourriture', 'emoji': '🍞'},
        'metal': {'name': '🪨 Métal', 'emoji': '⚒️'},
        'oil': {'name': '🛢️ Pétrole', 'emoji': '🛢️'},
        'energy': {'name': '⚡ Énergie', 'emoji': '⚡'},
        'materials': {'name': '🧱 Matériaux', 'emoji': '🧱'}
    },
    'military_units': {
        'soldiers': {'name': '👮 Soldats', 'cost': 100, 'power': 10},
        'vehicles': {'name': '🪖 Véhicules', 'cost': 500, 'power': 50},
        'aircraft': {'name': '✈️ Avions', 'cost': 1000, 'power': 100},
        'missiles': {'name': '🚀 Missiles', 'cost': 2000, 'power': 200},
        'navy': {'name': '⚓ Flotte', 'cost': 1500, 'power': 150}
    }
}
