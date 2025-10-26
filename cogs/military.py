import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from config import GAME_CONFIG
import asyncio
import random

class MilitaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="armée", description="Consulter les forces armées de votre pays")
    async def army(self, interaction: discord.Interaction):
        """Consulter les forces armées"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'army'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour consulter l'armée."),
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
        
        # Simuler des unités militaires basées sur la force militaire
        army_strength = country.get('army_strength', 0)
        resources = country.get('resources', {})
        
        # Calculer les unités disponibles
        soldiers = min(army_strength * 10, resources.get('money', 0) // 100)
        vehicles = min(army_strength * 2, resources.get('metal', 0) // 50)
        aircraft = min(army_strength, resources.get('materials', 0) // 20)
        missiles = min(army_strength // 2, resources.get('materials', 0) // 50)
        navy = min(army_strength // 3, resources.get('materials', 0) // 30)
        
        embed = discord.Embed(
            title=f"🪖 Forces Armées de {country['name']}",
            color=0x8B4513
        )
        
        embed.add_field(
            name="👮 Soldats",
            value=f"{soldiers:,}",
            inline=True
        )
        embed.add_field(
            name="🪖 Véhicules",
            value=f"{vehicles:,}",
            inline=True
        )
        embed.add_field(
            name="✈️ Avions",
            value=f"{aircraft:,}",
            inline=True
        )
        embed.add_field(
            name="🚀 Missiles",
            value=f"{missiles:,}",
            inline=True
        )
        embed.add_field(
            name="⚓ Flotte",
            value=f"{navy:,}",
            inline=True
        )
        embed.add_field(
            name="⚔️ Force Totale",
            value=f"{army_strength}/100",
            inline=True
        )
        
        # Afficher les guerres actives
        active_wars = await db.get_active_wars(country['id'])
        if active_wars:
            war_text = ""
            for war in active_wars:
                if war['attacker_id'] == country['id']:
                    war_text += f"🪖 Attaque en cours\n"
                else:
                    war_text += f"🛡️ Défense en cours\n"
            
            embed.add_field(
                name="⚔️ Conflits Actifs",
                value=war_text or "Aucun",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="attaquer", description="Attaquer un autre pays (Chef d'État seulement)")
    @app_commands.describe(target_country="Pays à attaquer")
    async def attack(self, interaction: discord.Interaction, target_country: str):
        """Attaquer un autre pays"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions (Chef d'État seulement)
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'attack'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Seul le Chef d'État peut déclarer la guerre."),
                ephemeral=True
            )
            return
        
        # Récupérer les pays
        attacker_country = await db.get_country(player['country_id'])
        defender_country = await db.get_country_by_name(target_country)
        
        if not attacker_country or not defender_country:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        if attacker_country['id'] == defender_country['id']:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas vous attaquer vous-même."),
                ephemeral=True
            )
            return
        
        # Vérifier qu'il n'y a pas déjà une guerre active
        active_wars = await db.get_active_wars(attacker_country['id'])
        if any(war['defender_id'] == defender_country['id'] or war['attacker_id'] == defender_country['id'] for war in active_wars):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Une guerre est déjà en cours avec ce pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les ressources pour la guerre
        attacker_resources = attacker_country.get('resources', {})
        war_cost = 1000  # Coût minimum pour déclarer la guerre
        
        if attacker_resources.get('money', 0) < war_cost:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Pas assez d'argent pour déclarer la guerre. Nécessaire: {war_cost:,} 💵"),
                ephemeral=True
            )
            return
        
        # Créer la guerre
        war = await db.create_war(attacker_country['id'], defender_country['id'])
        if not war:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Erreur lors de la création de la guerre."),
                ephemeral=True
            )
            return
        
        # Déduire le coût de la guerre
        attacker_resources['money'] -= war_cost
        await db.update_country(attacker_country['id'], {'resources': attacker_resources})
        
        # Calculer le résultat de la guerre
        war_result = GameHelpers.calculate_war_result(attacker_country, defender_country)
        
        # Appliquer les dégâts
        if war_result['winner'] == 'attacker':
            # Attaquant gagne
            defender_damage = GameHelpers.apply_war_damage(defender_country, war_result['damage'])
            await db.update_country(defender_country['id'], defender_damage)
            
            # Récompense pour l'attaquant
            attacker_resources['money'] += war_result['damage'] * 50
            await db.update_country(attacker_country['id'], {'resources': attacker_resources})
            
            winner_name = attacker_country['name']
            loser_name = defender_country['name']
        else:
            # Défenseur gagne
            attacker_damage = GameHelpers.apply_war_damage(attacker_country, war_result['damage'])
            await db.update_country(attacker_country['id'], attacker_damage)
            
            winner_name = defender_country['name']
            loser_name = attacker_country['name']
        
        # Mettre à jour la guerre avec le résultat
        await db.supabase.table('wars').update({
            'ended_at': 'now()',
            'winner_id': attacker_country['id'] if war_result['winner'] == 'attacker' else defender_country['id'],
            'summary': f"{winner_name} a vaincu {loser_name}"
        }).eq('id', war['id']).execute()
        
        embed = discord.Embed(
            title="⚔️ Guerre Terminée",
            description=f"La guerre entre {attacker_country['name']} et {defender_country['name']} est terminée !",
            color=0xff0000
        )
        embed.add_field(
            name="🏆 Vainqueur",
            value=winner_name,
            inline=True
        )
        embed.add_field(
            name="💥 Dégâts",
            value=f"{war_result['damage']}%",
            inline=True
        )
        embed.add_field(
            name="⚔️ Force Attaquant",
            value=f"{war_result['attacker_power']}",
            inline=True
        )
        embed.add_field(
            name="🛡️ Force Défenseur",
            value=f"{war_result['defender_power']}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="espionner", description="Espionner un autre pays pour obtenir des informations")
    @app_commands.describe(target_country="Pays à espionner")
    async def spy(self, interaction: discord.Interaction, target_country: str):
        """Espionner un autre pays"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'spy'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour espionner."),
                ephemeral=True
            )
            return
        
        # Récupérer les pays
        spy_country = await db.get_country(player['country_id'])
        target_country_data = await db.get_country_by_name(target_country)
        
        if not spy_country or not target_country_data:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        if spy_country['id'] == target_country_data['id']:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas vous espionner vous-même."),
                ephemeral=True
            )
            return
        
        # Coût de l'espionnage
        spy_cost = 500
        spy_resources = spy_country.get('resources', {})
        
        if spy_resources.get('money', 0) < spy_cost:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Pas assez d'argent pour espionner. Nécessaire: {spy_cost:,} 💵"),
                ephemeral=True
            )
            return
        
        # Déduire le coût
        spy_resources['money'] -= spy_cost
        await db.update_country(spy_country['id'], {'resources': spy_resources})
        
        # Calculer le succès de l'espionnage
        spy_success = random.random() < 0.7  # 70% de chance de succès
        
        if spy_success:
            # Révéler des informations partielles
            target_resources = target_country_data.get('resources', {})
            
            embed = discord.Embed(
                title="🕵️ Mission d'Espionnage Réussie",
                description=f"Informations sur {target_country}",
                color=0x00ff00
            )
            
            # Révéler 3 ressources aléatoires
            revealed_resources = random.sample(list(target_resources.keys()), min(3, len(target_resources)))
            
            for resource in revealed_resources:
                amount = target_resources[resource]
                resource_info = GAME_CONFIG['resources'].get(resource, {})
                embed.add_field(
                    name=resource_info.get('name', resource),
                    value=f"{amount:,} {resource_info.get('emoji', '📦')}",
                    inline=True
                )
            
            embed.add_field(
                name="⚔️ Force Militaire",
                value=f"{target_country_data.get('army_strength', 0)}/100",
                inline=True
            )
            embed.add_field(
                name="📊 Économie",
                value=f"{target_country_data.get('economy', 0)}/100",
                inline=True
            )
            embed.add_field(
                name="📈 Stabilité",
                value=f"{target_country_data.get('stability', 0)}%",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="🕵️ Mission d'Espionnage Échouée",
                description="Vos espions ont été découverts !",
                color=0xff0000
            )
            embed.add_field(
                name="Coût",
                value=f"{spy_cost:,} 💵",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="défendre", description="Renforcer les défenses du pays")
    async def defend(self, interaction: discord.Interaction):
        """Renforcer les défenses"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'defend'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour renforcer les défenses."),
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
        
        # Coût de la défense
        defense_cost = 800
        resources = country.get('resources', {})
        
        if resources.get('money', 0) < defense_cost:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Pas assez d'argent pour renforcer les défenses. Nécessaire: {defense_cost:,} 💵"),
                ephemeral=True
            )
            return
        
        # Déduire le coût et améliorer les défenses
        resources['money'] -= defense_cost
        new_army_strength = min(100, country.get('army_strength', 0) + 5)
        new_stability = min(100, country.get('stability', 0) + 3)
        
        await db.update_country(country['id'], {
            'resources': resources,
            'army_strength': new_army_strength,
            'stability': new_stability
        })
        
        embed = discord.Embed(
            title="🛡️ Défenses Renforcées",
            description="Vos défenses ont été améliorées !",
            color=0x00ff00
        )
        embed.add_field(
            name="Coût",
            value=f"{defense_cost:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Force Militaire",
            value=f"+5 ({new_army_strength}/100)",
            inline=True
        )
        embed.add_field(
            name="Stabilité",
            value=f"+3% ({new_stability}%)",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MilitaryCog(bot))
