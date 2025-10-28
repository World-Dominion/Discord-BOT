import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from config import GAME_CONFIG
import asyncio

class CountryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="pays", description="Consulter les informations d'un pays")
    @app_commands.describe(country_name="Nom du pays (optionnel, affiche votre pays par défaut)")
    async def country_info(self, interaction: discord.Interaction, country_name: str = None):
        """Consulter les informations d'un pays"""
        if country_name:
            # Afficher un pays spécifique
            country = await db.get_country_by_name(country_name)
            if not country:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Pays introuvable."),
                    ephemeral=True
                )
                return
            
            # Récupérer le nom du leader
            leader_name = "Inconnu"
            if country.get('leader_id'):
                leader = await db.get_player_by_id(country['leader_id'])
                if leader:
                    leader_name = leader['username']
            
            embed = GameEmbeds.country_info(country, leader_name)
        else:
            # Afficher le pays du joueur
            player = await db.get_player(str(interaction.user.id))
            if not player or not player.get('country_id'):
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                    ephemeral=True
                )
                return
            
            country = await db.get_country(player['country_id'])
            if not country:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Pays introuvable."),
                    ephemeral=True
                )
                return
            
            # Récupérer le nom du leader
            leader_name = "Inconnu"
            if country.get('leader_id'):
                leader = await db.get_player_by_id(country['leader_id'])
                if leader:
                    leader_name = leader['username']
            
            embed = GameEmbeds.country_info(country, leader_name)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rejoindre", description="Rejoindre un pays disponible")
    async def join_country(self, interaction: discord.Interaction):
        """Rejoindre un pays - Affiche un menu déroulant"""
        # Vérifier si le joueur existe déjà et est dans un pays
        player = await db.get_player(str(interaction.user.id))
        if player and player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous appartenez déjà à un pays."),
                ephemeral=True
            )
            return
        
        # Récupérer les pays disponibles (non verrouillés)
        available_countries = await db.get_available_countries()
        if not available_countries:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Aucun pays disponible pour rejoindre."),
                ephemeral=True
            )
            return
        
        # Créer le menu déroulant
        view = CountryJoinView(available_countries, interaction.user)
        
        embed = discord.Embed(
            title="🏳️ Rejoindre un Pays",
            description="Choisissez un pays dans le menu déroulant ci-dessous :",
            color=0x0099ff
        )
        
        # Afficher la liste des pays disponibles
        countries_text = ""
        for i, country in enumerate(available_countries[:10], 1):  # Limiter à 10 pays
            leader_name = "Aucun leader"
            if country.get('leader_id'):
                leader = await db.get_player_by_id(country['leader_id'])
                if leader:
                    leader_name = leader['username']
            
            countries_text += f"{i}. **{country['name']}** - Leader: {leader_name}\n"
        
        embed.add_field(
            name="Pays Disponibles",
            value=countries_text or "Aucun pays disponible",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def create_country(self, interaction: discord.Interaction, player: dict, country_name: str):
        """Créer un nouveau pays"""
        if not country_name:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Veuillez spécifier un nom pour votre pays."),
                ephemeral=True
            )
            return
        
        # Vérifier que le joueur n'est pas déjà dans un pays
        if player and player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous appartenez déjà à un pays."),
                ephemeral=True
            )
            return
        
        # Créer le joueur s'il n'existe pas
        if not player:
            player = await db.create_player(str(interaction.user.id), interaction.user.name)
            if not player:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Erreur lors de la création du joueur."),
                    ephemeral=True
                )
                return
        
        # Créer le pays
        country = await db.create_country(country_name, player['id'])
        if not country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Erreur lors de la création du pays."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🏳️ Nouveau Pays Créé",
            description=f"Le pays '{country_name}' a été créé avec succès !",
            color=0x00ff00
        )
        embed.add_field(
            name="Chef d'État",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        embed.add_field(
            name="Budget Initial",
            value=f"{country.get('resources', {}).get('money', 0):,} 💵",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def join_existing_country(self, interaction: discord.Interaction, player: dict, country_name: str):
        """Rejoindre un pays existant"""
        if not country_name:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Veuillez spécifier le nom du pays à rejoindre."),
                ephemeral=True
            )
            return
        
        # Vérifier que le joueur n'est pas déjà dans un pays
        if player and player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous appartenez déjà à un pays."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays
        country = await db.get_country_by_name(country_name)
        if not country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Créer le joueur s'il n'existe pas
        if not player:
            player = await db.create_player(str(interaction.user.id), interaction.user.name)
            if not player:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Erreur lors de la création du joueur."),
                    ephemeral=True
                )
                return
        
        # Rejoindre le pays
        await db.update_player(str(interaction.user.id), {
            'country_id': country['id'],
            'role': 'citizen'
        })
        
        embed = discord.Embed(
            title="🎉 Pays Rejoint",
            description=f"Vous avez rejoint {country_name} !",
            color=0x00ff00
        )
        embed.add_field(
            name="Votre rang",
            value="👤 Citoyen",
            inline=True
        )
        embed.add_field(
            name="Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="territoire", description="Consulter les territoires contrôlés par votre pays")
    async def territory(self, interaction: discord.Interaction):
        """Consulter les territoires"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays
        country = await db.get_country(player['country_id'])
        if not country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Simuler des territoires
        territories = [
            {"name": "Capitale", "type": "🏛️", "population": country.get('population', 0) // 4},
            {"name": "Région Nord", "type": "🏔️", "population": country.get('population', 0) // 6},
            {"name": "Région Sud", "type": "🌊", "population": country.get('population', 0) // 6},
            {"name": "Région Est", "type": "🌅", "population": country.get('population', 0) // 6},
            {"name": "Région Ouest", "type": "🌅", "population": country.get('population', 0) // 6}
        ]
        
        embed = discord.Embed(
            title=f"🗺️ Territoires de {country['name']}",
            color=0x8B4513
        )
        
        for territory in territories:
            embed.add_field(
                name=f"{territory['type']} {territory['name']}",
                value=f"Population: {territory['population']:,}",
                inline=True
            )
        
        embed.add_field(
            name="📊 Total",
            value=f"Population: {country.get('population', 0):,}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    # Commande /classement SUPPRIMÉE selon demande
    
    @app_commands.command(name="profil", description="Consulter votre profil de joueur")
    async def profile(self, interaction: discord.Interaction):
        """Consulter le profil du joueur"""
        # Récupérer le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'êtes pas enregistré. Utilisez /rejoindre d'abord."),
                ephemeral=True
            )
            return
        
        # Récupérer le nom du pays
        country_name = "Aucun pays"
        if player.get('country_id'):
            country = await db.get_country(player['country_id'])
            if country:
                country_name = country['name']
        
        embed = GameEmbeds.player_info(player, country_name)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="lock-pays", description="Verrouiller/déverrouiller un pays (Chef d'État et Vice-Chef seulement)")
    async def lock_country(self, interaction: discord.Interaction):
        """Verrouiller ou déverrouiller un pays avec menu"""
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."), ephemeral=True)
            return
        
        if player.get('role') not in ['chief', 'vice_chief']:
            await interaction.response.send_message(embed=GameEmbeds.error_embed("Seuls le Chef d'État et le Vice-Chef peuvent verrouiller/déverrouiller le pays."), ephemeral=True)
            return
        
        country = await db.get_country(player['country_id'])
        if not country:
            await interaction.response.send_message(embed=GameEmbeds.error_embed("Pays introuvable."), ephemeral=True)
            return
        
        view = LockCountryView(country, player, interaction.user)
        embed = discord.Embed(title=f"🔒 Verrouillage - {country['name']}", description="Choisissez une action :", color=0xff9900)
        embed.add_field(name="État actuel", value="🔒 Verrouillé" if country.get('is_locked', False) else "🔓 Déverrouillé", inline=True)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CountryJoinView(discord.ui.View):
    def __init__(self, countries: list, user: discord.Member):
        super().__init__(timeout=300)  # 5 minutes
        self.countries = countries
        self.user = user
        
        # Créer les options du menu déroulant
        options = []
        for i, country in enumerate(countries[:25]):  # Discord limite à 25 options
            options.append(discord.SelectOption(
                label=country['name'],
                description=f"Population: {country.get('population', 0):,}",
                value=str(i)
            ))
        
        if options:
            select = CountrySelect(options, countries, user)
            self.add_item(select)

class CountrySelect(discord.ui.Select):
    def __init__(self, options: list, countries: list, user: discord.Member):
        super().__init__(placeholder="Choisissez un pays...", options=options)
        self.countries = countries
        self.user = user
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        country_index = int(self.values[0])
        country = self.countries[country_index]
        
        # Vérifier que le joueur n'est pas déjà dans un pays
        player = await db.get_player(str(interaction.user.id))
        if player and player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous appartenez déjà à un pays."),
                ephemeral=True
            )
            return
        
        # Créer le joueur s'il n'existe pas
        if not player:
            player = await db.create_player(str(interaction.user.id), interaction.user.name)
            if not player:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Erreur lors de la création du joueur."),
                    ephemeral=True
                )
                return
        
        # Rejoindre le pays
        await db.update_player(str(interaction.user.id), {
            'country_id': country['id'],
            'role': 'citizen'
        })
        
        embed = discord.Embed(
            title="🎉 Pays Rejoint",
            description=f"Vous avez rejoint {country['name']} !",
            color=0x00ff00
        )
        embed.add_field(
            name="Votre rang",
            value="👤 Citoyen",
            inline=True
        )
        embed.add_field(
            name="Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LockCountryView(discord.ui.View):
    def __init__(self, country: dict, player: dict, user: discord.Member):
        super().__init__(timeout=300)  # 5 minutes
        self.country = country
        self.player = player
        self.user = user
    
    @discord.ui.button(label="🔒 Verrouiller", style=discord.ButtonStyle.danger)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        if self.country.get('is_locked', False):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Le pays est déjà verrouillé."),
                ephemeral=True
            )
            return
        
        success = await db.lock_country(self.country['id'])
        if success:
            embed = discord.Embed(
                title="🔒 Pays Verrouillé",
                description=f"Le pays {self.country['name']} est maintenant verrouillé.",
                color=0xff9900
            )
            embed.add_field(
                name="Effet",
                value="Les nouveaux joueurs ne peuvent plus rejoindre ce pays.",
                inline=False
            )
        else:
            embed = GameEmbeds.error_embed("Erreur lors du verrouillage du pays.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()
    
    @discord.ui.button(label="🔓 Déverrouiller", style=discord.ButtonStyle.success)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        if not self.country.get('is_locked', False):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Le pays n'est pas verrouillé."),
                ephemeral=True
            )
            return
        
        success = await db.unlock_country(self.country['id'])
        if success:
            embed = discord.Embed(
                title="🔓 Pays Déverrouillé",
                description=f"Le pays {self.country['name']} est maintenant ouvert.",
                color=0x00ff00
            )
            embed.add_field(
                name="Effet",
                value="Les nouveaux joueurs peuvent maintenant rejoindre ce pays.",
                inline=False
            )
        else:
            embed = GameEmbeds.error_embed("Erreur lors du déverrouillage du pays.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

async def setup(bot):
    await bot.add_cog(CountryCog(bot))
