import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import GameEmbeds
from config import ADMIN_ROLE_IDS
import os

class WebPanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        """Vérifier si l'utilisateur est admin"""
        # Vérifier les rôles admin
        if interaction.guild and ADMIN_ROLE_IDS:
            user_roles = [role.id for role in interaction.user.roles]
            if any(role_id in ADMIN_ROLE_IDS for role_id in user_roles):
                return True
        
        return False
    
    @app_commands.command(name="web-panel", description="Obtenir l'URL du panel d'administration web (Admin seulement)")
    async def web_panel(self, interaction: discord.Interaction):
        """Afficher l'URL du panel d'administration web"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        
        # URL du panel web - Render.com fournit RENDER_EXTERNAL_URL automatiquement
        web_url = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEB_PANEL_URL') or os.getenv('HOST_IP', 'http://localhost:5000')
        
        embed = discord.Embed(
            title="🌍 Panel d'Administration Web",
            description="Accédez au panel d'administration complet de World Dominion",
            color=0x5865f2
        )
        
        embed.add_field(
            name="🔗 URL du Panel",
            value=f"[Cliquez ici pour accéder au panel]({web_url})",
            inline=False
        )
        
        embed.add_field(
            name="🔐 Connexion",
            value="Connectez-vous avec votre compte Discord",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Fonctionnalités",
            value="Gestion complète des pays, joueurs, guerres et événements",
            inline=True
        )
        
        embed.add_field(
            name="📊 Dashboard",
            value="Statistiques en temps réel et graphiques interactifs",
            inline=True
        )
        
        embed.add_field(
            name="🛠️ Outils Avancés",
            value="Modification détaillée, export de données, sauvegarde",
            inline=True
        )
        
        embed.add_field(
            name="⚠️ Important",
            value="Seuls les administrateurs peuvent accéder au panel",
            inline=False
        )
        
        embed.set_footer(text="Panel d'Administration World Dominion")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WebPanelCog(bot))
