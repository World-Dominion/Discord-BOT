#!/usr/bin/env python3
"""
Script de démarrage simple pour World Dominion
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def main():
    print("🌍 World Dominion - Démarrage Complet")
    print("=" * 50)
    
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
    
    # Démarrer le panel web en arrière-plan
    print("🌐 Démarrage du panel web...")
    web_process = subprocess.Popen([sys.executable, "web/run.py"])
    
    # Attendre que le panel web démarre
    time.sleep(5)
    
    print("🤖 Démarrage du bot Discord...")
    print("=" * 50)
    
    try:
        # Démarrer le bot Discord
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de World Dominion...")
        print("Arrêt du panel web...")
        web_process.terminate()
        web_process.wait()
        print("✅ Arrêt terminé")

if __name__ == "__main__":
    main()
