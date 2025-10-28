#!/usr/bin/env python3
"""
Point d'entrée unique: démarre le panel web Flask + le bot Discord.
Remplace les anciens start_both.py et main.py.
"""

import os
import sys
import threading
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

def check_env():
    required_vars = [
        'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'SUPABASE_URL', 'SUPABASE_KEY', 'ADMIN_ROLE_IDS'
    ]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print("❌ Variables d'environnement manquantes :")
        for v in missing:
            print(f"   - {v}")
        print("\nVeuillez configurer ces variables dans votre fichier .env")
        sys.exit(1)

def start_web():
    # Démarre le panel web (import absolu pour les analyseurs statiques)
    from web.run import socketio, app  
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)

async def start_bot_async():
    # Démarre le bot Discord (reprend la logique de main.py)
    import discord
    from discord.ext import commands
    from discord import app_commands
    from config import DISCORD_TOKEN, DISCORD_GUILD_ID

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    class WorldDominionBot(commands.Bot):
        def __init__(self):
            super().__init__(command_prefix='!', intents=intents, help_command=None)
        async def setup_hook(self):
            print("🤖 Initialisation du bot World Dominion...")
            cogs = [
                'cogs.economy','cogs.politics','cogs.military','cogs.diplomacy',
                'cogs.country','cogs.admin','cogs.events','cogs.web_panel'
            ]
            for cog in cogs:
                try:
                    await self.load_extension(cog)
                    print(f"✅ Cog chargé: {cog}")
                except Exception as e:
                    print(f"❌ Erreur lors du chargement de {cog}: {e}")
            if DISCORD_GUILD_ID:
                guild = discord.Object(id=DISCORD_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"🔄 Commandes synchronisées pour le serveur {DISCORD_GUILD_ID}")
            else:
                await self.tree.sync()
                print("🔄 Commandes synchronisées globalement")
        async def on_ready(self):
            print(f"🌍 World Dominion Bot connecté en tant que {self.user}")
            print(f"📊 Connecté à {len(self.guilds)} serveur(s)")
            activity = discord.Activity(type=discord.ActivityType.playing, name="World Dominion - Stratégie Mondiale")
            await self.change_presence(activity=activity)

    if not DISCORD_TOKEN:
        print("❌ Token Discord manquant ! Vérifiez votre fichier .env")
        return
    bot = WorldDominionBot()
    try:
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ Token Discord invalide !")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")

def main():
    print("🌍 Démarrage World Dominion (Bot + Panel Web) — point d'entrée unique")
    check_env()
    # Lancer le web dans un thread
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    time.sleep(3)
    # Lancer le bot dans la boucle principale
    asyncio.run(start_bot_async())

if __name__ == '__main__':
    main()
