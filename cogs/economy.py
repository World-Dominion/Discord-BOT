import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from config import GAME_CONFIG
import asyncio

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="produire", description="Produire une ressource en consommant de l'énergie")
    @app_commands.describe(
        resource="Type de ressource à produire",
        amount="Quantité à produire"
    )
    @app_commands.choices(resource=[
        app_commands.Choice(name="💵 Argent", value="money"),
        app_commands.Choice(name="🌾 Nourriture", value="food"),
        app_commands.Choice(name="🪨 Métal", value="metal"),
        app_commands.Choice(name="🛢️ Pétrole", value="oil"),
        app_commands.Choice(name="⚡ Énergie", value="energy"),
        app_commands.Choice(name="🧱 Matériaux", value="materials")
    ])
    async def produce(self, interaction: discord.Interaction, resource: str, amount: int):
        """Produire une ressource"""
<<<<<<< HEAD
        rules = GAME_CONFIG.get('economy_rules', {})
=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        if amount <= 0 or amount > 1000:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("La quantité doit être entre 1 et 1000"),
                ephemeral=True
            )
            return
        
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'êtes pas enregistré. Utilisez /rejoindre d'abord."),
                ephemeral=True
            )
            return
        
        if not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'produce'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour produire des ressources."),
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
        
<<<<<<< HEAD
        # Caps journaliers
        daily = await db.get_daily_totals(player_id=player.get('id')) if player else {'produce': {}}
        daily_res = daily.get('produce', {}).get(resource, 0)
        cap = rules.get('produce_daily_cap_per_resource', 2000)
        if daily_res + amount > cap:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Cap quotidien atteint pour {resource}. Restant: {max(0, cap - daily_res)}"),
                ephemeral=True
            )
            return

=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        # Calculer le coût
        energy_cost = GameHelpers.calculate_production_cost(resource, amount)
        current_energy = country.get('resources', {}).get('energy', 0)
        
        if current_energy < energy_cost:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Pas assez d'énergie ! Nécessaire: {energy_cost}, Disponible: {current_energy}"),
                ephemeral=True
            )
            return
        
        # Effectuer la production
        resources = country.get('resources', {}).copy()
        resources['energy'] -= energy_cost
        resources[resource] = resources.get(resource, 0) + amount
        
        # Mettre à jour le pays
        await db.update_country(country['id'], {'resources': resources})
<<<<<<< HEAD
        # Log transaction
        if GAME_CONFIG.get('economy_rules', {}).get('transaction_log_enabled'):
            await db.log_transaction({
                'type': 'produce',
                'player_id': player.get('id'),
                'country_id': country['id'],
                'resource': resource,
                'amount': amount,
                'cost_energy': energy_cost
            })
=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        
        await interaction.response.send_message(
            embed=GameEmbeds.production_result(resource, amount, energy_cost)
        )
    
    @app_commands.command(name="commerce", description="Échanger des ressources avec un autre pays")
    @app_commands.describe(
        target_country="Pays avec lequel échanger",
        give_resource="Ressource à donner",
        give_amount="Quantité à donner",
        receive_resource="Ressource à recevoir",
        receive_amount="Quantité à recevoir"
    )
    @app_commands.choices(give_resource=[
        app_commands.Choice(name="💵 Argent", value="money"),
        app_commands.Choice(name="🌾 Nourriture", value="food"),
        app_commands.Choice(name="🪨 Métal", value="metal"),
        app_commands.Choice(name="🛢️ Pétrole", value="oil"),
        app_commands.Choice(name="⚡ Énergie", value="energy"),
        app_commands.Choice(name="🧱 Matériaux", value="materials")
    ])
    @app_commands.choices(receive_resource=[
        app_commands.Choice(name="💵 Argent", value="money"),
        app_commands.Choice(name="🌾 Nourriture", value="food"),
        app_commands.Choice(name="🪨 Métal", value="metal"),
        app_commands.Choice(name="🛢️ Pétrole", value="oil"),
        app_commands.Choice(name="⚡ Énergie", value="energy"),
        app_commands.Choice(name="🧱 Matériaux", value="materials")
    ])
    async def trade(self, interaction: discord.Interaction, target_country: str, 
                   give_resource: str, give_amount: int, receive_resource: str, receive_amount: int):
        """Échanger des ressources"""
<<<<<<< HEAD
        rules = GAME_CONFIG.get('economy_rules', {})
=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        if give_amount <= 0 or receive_amount <= 0:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Les quantités doivent être positives"),
                ephemeral=True
            )
            return
        
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
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour le commerce."),
                ephemeral=True
            )
            return
        
        # Récupérer les pays
        my_country = await db.get_country(player['country_id'])
        target_country_data = await db.get_country_by_name(target_country)
        
        if not my_country or not target_country_data:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        if my_country['id'] == target_country_data['id']:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas échanger avec votre propre pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les ressources disponibles
        my_resources = my_country.get('resources', {})
        target_resources = target_country_data.get('resources', {})
        
        if my_resources.get(give_resource, 0) < give_amount:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Pas assez de {give_resource} disponible."),
                ephemeral=True
            )
            return
        
        if target_resources.get(receive_resource, 0) < receive_amount:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"{target_country} n'a pas assez de {receive_resource}."),
                ephemeral=True
            )
            return
        
<<<<<<< HEAD
        # Caps valeur/jour et frais
        trade_value = give_amount + receive_amount
        daily = await db.get_daily_totals(player_id=player.get('id')) if player else {'trade_value': 0}
        daily_value = daily.get('trade_value', 0)
        cap_value = rules.get('trade_daily_value_cap', 100000)
        if daily_value + trade_value > cap_value:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Cap quotidien de valeur d'échange atteint."),
                ephemeral=True
            )
            return
        fee_percent = rules.get('trade_fee_percent', 2)
        fee = GameHelpers.apply_trade_fee(give_amount, fee_percent)

=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        # Effectuer l'échange
        my_resources[give_resource] -= give_amount
        my_resources[receive_resource] = my_resources.get(receive_resource, 0) + receive_amount
        
        target_resources[receive_resource] -= receive_amount
        target_resources[give_resource] = target_resources.get(give_resource, 0) + give_amount
        
<<<<<<< HEAD
        # Appliquer frais (déduit de l'argent du pays initiateur si applicable)
        if give_resource == 'money' and fee > 0:
            my_resources['money'] = max(0, my_resources.get('money', 0) - fee)

        # Mettre à jour les pays
        await db.update_country(my_country['id'], {'resources': my_resources})
        await db.update_country(target_country_data['id'], {'resources': target_resources})

        # Log transaction
        if GAME_CONFIG.get('economy_rules', {}).get('transaction_log_enabled'):
            await db.log_transaction({
                'type': 'trade',
                'player_id': player.get('id'),
                'country_id': my_country['id'],
                'target_country_id': target_country_data['id'],
                'give': {give_resource: give_amount},
                'receive': {receive_resource: receive_amount},
                'fee': fee,
                'value': trade_value
            })
=======
        # Mettre à jour les pays
        await db.update_country(my_country['id'], {'resources': my_resources})
        await db.update_country(target_country_data['id'], {'resources': target_resources})
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        
        embed = discord.Embed(
            title="🤝 Échange Commercial",
            description=f"Échange réussi avec {target_country}",
            color=0x00ff00
        )
        embed.add_field(
            name="Vous donnez",
            value=f"{give_amount} {GAME_CONFIG['resources'][give_resource]['emoji']}",
            inline=True
        )
        embed.add_field(
            name="Vous recevez",
            value=f"{receive_amount} {GAME_CONFIG['resources'][receive_resource]['emoji']}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="taxe", description="Fixer le taux d'imposition (Chef d'État seulement)")
    @app_commands.describe(tax_rate="Taux d'imposition (0-50%)")
    async def set_tax(self, interaction: discord.Interaction, tax_rate: int):
        """Fixer le taux d'imposition"""
        if tax_rate < 0 or tax_rate > 50:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Le taux d'imposition doit être entre 0% et 50%"),
                ephemeral=True
            )
            return
        
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
                embed=GameEmbeds.error_embed("Seul le Chef d'État peut fixer les impôts."),
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
        
        # Calculer l'impact sur la satisfaction
        satisfaction_impact = GameHelpers.calculate_tax_satisfaction_impact(tax_rate)
        new_stability = max(0, min(100, country.get('stability', 0) + satisfaction_impact))
        
        # Calculer les revenus fiscaux
        tax_revenue = GameHelpers.calculate_tax_revenue(country.get('population', 0), tax_rate)
        
        # Mettre à jour le pays
        resources = country.get('resources', {}).copy()
        resources['money'] = resources.get('money', 0) + tax_revenue
        
        await db.update_country(country['id'], {
            'stability': new_stability,
            'resources': resources
        })
        
        embed = discord.Embed(
            title="💰 Impôts Fixés",
            description=f"Taux d'imposition fixé à {tax_rate}%",
            color=0x00ff00
        )
        embed.add_field(
            name="Revenus fiscaux",
            value=f"{tax_revenue:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Impact stabilité",
            value=f"{satisfaction_impact:+d}%",
            inline=True
        )
        embed.add_field(
            name="Nouvelle stabilité",
            value=f"{new_stability}%",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="banque", description="Consulter le budget national")
    async def bank(self, interaction: discord.Interaction):
        """Consulter le budget national"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'bank'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour consulter la banque."),
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
        
        resources = country.get('resources', {})
        
        embed = discord.Embed(
            title=f"🏦 Budget de {country['name']}",
            color=0x0099ff
        )
        
        # Afficher toutes les ressources
        for resource, info in GAME_CONFIG['resources'].items():
            amount = resources.get(resource, 0)
            embed.add_field(
                name=info['name'],
                value=f"{amount:,} {info['emoji']}",
                inline=True
            )
        
        # Statistiques économiques
        embed.add_field(
            name="📊 Économie",
            value=f"{country.get('economy', 0)}/100",
            inline=True
        )
        embed.add_field(
            name="👥 Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        embed.add_field(
            name="📈 Stabilité",
            value=f"{country.get('stability', 0)}%",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="travail", description="Travailler pour gagner de l'argent personnel")
    async def work(self, interaction: discord.Interaction):
        """Travailler pour gagner de l'argent"""
<<<<<<< HEAD
        rules = GAME_CONFIG.get('economy_rules', {})
=======
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'êtes pas enregistré. Utilisez /rejoindre d'abord."),
                ephemeral=True
            )
            return
        
        if not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'work'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous ne pouvez pas travailler."),
                ephemeral=True
            )
            return
        
        # Calculer le salaire basé sur le rang
        role_multipliers = {
            'chief': 100,
            'vice_chief': 80,
            'economy_minister': 60,
            'defense_minister': 60,
            'governor': 40,
            'officer': 30,
            'citizen': 20,
            'recruit': 10
        }
        
        base_salary = role_multipliers.get(player.get('role', 'recruit'), 10)
        salary = base_salary + (player.get('balance', 0) // 1000)  # Bonus basé sur la richesse
        
<<<<<<< HEAD
        # Caps et cooldown
        from datetime import datetime, timedelta
        # On lit le total du jour via transactions
        totals = await db.get_daily_totals(player_id=player.get('id'))
        daily_work = totals.get('work', 0)
        daily_cap = rules.get('work_daily_cap', 20000)
        if daily_work + salary > daily_cap:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Cap quotidien de travail atteint."),
                ephemeral=True
            )
            return

        # Mettre à jour le solde du joueur
        new_balance = player.get('balance', 0) + salary
        await db.update_player(str(interaction.user.id), {'balance': new_balance})

        # Log transaction
        if GAME_CONFIG.get('economy_rules', {}).get('transaction_log_enabled'):
            await db.log_transaction({
                'type': 'work',
                'player_id': player.get('id'),
                'country_id': player.get('country_id'),
                'amount': salary
            })
=======
        # Mettre à jour le solde du joueur
        new_balance = player.get('balance', 0) + salary
        await db.update_player(str(interaction.user.id), {'balance': new_balance})
>>>>>>> b556a5d867764cde2324721253152c4615c2bcc6
        
        embed = discord.Embed(
            title="💼 Travail",
            description="Vous avez travaillé et gagné de l'argent !",
            color=0x00ff00
        )
        embed.add_field(
            name="Salaire gagné",
            value=f"{salary:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Nouveau solde",
            value=f"{new_balance:,} 💵",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
