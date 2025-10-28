#!/usr/bin/env python3
"""
Script pour démarrer le bot Discord et le panel web en même temps
"""

import os
import sys
import subprocess
import threading
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def start_bot():
    """Démarrer le bot Discord"""
    print("🤖 Démarrage du bot Discord...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage du bot: {e}")
    except KeyboardInterrupt:
        print("🛑 Arrêt du bot Discord...")

def start_web_panel():
    """Démarrer le panel web"""
    print("🌐 Démarrage du panel web...")
    try:
        os.chdir("web")
        subprocess.run([sys.executable, "run.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage du panel web: {e}")
    except KeyboardInterrupt:
        print("🛑 Arrêt du panel web...")

def main():
    print("🌍 Démarrage de World Dominion (Bot + Panel Web)...")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    required_vars = [
        'DISCORD_TOKEN',
        'DISCORD_GUILD_ID',
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
    
    print("✅ Configuration vérifiée")
    print()
    
    # Démarrer le panel web dans un thread séparé
    web_thread = threading.Thread(target=start_web_panel, daemon=True)
    web_thread.start()
    
    # Attendre un peu que le panel web démarre
    time.sleep(3)
    
    # Démarrer le bot Discord (thread principal)
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de World Dominion...")
        print("Bot Discord et Panel Web arrêtés.")

if __name__ == "__main__":
    main()
