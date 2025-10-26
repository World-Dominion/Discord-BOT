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
        self.event_task = None
    
    async def setup_hook(self):
        """Démarrer le système d'événements"""
        self.event_task = asyncio.create_task(self.event_loop())
        logger.info("Système d'événements démarré")
    
    async def cog_unload(self):
        """Arrêter le système d'événements"""
        if self.event_task:
            self.event_task.cancel()
            logger.info("Système d'événements arrêté")
    
    async def event_loop(self):
        """Boucle principale des événements"""
        while True:
            try:
                # Attendre 1 heure (3600 secondes)
                await asyncio.sleep(3600)
                
                # Déclencher un événement aléatoire
                await self.trigger_random_event()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'événements: {e}")
                await asyncio.sleep(300)  # Attendre 5 minutes avant de réessayer
    
    async def trigger_random_event(self):
        """Déclencher un événement aléatoire"""
        # Récupérer tous les pays
        countries = await db.get_all_countries()
        if not countries:
            return
        
        # Choisir un pays aléatoire
        target_country = random.choice(countries)
        
        # Générer un événement
        event = GameHelpers.get_random_event()
        
        # Appliquer les effets
        await self.apply_event_effects(target_country, event)
        
        # Enregistrer l'événement
        await self.save_event(target_country, event)
        
        # Notifier les joueurs du pays
        await self.notify_country_players(target_country, event)
        
        logger.log_game_event(
            event['type'], 
            f"{event['name']} - {event['description']}", 
            target_country['id']
        )
    
    async def apply_event_effects(self, country: dict, event: dict):
        """Appliquer les effets d'un événement sur un pays"""
        effects = event.get('effects', {})
        if not effects:
            return
        
        # Préparer les mises à jour
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
        
        # Appliquer les mises à jour
        if updates:
            await db.update_country(country['id'], updates)
    
    async def save_event(self, country: dict, event: dict):
        """Enregistrer un événement dans la base de données"""
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
        """Notifier les joueurs d'un pays d'un événement"""
        try:
            # Récupérer tous les joueurs du pays
            players_result = db.supabase.table('players').select('discord_id').eq('country_id', country['id']).execute()
            
            if not players_result.data:
                return
            
            # Créer l'embed de notification
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
            
            # Afficher les effets
            effects_text = ""
            for stat, change in event.get('effects', {}).items():
                if stat == 'economy':
                    effects_text += f"📈 Économie: {change:+d}\n"
                elif stat == 'stability':
                    effects_text += f"📊 Stabilité: {change:+d}%\n"
                elif stat == 'army_strength':
                    effects_text += f"⚔️ Force Militaire: {change:+d}\n"
            
            if effects_text:
                embed.add_field(
                    name="Effets",
                    value=effects_text,
                    inline=False
                )
            
            # Envoyer la notification à chaque joueur
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
        """Consulter les événements récents"""
        # Vérifier le joueur
        player = await db.get_player(str(interaction.user.id))
        if not player or not player.get('country_id'):
            await interaction.response.send_message(
                embed=GameEmbeds.error_embed("Vous n'appartenez à aucun pays."),
                ephemeral=True
            )
            return
        
        # Récupérer les événements récents du pays
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
    
    @app_commands.command(name="trigger-event", description="Déclencher un événement manuellement (Admin seulement)")
    @app_commands.describe(country_name="Nom du pays cible")
    async def trigger_manual_event(self, interaction: discord.Interaction, country_name: str):
        """Déclencher un événement manuellement (Admin seulement)"""
        # Vérifier les permissions admin
        from cogs.admin import AdminCog
        admin_cog = AdminCog(self.bot)
        if not admin_cog.is_admin(interaction):
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
        
        # Générer et appliquer l'événement
        event = GameHelpers.get_random_event()
        await self.apply_event_effects(country, event)
        await self.save_event(country, event)
        await self.notify_country_players(country, event)
        
        embed = discord.Embed(
            title="📢 Événement Déclenché",
            description=f"Événement '{event['name']}' déclenché sur {country_name}",
            color=0x00ff00
        )
        embed.add_field(
            name="Description",
            value=event['description'],
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
