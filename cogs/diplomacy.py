import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from config import GAME_CONFIG
import asyncio

class DiplomacyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="alliance", description="Gérer les alliances")
    @app_commands.describe(
        action="Action à effectuer",
        name="Nom de l'alliance (pour créer)",
        target_country="Pays cible (pour inviter)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Créer", value="create"),
        app_commands.Choice(name="Inviter", value="invite"),
        app_commands.Choice(name="Quitter", value="leave"),
        app_commands.Choice(name="Liste", value="list")
    ])
    async def alliance(self, interaction: discord.Interaction, action: str, name: str = None, target_country: str = None):
        """Gérer les alliances"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions (Vice-Chef et plus)
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'commerce'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour gérer les alliances."),
                ephemeral=True
            )
            return
        
        if action == "create":
            await self.create_alliance(interaction, player, name)
        elif action == "invite":
            await self.invite_to_alliance(interaction, player, target_country)
        elif action == "leave":
            await self.leave_alliance(interaction, player)
        elif action == "list":
            await self.list_alliances(interaction, player)
    
    async def create_alliance(self, interaction: discord.Interaction, player: dict, name: str):
        """Créer une nouvelle alliance"""
        if not name:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Veuillez spécifier un nom pour l'alliance."),
                ephemeral=True
            )
            return
        
        # Vérifier que le nom n'existe pas déjà
        # Pour simplifier, on va créer l'alliance directement
        alliance = await db.create_alliance(name, player['country_id'])
        
        if alliance:
            embed = discord.Embed(
                title="🤝 Alliance Créée",
                description=f"L'alliance '{name}' a été créée avec succès !",
                color=0x00ff00
            )
            embed.add_field(
                name="Créateur",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="Membres",
                value="1 pays",
                inline=True
            )
        else:
            embed = GameEmbeds.error_embed("Erreur lors de la création de l'alliance.")
        
        await interaction.response.send_message(embed=embed)
    
    async def invite_to_alliance(self, interaction: discord.Interaction, player: dict, target_country: str):
        """Inviter un pays dans une alliance"""
        if not target_country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Veuillez spécifier un pays à inviter."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays cible
        target_country_data = await db.get_country_by_name(target_country)
        if not target_country_data:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Pour simplifier, on va simuler l'invitation
        embed = discord.Embed(
            title="📨 Invitation Envoyée",
            description=f"Invitation envoyée à {target_country}",
            color=0x0099ff
        )
        embed.add_field(
            name="De",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="À",
            value=target_country,
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def leave_alliance(self, interaction: discord.Interaction, player: dict):
        """Quitter une alliance"""
        # Pour simplifier, on va simuler la sortie d'alliance
        embed = discord.Embed(
            title="👋 Alliance Quittée",
            description="Vous avez quitté votre alliance.",
            color=0xff9900
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def list_alliances(self, interaction: discord.Interaction, player: dict):
        """Lister les alliances"""
        # Pour simplifier, on va afficher une liste fictive
        embed = discord.Embed(
            title="🤝 Alliances Mondiales",
            color=0x9932cc
        )
        
        embed.add_field(
            name="Alliance du Nord",
            value="3 pays membres",
            inline=True
        )
        embed.add_field(
            name="Pacte du Sud",
            value="2 pays membres",
            inline=True
        )
        embed.add_field(
            name="Union Orientale",
            value="4 pays membres",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="négocier", description="Négocier avec un autre pays")
    @app_commands.describe(
        target_country="Pays avec lequel négocier",
        proposal="Votre proposition"
    )
    async def negotiate(self, interaction: discord.Interaction, target_country: str, proposal: str):
        """Négocier avec un autre pays"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'commerce'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour négocier."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays cible
        target_country_data = await db.get_country_by_name(target_country)
        if not target_country_data:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays du joueur
        my_country = await db.get_country(player['country_id'])
        if not my_country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        if my_country['id'] == target_country_data['id']:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas négocier avec votre propre pays."),
                ephemeral=True
            )
            return
        
        # Simuler la négociation
        embed = discord.Embed(
            title="🤝 Négociation",
            description=f"Négociation avec {target_country}",
            color=0x0099ff
        )
        embed.add_field(
            name="Votre proposition",
            value=proposal,
            inline=False
        )
        embed.add_field(
            name="Statut",
            value="En attente de réponse...",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="embargo", description="Mettre un embargo sur un pays")
    @app_commands.describe(target_country="Pays à mettre sous embargo")
    async def embargo(self, interaction: discord.Interaction, target_country: str):
        """Mettre un embargo sur un pays"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions (Chef d'État seulement)
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'tax'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Seul le Chef d'État peut mettre un embargo."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays cible
        target_country_data = await db.get_country_by_name(target_country)
        if not target_country_data:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays du joueur
        my_country = await db.get_country(player['country_id'])
        if not my_country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        if my_country['id'] == target_country_data['id']:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas mettre un embargo sur votre propre pays."),
                ephemeral=True
            )
            return
        
        # Simuler l'embargo
        embed = discord.Embed(
            title="🚫 Embargo Déclaré",
            description=f"Embargo mis sur {target_country}",
            color=0xff0000
        )
        embed.add_field(
            name="Déclaré par",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="Cible",
            value=target_country,
            inline=True
        )
        embed.add_field(
            name="Effet",
            value="Commerce bloqué",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DiplomacyCog(bot))
