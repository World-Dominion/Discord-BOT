import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from config import GAME_CONFIG
import asyncio

class PoliticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="promouvoir", description="Promouvoir un joueur dans la hiérarchie (Chef d'État seulement)")
    @app_commands.describe(
        user="Utilisateur à promouvoir",
        new_role="Nouveau rôle"
    )
    @app_commands.choices(new_role=[
        app_commands.Choice(name="⚖️ Vice-Chef", value="vice_chief"),
        app_commands.Choice(name="💰 Ministre de l'Économie", value="economy_minister"),
        app_commands.Choice(name="🪖 Ministre de la Défense", value="defense_minister"),
        app_commands.Choice(name="🏙️ Gouverneur", value="governor"),
        app_commands.Choice(name="⚙️ Officier", value="officer"),
        app_commands.Choice(name="👤 Citoyen", value="citizen")
    ])
    async def promote(self, interaction: discord.Interaction, user: discord.Member, new_role: str):
        """Promouvoir un joueur"""
        # Vérifier le joueur qui fait la promotion
        promoter = await db.get_player(str(interaction.user.id))
        if not promoter or not promoter.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions (Chef d'État seulement)
        if not GameHelpers.can_player_use_command(promoter.get('role', 'recruit'), 'promote'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Seul le Chef d'État peut promouvoir des joueurs."),
                ephemeral=True
            )
            return
        
        # Vérifier que le joueur à promouvoir existe
        target_player = await db.get_player(str(user.id))
        if not target_player:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce joueur n'est pas enregistré."),
                ephemeral=True
            )
            return
        
        # Vérifier qu'ils sont dans le même pays
        if target_player.get('country_id') != promoter.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce joueur n'est pas dans votre pays."),
                ephemeral=True
            )
            return
        
        # Vérifier que le nouveau rôle est inférieur au rôle du promoteur
        promoter_level = GAME_CONFIG['roles'].get(promoter.get('role', 'recruit'), {}).get('level', 8)
        new_role_level = GAME_CONFIG['roles'].get(new_role, {}).get('level', 8)
        
        if new_role_level <= promoter_level:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas promouvoir quelqu'un à un rang égal ou supérieur au vôtre."),
                ephemeral=True
            )
            return
        
        # Effectuer la promotion
        await db.update_player(str(user.id), {'role': new_role})
        
        new_role_name = GAME_CONFIG['roles'].get(new_role, {}).get('name', new_role)
        
        embed = discord.Embed(
            title="🎖️ Promotion",
            description=f"{user.mention} a été promu !",
            color=0x00ff00
        )
        embed.add_field(
            name="Nouveau rang",
            value=new_role_name,
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="élection", description="Organiser une élection pour choisir un nouveau Chef d'État")
    @app_commands.describe(candidate="Candidat à l'élection")
    async def election(self, interaction: discord.Interaction, candidate: discord.Member):
        """Organiser une élection"""
        # Vérifier le joueur qui organise l'élection
        organizer = await db.get_player(str(interaction.user.id))
        if not organizer or not organizer.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions (Vice-Chef et plus)
        if not GameHelpers.can_player_use_command(organizer.get('role', 'recruit'), 'election'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour organiser une élection."),
                ephemeral=True
            )
            return
        
        # Vérifier que le candidat existe et est dans le même pays
        candidate_player = await db.get_player(str(candidate.id))
        if not candidate_player or candidate_player.get('country_id') != organizer.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce joueur n'est pas dans votre pays."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays
        country = await db.get_country(organizer['country_id'])
        if not country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Créer l'embed d'élection
        embed = discord.Embed(
            title="🗳️ Élection Présidentielle",
            description=f"Élection pour choisir le nouveau Chef d'État de {country['name']}",
            color=0x0099ff
        )
        embed.add_field(
            name="Candidat",
            value=candidate.mention,
            inline=True
        )
        embed.add_field(
            name="Organisateur",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="Durée",
            value="5 minutes",
            inline=True
        )
        
        # Créer les boutons de vote
        view = ElectionView(candidate.id, organizer['country_id'], country['name'])
        
        message = await interaction.response.send_message(embed=embed, view=view)
        
        # Programmer la fin de l'élection
        await asyncio.sleep(300)  # 5 minutes
        
        # Récupérer les résultats
        votes = view.get_votes()
        if votes['yes'] > votes['no']:
            # Le candidat gagne
<<<<<<< HEAD
            # Utiliser les IDs internes joueurs
            new_leader = await db.get_player(str(candidate.id))
            current_leader = await db.get_player_by_id(country['leader_id']) if country.get('leader_id') else None
            if new_leader:
                await db.update_player(str(candidate.id), {'role': 'chief'})
                if current_leader:
                    await db.update_player(current_leader['discord_id'], {'role': 'vice_chief'})
                await db.update_country(country['id'], {'leader_id': new_leader['id']})
=======
            await db.update_player(str(candidate.id), {'role': 'chief'})
            await db.update_player(str(country['leader_id']), {'role': 'vice_chief'})
            await db.update_country(country['id'], {'leader_id': candidate.id})
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
            
            embed = discord.Embed(
                title="🎉 Élection Terminée",
                description=f"{candidate.mention} est le nouveau Chef d'État de {country['name']} !",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Élection Terminée",
                description=f"{candidate.mention} n'a pas été élu Chef d'État.",
                color=0xff0000
            )
        
        embed.add_field(
            name="Votes pour",
            value=f"{votes['yes']} ✅",
            inline=True
        )
        embed.add_field(
            name="Votes contre",
            value=f"{votes['no']} ❌",
            inline=True
        )
        
        # Mettre à jour le message
        try:
            await interaction.edit_original_response(embed=embed, view=None)
        except:
            pass
    
    @app_commands.command(name="vote", description="Voter lors d'une élection")
    @app_commands.describe(choice="Votre choix")
    @app_commands.choices(choice=[
        app_commands.Choice(name="✅ Pour", value="yes"),
        app_commands.Choice(name="❌ Contre", value="no")
    ])
    async def vote(self, interaction: discord.Interaction, choice: str):
        """Voter lors d'une élection"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'vote'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas voter."),
                ephemeral=True
            )
            return
        
        # Pour l'instant, on simule un vote simple
        # Dans une vraie implémentation, il faudrait gérer les élections actives
        
        await interaction.response.send_message(
            embed=GameEmbeds.success_embed("Votre vote a été enregistré !"),
            ephemeral=True
        )

class ElectionView(discord.ui.View):
    def __init__(self, candidate_id: int, country_id: str, country_name: str):
        super().__init__(timeout=300)  # 5 minutes
        self.candidate_id = candidate_id
        self.country_id = country_id
        self.country_name = country_name
        self.votes = {'yes': 0, 'no': 0}
        self.voters = set()
    
    @discord.ui.button(label="✅ Pour", style=discord.ButtonStyle.green)
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, 'yes')
    
    @discord.ui.button(label="❌ Contre", style=discord.ButtonStyle.red)
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, 'no')
    
    async def handle_vote(self, interaction: discord.Interaction, choice: str):
        # Vérifier que le joueur peut voter
        player = await db.get_player(str(interaction.user.id))
        if not player or player.get('country_id') != self.country_id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas voter dans cette élection."),
                ephemeral=True
            )
            return
        
        # Vérifier qu'il n'a pas déjà voté
        if interaction.user.id in self.voters:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous avez déjà voté."),
                ephemeral=True
            )
            return
        
        # Enregistrer le vote
        self.votes[choice] += 1
        self.voters.add(interaction.user.id)
        
        await interaction.response.send_message(
            embed=GameEmbeds.success_embed("Votre vote a été enregistré !"),
            ephemeral=True
        )
    
    def get_votes(self):
        return self.votes

async def setup(bot):
    await bot.add_cog(PoliticsCog(bot))
