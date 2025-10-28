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
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

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
    from web.app import socketio, app
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
        async def on_command_error(self, ctx, error):
            from discord.ext import commands as _commands
            if isinstance(error, _commands.CommandNotFound):
                return
            print(f"❌ Erreur de commande: {error}")
            try:
                import discord as _discord
                embed = _discord.Embed(
                    title="❌ Erreur",
                    description="Une erreur est survenue lors de l'exécution de la commande.",
                    color=0xff0000
                )
                await ctx.send(embed=embed, ephemeral=True)
            except Exception:
                pass
        async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
            print(f"❌ Erreur de commande slash: {error}")
            try:
                import discord as _discord
                embed = _discord.Embed(
                    title="❌ Erreur",
                    description="Une erreur est survenue lors de l'exécution de la commande.",
                    color=0xff0000
                )
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception:
                pass

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
    print("Demarrage World Dominion (Bot + Panel Web) - point d'entree unique")
    print("📋 Commandes disponibles:")
    print("   /rejoindre - Rejoindre un pays (menu déroulant)")
    print("   /pays - Consulter les informations d'un pays")
    print("   /profil - Consulter votre profil")
    print("   /classement - Afficher le classement mondial")
    print("   /lock-pays - Verrouiller/déverrouiller un pays (Chef/Vice-Chef)")
    print("   /produire - Produire des ressources")
    print("   /commerce - Échanger avec d'autres pays")
    print("   /taxe - Fixer les impôts (Chef d'État)")
    print("   /banque - Consulter le budget national")
    print("   /travail - Travailler pour gagner de l'argent")
    print("   /promouvoir - Promouvoir un joueur (Chef d'État)")
    print("   /élection - Organiser une élection")
    print("   /armée - Consulter les forces armées")
    print("   /attaquer - Attaquer un pays (Chef d'État)")
    print("   /espionner - Espionner un pays")
    print("   /défendre - Renforcer les défenses")
    print("   /alliance - Gérer les alliances")
    print("   /négocier - Négocier avec un pays")
    print("   /embargo - Mettre un embargo (Chef d'État)")
    print("   /territoire - Consulter les territoires")
    print("   /create - Créer un pays (Admin)")
    print("   /own - Assigner un pays à un joueur (Admin)")
    print("   /admin-list - Lister tous les pays (Admin)")
    print("   /delete - Supprimer des éléments d'un pays (Admin)")
    print("   /events - Consulter les événements récents")
    print("   /trigger-event - Déclencher un événement (Admin)")
    print("   /web-panel - Obtenir l'URL du panel web (Admin)")
    check_env()
    # Lancer le web dans un thread
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    time.sleep(3)
    # Lancer le bot dans la boucle principale
    asyncio.run(start_bot_async())

if __name__ == '__main__':
    main()
