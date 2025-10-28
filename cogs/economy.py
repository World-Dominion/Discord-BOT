import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from utils.ai_helper_gemini import generate_element_details
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
        rules = GAME_CONFIG.get('economy_rules', {})
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
        
        # Cap quotidien
        daily = await db.get_daily_totals(player_id=player.get('id')) if player else {'produce': {}}
        daily_res = daily.get('produce', {}).get(resource, 0)
        cap = rules.get('produce_daily_cap_per_resource', 2000)
        if daily_res + amount > cap:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed(f"Cap quotidien atteint pour {resource}. Restant: {max(0, cap - daily_res)}"),
                ephemeral=True
            )
            return

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
        rules = GAME_CONFIG.get('economy_rules', {})
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

        # Effectuer l'échange
        my_resources[give_resource] -= give_amount
        my_resources[receive_resource] = my_resources.get(receive_resource, 0) + receive_amount
        
        target_resources[receive_resource] -= receive_amount
        target_resources[give_resource] = target_resources.get(give_resource, 0) + give_amount
        
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
        
        # Caps et cooldown - NOUVEAU SYSTÈME
        from datetime import datetime, timedelta
        current_time = datetime.utcnow()
        
        # Vérifier le cooldown (6 heures)
        last_work = player.get('last_work_time')
        if last_work:
            last_work_time = datetime.fromisoformat(last_work) if isinstance(last_work, str) else last_work
            cooldown_hours = 6
            time_since_last_work = current_time - last_work_time
            
            if time_since_last_work.total_seconds() < cooldown_hours * 3600:
                hours_left = cooldown_hours - (time_since_last_work.total_seconds() / 3600)
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed(f"⏱️ Cooldown actif ! Vous pourrez retravailler dans {hours_left:.1f}h"),
                    ephemeral=True
                )
                return
        
        # On lit le total du jour via transactions
        totals = await db.get_daily_totals(player_id=player.get('id'))
        daily_work = totals.get('work', 0)
        daily_cap = GAME_CONFIG.get('economy_rules', {}).get('work_daily_cap', 20000)
        if daily_work + salary > daily_cap:
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Cap quotidien de travail atteint."),
                ephemeral=True
            )
            return

        # NOUVEAU : Calcul des taxes (15% pour le pays)
        tax_rate = 0.15  # 15% de taxe
        tax_amount = int(salary * tax_rate)
        net_salary = salary - tax_amount
        
        # Mettre à jour le solde du joueur avec le salaire NET
        new_balance = player.get('balance', 0) + net_salary
        await db.update_player(str(interaction.user.id), {'balance': new_balance, 'last_work_time': current_time.isoformat()})
        
        # NOUVEAU : Ajouter la taxe à la banque du pays
        country = await db.get_country(player['country_id'])
        if country:
            country_resources = country.get('resources', {})
            country_resources['money'] = country_resources.get('money', 0) + tax_amount
            await db.update_country(country['id'], {'resources': country_resources})

        # Log transaction
        if GAME_CONFIG.get('economy_rules', {}).get('transaction_log_enabled'):
            await db.log_transaction({
                'type': 'work',
                'player_id': player.get('id'),
                'country_id': player.get('country_id'),
                'amount': salary
            })
        
        embed = discord.Embed(
            title="💼 Travail",
            description="Vous avez travaillé et gagné de l'argent !",
            color=0x00ff00
        )
        embed.add_field(
            name="Salaire brut",
            value=f"{salary:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Taxe (15%)",
            value=f"-{tax_amount:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Salaire net reçu",
            value=f"{net_salary:,} 💵",
            inline=True
        )
        embed.add_field(
            name="Nouveau solde",
            value=f"{new_balance:,} 💵",
            inline=False
        )
        embed.set_footer(text="⏱️ Prochain travail disponible dans 6h")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="construire", description="Construire un élément (aliment, objet, concept, etc.) avec l'IA")
    @app_commands.describe(
        element_name="Nom de l'élément à construire",
        element_type="Type d'élément"
    )
    @app_commands.choices(element_type=[
        app_commands.Choice(name="🍎 Aliment", value="aliment"),
        app_commands.Choice(name="🏗️ Objet manufacturé", value="objet"),
        app_commands.Choice(name="🧪 Élément chimique", value="chimique"),
        app_commands.Choice(name="🌿 Espèce vivante", value="vivant"),
        app_commands.Choice(name="💎 Minéral", value="minéral"),
        app_commands.Choice(name="💡 Concept/Idée", value="concept")
    ])
    async def construire(self, interaction: discord.Interaction, element_name: str, element_type: str):
        """Construire un élément en utilisant l'IA Gemini"""
        await interaction.response.defer(ephemeral=False)
        
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.followup.send(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Vérifier les permissions
        if not GameHelpers.can_player_use_command(player.get('role', 'recruit'), 'produce'):
            await interaction.followup.send(
                embed=GameEmbeds.error_embed("Vous n'avez pas les permissions pour construire des éléments."),
                ephemeral=True
            )
            return
        
        # Récupérer le pays pour le contexte
        country = await db.get_country(player['country_id'])
        if not country:
            await interaction.followup.send(
                embed=GameEmbeds.error_embed("Pays introuvable."),
                ephemeral=True
            )
            return
        
        # Générer les détails de l'élément avec l'IA
        try:
            context = {
                'country_name': country['name'],
                'economy': country.get('economy', 0),
                'stability': country.get('stability', 0),
                'resources': country.get('resources', {})
            }
            
            element_details = generate_element_details(element_type, element_name, context)
            
            # Vérifier si le pays a les ressources nécessaires
            country_resources = country.get('resources', {})
            required_materials = element_details.get('materials', [])
            cost = element_details.get('cost', 0)
            
            # Vérifier l'argent
            if country_resources.get('money', 0) < cost:
                await interaction.followup.send(
                    embed=GameEmbeds.error_embed(f"Pas assez d'argent ! Nécessaire: {cost} 💵, Disponible: {country_resources.get('money', 0)}"),
                    ephemeral=True
                )
                return
            
            # Vérifier les matériaux (simplifié: on vérifie juste si les matériaux de base existent)
            for material in required_materials:
                # Convertir le nom du matériau en ressource du jeu
                material_map = {
                    'metal': 'metal',
                    'materials': 'materials',
                    'oil': 'oil',
                    'energy': 'energy',
                    'food': 'food',
                    'argent': 'money',
                    'money': 'money'
                }
                resource_key = material_map.get(material.lower(), 'materials')
                if country_resources.get(resource_key, 0) < 10:
                    await interaction.followup.send(
                        embed=GameEmbeds.error_embed(f"Pas assez de {material}. Minimum requis: 10"),
                        ephemeral=True
                    )
                    return
            
            # Déduire le coût
            country_resources['money'] = country_resources.get('money', 0) - cost
            
            # Déduire les matériaux de base (10 de chaque)
            for material in required_materials:
                material_map = {
                    'metal': 'metal',
                    'materials': 'materials',
                    'oil': 'oil',
                    'energy': 'energy',
                    'food': 'food'
                }
                resource_key = material_map.get(material.lower(), 'materials')
                country_resources[resource_key] = max(0, country_resources.get(resource_key, 0) - 10)
            
            # Mettre à jour le pays
            await db.update_country(country['id'], {'resources': country_resources})
            
            # Créer l'élément dans la DB
            element_db = await db.create_element(element_details, player['id'], country['id'])
            
            # Log transaction
            if GAME_CONFIG.get('economy_rules', {}).get('transaction_log_enabled'):
                await db.log_transaction({
                    'type': 'build',
                    'player_id': player.get('id'),
                    'country_id': country['id'],
                    'resource': element_name,
                    'amount': cost,
                    'cost_energy': 0
                })
            
            # Créer l'embed de réponse
            embed = discord.Embed(
                title=f"🏗️ {element_details['name']} - {element_details.get('rarity', 'commun').upper()}",
                description=element_details.get('description', 'Un nouvel élément a été construit.'),
                color={
                    'commun': 0x808080,
                    'rare': 0x0099ff,
                    'épique': 0x9932cc,
                    'légendaire': 0xffd700
                }.get(element_details.get('rarity', 'commun'), 0x808080)
            )
            
            # Matériaux requis
            materials_text = ", ".join([f"{mat} (10)" for mat in required_materials[:5]])
            embed.add_field(
                name="📦 Matériaux utilisés",
                value=materials_text if required_materials else "Aucun",
                inline=False
            )
            
            # Coût
            embed.add_field(
                name="💰 Coût",
                value=f"{cost} 💵",
                inline=True
            )
            
            # Temps de construction
            embed.add_field(
                name="⏱️ Temps",
                value=element_details.get('time_to_build', '2h'),
                inline=True
            )
            
            # Effets
            effects = element_details.get('effects', {})
            if effects:
                effects_text = ""
                if effects.get('economy'):
                    effects_text += f"📈 Économie: {effects['economy']:+d}\n"
                if effects.get('stability'):
                    effects_text += f"📊 Stabilité: {effects['stability']:+d}\n"
                if effects.get('army_strength'):
                    effects_text += f"⚔️ Force Militaire: {effects['army_strength']:+d}\n"
                if effects_text:
                    embed.add_field(
                        name="⚡ Effets",
                        value=effects_text,
                        inline=False
                    )
            
            # Appliquer les effets au pays
            updates = {}
            if effects.get('economy'):
                new_economy = max(0, min(100, country.get('economy', 50) + effects['economy']))
                updates['economy'] = new_economy
            if effects.get('stability'):
                new_stability = max(0, min(100, country.get('stability', 80) + effects['stability']))
                updates['stability'] = new_stability
            if effects.get('army_strength'):
                new_army = max(0, min(100, country.get('army_strength', 20) + effects['army_strength']))
                updates['army_strength'] = new_army
            
            if updates:
                await db.update_country(country['id'], updates)
            
            # Footer
            embed.set_footer(text=f"Construit par {interaction.user.name} dans {country['name']}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Erreur lors de la construction: {e}")
            await interaction.followup.send(
                embed=GameEmbeds.error_embed(f"Erreur lors de la génération de l'élément: {str(e)}"),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
