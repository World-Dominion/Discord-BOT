import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from config import ADMIN_ROLE_IDS
from utils.helpers import GameHelpers
import asyncio

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    async def is_admin(self, interaction: discord.Interaction) -> bool:
        # Vérifier les rôles admin (Discord roles ou rôle jeu Fondateur/Haut Conseil)
        if interaction.guild and ADMIN_ROLE_IDS:
            user_roles = [role.id for role in interaction.user.roles]
            if any(role_id in ADMIN_ROLE_IDS for role_id in user_roles):
                return True
        # Vérifier rôle jeu (Fondateur ou Haut Conseil autorisé à agir comme admin)
        try:
            player = await db.get_player(str(interaction.user.id))
            if player and player.get('role') in ['founder', 'high_council']:
                return True
        except:
            pass
        return False

    @app_commands.command(name="give", description="Donner une ressource ou de l'argent (Admin)")
    @app_commands.describe(
        target_type="Type de cible: player/country/all_players/all_countries",
        target_id="ID interne de la cible (players.id ou countries.id)",
        resource="balance pour joueur, ou money/food/metal/oil/energy/materials pour pays",
        amount="Montant à donner"
    )
    async def give(self, interaction: discord.Interaction, target_type: str, resource: str, amount: int, target_id: str = None):
        """Commande admin /give"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        if amount == 0:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Le montant doit être non nul."),
                ephemeral=True
            )
            return
        try:
            # Cas joueur spécifique: target_id peut être vide => on prend l'appelant
            if target_type == 'player' and not target_id:
                player = await db.get_player(str(interaction.user.id))
                if not player:
                    await interaction.response.send_message(embed=GameEmbeds.error_embed("Joueur introuvable."), ephemeral=True)
                    return
                target_id = player['id']
            # Appliquer dons via DB manager
            if target_type == 'player':
                # balance seulement
                if resource not in ['balance', 'money']:
                    await interaction.response.send_message(embed=GameEmbeds.error_embed("Ressource invalide pour un joueur."), ephemeral=True)
                    return
                target_player = await db.get_player_by_id(target_id)
                if not target_player:
                    await interaction.response.send_message(embed=GameEmbeds.error_embed("Joueur introuvable."), ephemeral=True)
                    return
                new_balance = (target_player.get('balance', 0) or 0) + amount
                await db.update_player(target_player['discord_id'], {'balance': new_balance})
            elif target_type in ['country', 'all_countries']:
                if resource not in ['money','food','metal','oil','energy','materials']:
                    await interaction.response.send_message(embed=GameEmbeds.error_embed("Ressource invalide pour un pays."), ephemeral=True)
                    return
                if target_type == 'country':
                    country = await db.get_country(target_id)
                    if not country:
                        await interaction.response.send_message(embed=GameEmbeds.error_embed("Pays introuvable."), ephemeral=True)
                        return
                    res = country.get('resources', {}).copy()
                    res[resource] = (res.get(resource, 0) or 0) + amount
                    await db.update_country(country['id'], {'resources': res})
                else:
                    countries = await db.get_all_countries()
                    for c in countries:
                        res = c.get('resources', {}).copy()
                        res[resource] = (res.get(resource, 0) or 0) + amount
                        await db.update_country(c['id'], {'resources': res})
            elif target_type == 'all_players':
                if resource not in ['balance','money']:
                    await interaction.response.send_message(embed=GameEmbeds.error_embed("Ressource invalide pour joueurs."), ephemeral=True)
                    return
                players_result = db.supabase.table('players').select('discord_id,balance').execute()
                for p in (players_result.data or []):
                    new_balance = (p.get('balance', 0) or 0) + amount
                    await db.update_player(p['discord_id'], {'balance': new_balance})
            else:
                await interaction.response.send_message(embed=GameEmbeds.error_embed("target_type invalide."), ephemeral=True)
                return
            embed = discord.Embed(title="🎁 Don effectué", description=f"{amount} {resource} → {target_type}", color=0x00ff00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=GameEmbeds.error_embed("Erreur lors du don."), ephemeral=True)

    @app_commands.command(name="create", description="Créer un nouveau pays (Admin seulement)")
    @app_commands.describe(country_name="Nom du pays à créer")
    async def create_country(self, interaction: discord.Interaction, country_name: str):
        """Créer un nouveau pays (Admin seulement)"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        
        if not country_name or len(country_name.strip()) < 2:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Le nom du pays doit contenir au moins 2 caractères."),
                ephemeral=True
            )
            return
        
        # Vérifier que le pays n'existe pas déjà
        existing_country = await db.get_country_by_name(country_name.strip())
        if existing_country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"❌ Le pays '{country_name}' existe déjà."),
                ephemeral=True
            )
            return
        
        # Créer le pays sans leader (sera assigné avec /own)
        try:
            result = db.supabase.table('countries').insert({
                'name': country_name.strip(),
                'leader_id': None,
                'population': 1000000,
                'economy': 50,
                'army_strength': 20,
                'resources': {
                    'money': 5000,
                    'food': 200,
                    'metal': 50,
                    'oil': 80,
                    'energy': 100,
                    'materials': 30
                },
                'stability': 80,
                'is_locked': False
            }).execute()
            
            if result.data:
                country = result.data[0]
                embed = discord.Embed(
                    title="🏳️ Pays Créé",
                    description=f"Le pays '{country_name}' a été créé avec succès !",
                    color=0x00ff00
                )
                embed.add_field(
                    name="ID du pays",
                    value=f"`{country['id']}`",
                    inline=True
                )
                embed.add_field(
                    name="Statut",
                    value="🆕 En attente d'un leader",
                    inline=True
                )
                embed.add_field(
                    name="Prochaine étape",
                    value="Utilisez `/own` pour assigner un leader",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("❌ Erreur lors de la création du pays."),
                    ephemeral=True
                )
        except Exception as e:
            print(f"Erreur création pays admin: {e}")
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Erreur lors de la création du pays."),
                ephemeral=True
            )
    
    @app_commands.command(name="own", description="Assigner un pays à un joueur (Admin seulement)")
    @app_commands.describe(
        country_name="Nom du pays à assigner",
        user="Utilisateur à qui assigner le pays"
    )
    async def assign_country(self, interaction: discord.Interaction, country_name: str, user: discord.Member):
        """Assigner un pays à un joueur (Admin seulement)"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays
        country = await db.get_country_by_name(country_name)
        if not country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"❌ Le pays '{country_name}' n'existe pas."),
                ephemeral=True
            )
            return
        
        # Vérifier si le pays a déjà un leader
        if country.get('leader_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"❌ Le pays '{country_name}' a déjà un leader."),
                ephemeral=True
            )
            return
        
        # Vérifier si l'utilisateur est déjà dans un pays
        existing_player = await db.get_player(str(user.id))
        if existing_player and existing_player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"❌ {user.mention} appartient déjà à un pays."),
                ephemeral=True
            )
            return
        
        # Créer ou mettre à jour le joueur
        if not existing_player:
            player = await db.create_player(str(user.id), user.name)
            if not player:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("❌ Erreur lors de la création du joueur."),
                    ephemeral=True
                )
                return
        else:
            player = existing_player
        
        # Assigner le pays au joueur
        await db.update_player(str(user.id), {
            'country_id': country['id'],
            'role': 'chief'
        })
        
        # Mettre à jour le pays avec le nouveau leader
        await db.update_country(country['id'], {
            'leader_id': player['id']
        })
        
        embed = discord.Embed(
            title="👑 Pays Assigné",
            description=f"Le pays '{country_name}' a été assigné avec succès !",
            color=0x00ff00
        )
        embed.add_field(
            name="Nouveau Chef d'État",
            value=user.mention,
            inline=True
        )
        embed.add_field(
            name="Pays",
            value=country_name,
            inline=True
        )
        embed.add_field(
            name="Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="admin-list", description="Lister tous les pays et leurs leaders (Admin seulement)")
    async def admin_list_countries(self, interaction: discord.Interaction):
        """Lister tous les pays (Admin seulement)"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        
        countries = await db.get_all_countries()
        if not countries:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Aucun pays trouvé."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🏳️ Liste des Pays (Admin)",
            color=0x0099ff
        )
        
        for country in countries:
            leader_name = "Aucun leader"
            if country.get('leader_id'):
                leader = await db.get_player_by_id(country['leader_id'])
                if leader:
                    leader_name = leader['username']
            
            status = "🔒 Verrouillé" if country.get('is_locked', False) else "🔓 Ouvert"
            
            embed.add_field(
                name=f"{country['name']} {status}",
                value=f"Leader: {leader_name}\nPopulation: {country.get('population', 0):,}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="delete", description="Supprimer des éléments d'un pays (Admin seulement)")
    async def delete_country_data(self, interaction: discord.Interaction):
        """Supprimer des éléments d'un pays - Étape 1: Sélection du pays"""
        if not self.is_admin(interaction):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Vous n'avez pas les permissions d'administrateur."),
                ephemeral=True
            )
            return
        
        # Récupérer tous les pays
        countries = await db.get_all_countries()
        if not countries:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("❌ Aucun pays trouvé."),
                ephemeral=True
            )
            return
        
        # Créer le menu de sélection des pays
        view = CountryDeleteView(countries, interaction.user)
        
        embed = discord.Embed(
            title="🗑️ Suppression d'Éléments",
            description="Sélectionnez le pays dont vous voulez supprimer des éléments :",
            color=0xff0000
        )
        
        # Afficher la liste des pays
        countries_text = ""
        for i, country in enumerate(countries[:25], 1):  # Limiter à 25 pays
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

class CountryDeleteView(discord.ui.View):
    def __init__(self, countries: list, user: discord.Member):
        super().__init__(timeout=300)  # 5 minutes
        self.countries = countries
        self.user = user
        
        # Créer les options du menu déroulant
        options = []
        for i, country in enumerate(countries[:25]):  # Discord limite à 25 options
            options.append(discord.SelectOption(
                label=country['name'],
                description=f"ID: {country['id'][:8]}...",
                value=str(i)
            ))
        
        if options:
            select = CountryDeleteSelect(options, countries, user)
            self.add_item(select)

class CountryDeleteSelect(discord.ui.Select):
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
        
        # Créer le menu de suppression des éléments
        view = DeleteElementsView(country, interaction.user)
        
        # Récupérer les informations détaillées du pays
        leader_name = "Aucun leader"
        if country.get('leader_id'):
            leader = await db.get_player_by_id(country['leader_id'])
            if leader:
                leader_name = leader['username']
        
        # Récupérer les guerres actives
        active_wars = await db.get_active_wars(country['id'])
        
        # Récupérer les joueurs du pays
        players_result = db.supabase.table('players').select('username, role').eq('country_id', country['id']).execute()
        players = players_result.data if players_result.data else []
        
        embed = discord.Embed(
            title=f"🗑️ Suppression - {country['name']}",
            description="Sélectionnez les éléments à supprimer :",
            color=0xff0000
        )
        
        # Informations du pays
        resources = country.get('resources', {})
        embed.add_field(
            name="💰 Ressources",
            value=f"Argent: {resources.get('money', 0):,} 💵\n"
                  f"Nourriture: {resources.get('food', 0):,} 🍞\n"
                  f"Métal: {resources.get('metal', 0):,} ⚒️\n"
                  f"Pétrole: {resources.get('oil', 0):,} 🛢️\n"
                  f"Énergie: {resources.get('energy', 0):,} ⚡\n"
                  f"Matériaux: {resources.get('materials', 0):,} 🧱",
            inline=True
        )
        
        embed.add_field(
            name="📊 Statistiques",
            value=f"Population: {country.get('population', 0):,}\n"
                  f"Économie: {country.get('economy', 0)}/100\n"
                  f"Force Militaire: {country.get('army_strength', 0)}/100\n"
                  f"Stabilité: {country.get('stability', 0)}%\n"
                  f"Leader: {leader_name}\n"
                  f"Verrouillé: {'Oui' if country.get('is_locked', False) else 'Non'}",
            inline=True
        )
        
        # Guerres actives
        wars_text = "Aucune guerre active"
        if active_wars:
            wars_text = f"{len(active_wars)} guerre(s) active(s)"
        
        # Joueurs
        players_text = f"{len(players)} joueur(s)"
        if players:
            players_text += "\n" + "\n".join([f"- {p['username']} ({p['role']})" for p in players[:5]])
            if len(players) > 5:
                players_text += f"\n... et {len(players) - 5} autres"
        
        embed.add_field(
            name="⚔️ Guerres & 👥 Joueurs",
            value=f"Guerres: {wars_text}\n\nJoueurs: {players_text}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class DeleteElementsView(discord.ui.View):
    def __init__(self, country: dict, user: discord.Member):
        super().__init__(timeout=300)  # 5 minutes
        self.country = country
        self.user = user
        
        # Créer les options de suppression
        options = [
            discord.SelectOption(
                label="💰 Ressources",
                description="Supprimer toutes les ressources du pays",
                value="resources",
                emoji="💰"
            ),
            discord.SelectOption(
                label="👥 Joueurs",
                description="Expulser tous les joueurs du pays",
                value="players",
                emoji="👥"
            ),
            discord.SelectOption(
                label="⚔️ Guerres",
                description="Terminer toutes les guerres actives",
                value="wars",
                emoji="⚔️"
            ),
            discord.SelectOption(
                label="📊 Statistiques",
                description="Réinitialiser économie, armée, stabilité",
                value="stats",
                emoji="📊"
            ),
            discord.SelectOption(
                label="🏳️ Pays Entier",
                description="SUPPRIMER COMPLÈTEMENT LE PAYS",
                value="country",
                emoji="🏳️"
            )
        ]
        
        select = DeleteElementsSelect(options, country, user)
        self.add_item(select)

class DeleteElementsSelect(discord.ui.Select):
    def __init__(self, options: list, country: dict, user: discord.Member):
        super().__init__(placeholder="Choisissez ce que vous voulez supprimer...", options=options)
        self.country = country
        self.user = user
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        action = self.values[0]
        
        if action == "resources":
            await self.delete_resources(interaction)
        elif action == "players":
            await self.delete_players(interaction)
        elif action == "wars":
            await self.delete_wars(interaction)
        elif action == "stats":
            await self.delete_stats(interaction)
        elif action == "country":
            await self.delete_country(interaction)
    
    async def delete_resources(self, interaction: discord.Interaction):
        """Supprimer toutes les ressources"""
        await db.update_country(self.country['id'], {
            'resources': {
                'money': 0,
                'food': 0,
                'metal': 0,
                'oil': 0,
                'energy': 0,
                'materials': 0
            }
        })
        
        embed = discord.Embed(
            title="💰 Ressources Supprimées",
            description=f"Toutes les ressources de {self.country['name']} ont été supprimées.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def delete_players(self, interaction: discord.Interaction):
        """Expulser tous les joueurs"""
        # Mettre à jour tous les joueurs du pays
        db.supabase.table('players').update({
            'country_id': None,
            'role': 'recruit'
        }).eq('country_id', self.country['id']).execute()
        
        # Supprimer le leader du pays
        await db.update_country(self.country['id'], {
            'leader_id': None
        })
        
        embed = discord.Embed(
            title="👥 Joueurs Expulsés",
            description=f"Tous les joueurs de {self.country['name']} ont été expulsés.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def delete_wars(self, interaction: discord.Interaction):
        """Terminer toutes les guerres"""
        # Terminer toutes les guerres actives
        db.supabase.table('wars').update({
            'ended_at': 'now()',
            'summary': 'Terminée par un administrateur'
        }).or_(f'attacker_id.eq.{self.country["id"]},defender_id.eq.{self.country["id"]}').is_('ended_at', 'null').execute()
        
        embed = discord.Embed(
            title="⚔️ Guerres Terminées",
            description=f"Toutes les guerres de {self.country['name']} ont été terminées.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def delete_stats(self, interaction: discord.Interaction):
        """Réinitialiser les statistiques"""
        await db.update_country(self.country['id'], {
            'economy': 0,
            'army_strength': 0,
            'stability': 0
        })
        
        embed = discord.Embed(
            title="📊 Statistiques Réinitialisées",
            description=f"Les statistiques de {self.country['name']} ont été réinitialisées.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def delete_country(self, interaction: discord.Interaction):
        """Supprimer complètement le pays"""
        # Créer un embed de confirmation
        embed = discord.Embed(
            title="⚠️ CONFIRMATION REQUISE",
            description=f"Êtes-vous sûr de vouloir **SUPPRIMER DÉFINITIVEMENT** le pays {self.country['name']} ?",
            color=0xff0000
        )
        embed.add_field(
            name="⚠️ ATTENTION",
            value="Cette action est **IRRÉVERSIBLE** !\n"
                  "Tous les joueurs seront expulsés.\n"
                  "Toutes les données seront perdues.",
            inline=False
        )
        
        # Créer les boutons de confirmation
        view = ConfirmDeleteView(self.country, interaction.user)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, country: dict, user: discord.Member):
        super().__init__(timeout=60)  # 1 minute pour confirmer
        self.country = country
        self.user = user
    
    @discord.ui.button(label="✅ CONFIRMER", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        # Expulser tous les joueurs
        db.supabase.table('players').update({
            'country_id': None,
            'role': 'recruit'
        }).eq('country_id', self.country['id']).execute()
        
        # Supprimer le pays
        db.supabase.table('countries').delete().eq('id', self.country['id']).execute()
        
        embed = discord.Embed(
            title="🏳️ Pays Supprimé",
            description=f"Le pays {self.country['name']} a été **DÉFINITIVEMENT SUPPRIMÉ**.",
            color=0xff0000
        )
        embed.add_field(
            name="Effets",
            value="✅ Tous les joueurs ont été expulsés\n"
                  "✅ Toutes les données ont été supprimées\n"
                  "✅ Le pays n'existe plus",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ ANNULER", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Ce menu ne vous appartient pas."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="❌ Suppression Annulée",
            description="La suppression du pays a été annulée.",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
