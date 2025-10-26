#!/usr/bin/env python3
"""
Script de démarrage pour le panel d'administration web de World Dominion
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Vérifier les variables requises
required_vars = [
    'DISCORD_TOKEN',
    'DISCORD_CLIENT_ID', 
    'DISCORD_CLIENT_SECRET',
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'ADMIN_ROLE_IDS'
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print("❌ Variables d'environnement manquantes :")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nVeuillez configurer ces variables dans votre fichier .env")
    sys.exit(1)

# Vérifier que le port n'est pas déjà utilisé
import socket
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if is_port_in_use(5000):
    print("❌ Le port 5000 est déjà utilisé.")
    print("Veuillez arrêter l'autre application ou modifier le port dans app.py")
    sys.exit(1)

print("🌍 Démarrage du Panel d'Administration World Dominion...")
print("📋 Configuration :")
print(f"   - Discord Client ID: {os.getenv('DISCORD_CLIENT_ID')}")
print(f"   - Supabase URL: {os.getenv('SUPABASE_URL')}")
print(f"   - Admin Roles: {os.getenv('ADMIN_ROLE_IDS')}")
print()
print("🚀 Le panel sera accessible sur : http://localhost:5000")
print("🔐 Seuls les administrateurs Discord peuvent se connecter")
print()
print("⚠️  Pour arrêter le serveur, utilisez Ctrl+C")
print()

# Importer et démarrer l'application

if __name__ == '__main__':
    try:
        # Démarrer le serveur web directement
        from app import app, socketio
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
    except Exception as e:
        print(f"\n❌ Erreur lors du démarrage : {e}")
        sys.exit(1)
