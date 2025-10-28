import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from config import DISCORD_TOKEN, DISCORD_GUILD_ID

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WorldDominionBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Configuration initiale du bot"""
        print("🤖 Initialisation du bot World Dominion...")
        
        # Charger tous les cogs
        cogs = [
            'cogs.economy',
            'cogs.politics', 
            'cogs.military',
            'cogs.diplomacy',
            'cogs.country',
            'cogs.admin',
            'cogs.events',
            'cogs.web_panel'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Cog chargé: {cog}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {cog}: {e}")
        
        # Synchroniser les commandes slash
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"🔄 Commandes synchronisées pour le serveur {DISCORD_GUILD_ID}")
        else:
            await self.tree.sync()
            print("🔄 Commandes synchronisées globalement")
    
    async def on_ready(self):
        """Événement déclenché quand le bot est prêt"""
        print(f"🌍 World Dominion Bot connecté en tant que {self.user}")
        print(f"📊 Connecté à {len(self.guilds)} serveur(s)")
        
        # Définir le statut du bot
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="World Dominion - Stratégie Mondiale"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Gestion des erreurs de commandes"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        print(f"❌ Erreur de commande: {error}")
        
        embed = discord.Embed(
            title="❌ Erreur",
            description="Une erreur est survenue lors de l'exécution de la commande.",
            color=0xff0000
        )
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Gestion des erreurs de commandes slash"""
        print(f"❌ Erreur de commande slash: {error}")
        
        embed = discord.Embed(
            title="❌ Erreur",
            description="Une erreur est survenue lors de l'exécution de la commande.",
            color=0xff0000
        )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

# Fonction principale
async def main():
    """Fonction principale pour démarrer le bot"""
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

# Point d'entrée
if __name__ == "__main__":
    print("🌍 Démarrage de World Dominion Bot...")
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
    print()
    
    asyncio.run(main())
