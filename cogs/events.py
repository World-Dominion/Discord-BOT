import discord
from discord.ext import commands
from discord import app_commands
from db.supabase import db
from utils.embeds import GameEmbeds
from utils.helpers import GameHelpers
from utils.logger import logger
import asyncio
import random
from datetime import datetime, timedelta

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_task = asyncio.create_task(self.event_loop())
        logger.info("Système d'événements démarré")

    async def cog_unload(self):
        if self.event_task:
            self.event_task.cancel()
            logger.info("Système d'événements arrêté")

    async def event_loop(self):
        while True:
            try:
                await asyncio.sleep(3600)
                await self.trigger_random_event()
                await self.apply_economic_tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'événements: {e}")
                await asyncio.sleep(300)

    async def trigger_random_event(self):
        countries = await db.get_all_countries()
        if not countries:
            return
        target_country = random.choice(countries)
        event = GameHelpers.get_random_event()
        await self.apply_event_effects(target_country, event)
        await self.save_event(target_country, event)
        await self.notify_country_players(target_country, event)
        logger.log_game_event(
            event['type'],
            f"{event['name']} - {event['description']}",
            target_country['id']
        )

    async def apply_event_effects(self, country: dict, event: dict):
        effects = event.get('effects', {})
        if not effects:
            return
        updates = {}
        for stat, change in effects.items():
            if stat == 'economy':
                new_value = max(0, min(100, country.get('economy', 50) + change))
                updates['economy'] = new_value
            elif stat == 'stability':
                new_value = max(0, min(100, country.get('stability', 80) + change))
                updates['stability'] = new_value
            elif stat == 'army_strength':
                new_value = max(0, min(100, country.get('army_strength', 20) + change))
                updates['army_strength'] = new_value
        if updates:
            await db.update_country(country['id'], updates)

    async def save_event(self, country: dict, event: dict):
        try:
            db.supabase.table('events').insert({
                'type': event['type'],
                'description': f"{event['name']} - {event['description']}",
                'target_country': country['id'],
                'impact': event.get('effects', {}),
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Erreur sauvegarde événement: {e}")

    async def notify_country_players(self, country: dict, event: dict):
        try:
            players_result = db.supabase.table('players').select('discord_id').eq('country_id', country['id']).execute()
            if not players_result.data:
                return
            embed = discord.Embed(
                title=f"📢 Événement dans {country['name']}",
                description=event['description'],
                color=0xff9900 if event['type'] == 'crisis' else 0x00ff00
            )
            embed.add_field(
                name="Type d'événement",
                value=event['name'],
                inline=True
            )
            effects_text = ""
            for stat, change in event.get('effects', {}).items():
                if stat == 'economy': effects_text += f"📈 Économie: {change:+d}\n"
                elif stat == 'stability': effects_text += f"📊 Stabilité: {change:+d}%\n"
                elif stat == 'army_strength': effects_text += f"⚔️ Force Militaire: {change:+d}\n"
            if effects_text:
                embed.add_field(
                    name="Effets",
                    value=effects_text,
                    inline=False
                )
            for player in players_result.data:
                try:
                    user = self.bot.get_user(int(player['discord_id']))
                    if user:
                        await user.send(embed=embed)
                except Exception as e:
                    logger.error(f"Erreur notification joueur {player['discord_id']}: {e}")
        except Exception as e:
            logger.error(f"Erreur notification pays: {e}")

    @app_commands.command(name="events", description="Consulter les événements récents")
    async def view_events(self, interaction: discord.Interaction):
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        try:
            events_result = db.supabase.table('events').select('*').eq('target_country', player['country_id']).order('created_at', desc=True).limit(5).execute()
            if not events_result.data:
                await interaction.response.send_message(
                    embed=GameEmbeds.error_embed("Aucun événement récent trouvé."),
                    ephemeral=True
                )
                return
            embed = discord.Embed(
                title="📢 Événements Récents",
                color=0x0099ff
            )
            for event in events_result.data:
                event_type_emoji = {
                    'economic': '💰',
                    'crisis': '⚠️',
                    'natural_disaster': '🌪️',
                    'alliance': '🤝',
                    'war': '⚔️'
                }.get(event['type'], '📢')
                embed.add_field(
                    name=f"{event_type_emoji} {event['description']}",
                    value=f"<t:{int(datetime.fromisoformat(event['created_at']).timestamp())}:R>",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erreur récupération événements: {e}")
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Erreur lors de la récupération des événements."),
                ephemeral=True
            )

    async def apply_economic_tick(self):
        try:
            from config import GAME_CONFIG
            rules = GAME_CONFIG.get('economy_rules', {})
            inflation = rules.get('inflation_percent_daily', 0)
            interest = rules.get('interest_percent_daily', 0)
            maintenance_per = rules.get('army_maintenance_per_strength', 0)
            countries = await db.get_all_countries()
            if not countries:
                return
            for c in countries:
                resources = c.get('resources', {}) or {}
                money = resources.get('money', 0) or 0
                if interest > 0 and money > 0:
                    gain = int(money * interest / 100)
                    money += gain
                if inflation > 0 and money > 0:
                    loss = int(money * inflation / 100)
                    money = max(0, money - loss)
                maintenance_cost = max(0, int((c.get('army_strength', 0) or 0) * maintenance_per))
                money = max(0, money - maintenance_cost)
                resources['money'] = money
                await db.update_country(c['id'], {'resources': resources})
                await db.log_transaction({
                    'type': 'tick',
                    'country_id': c['id'],
                    'amount': -maintenance_cost,
                    'value': 0,
                    'fee': 0
                })
        except Exception as e:
            logger.error(f"Erreur tick économique: {e}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
