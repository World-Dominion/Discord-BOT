import discord
from typing import Dict, Any, Optional
from config import GAME_CONFIG

class GameEmbeds:
    @staticmethod
    def country_info(country: Dict[str, Any], leader_name: str = "Inconnu") -> discord.Embed:
        """Embed d'informations sur un pays"""
        resources = country.get('resources', {})
        
        embed = discord.Embed(
            title=f"🏳️ {country['name']}",
            color=0x00ff00
        )
        
        embed.add_field(
            name="👑 Chef d'État",
            value=leader_name,
            inline=True
        )
        
        embed.add_field(
            name="👥 Population",
            value=f"{country.get('population', 0):,}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Stabilité",
            value=f"{country.get('stability', 0)}%",
            inline=True
        )
        
        # Ressources
        resources_text = ""
        for resource, emoji in GAME_CONFIG['resources'].items():
            amount = resources.get(resource, 0)
            resources_text += f"{emoji['emoji']} {amount:,}\n"
        
        embed.add_field(
            name="💰 Ressources",
            value=resources_text or "Aucune ressource",
            inline=False
        )
        
        # Statistiques
        embed.add_field(
            name="📈 Économie",
            value=f"{country.get('economy', 0)}/100",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Force Militaire",
            value=f"{country.get('army_strength', 0)}/100",
            inline=True
        )
        
        return embed
    
    @staticmethod
    def player_info(player: Dict[str, Any], country_name: str = "Aucun pays") -> discord.Embed:
        """Embed d'informations sur un joueur"""
        role_info = GAME_CONFIG['roles'].get(player.get('role', 'recruit'), {})
        
        embed = discord.Embed(
            title=f"👤 {player['username']}",
            color=0x0099ff
        )
        
        embed.add_field(
            name="🏳️ Pays",
            value=country_name,
            inline=True
        )
        
        embed.add_field(
            name="🎖️ Rang",
            value=role_info.get('name', '🧒 Recrue'),
            inline=True
        )
        
        embed.add_field(
            name="💰 Argent Personnel",
            value=f"{player.get('balance', 0):,} 💵",
            inline=True
        )
        
        # NOUVEAU : Inventaire
        inventory = player.get('inventory', [])
        if inventory and len(inventory) > 0:
            inv_text = ""
            for item in inventory[:5]:
                item_name = item if isinstance(item, str) else item.get('name', 'Objet')
                inv_text += f"• {item_name}\n"
            if len(inventory) > 5:
                inv_text += f"... et {len(inventory) - 5} autres"
            
            embed.add_field(
                name="🎒 Inventaire",
                value=inv_text or "Aucun objet",
                inline=False
            )
        
        return embed
    
    @staticmethod
    def war_info(war: Dict[str, Any], attacker_name: str, defender_name: str) -> discord.Embed:
        """Embed d'informations sur une guerre"""
        embed = discord.Embed(
            title="⚔️ Guerre en cours",
            color=0xff0000
        )
        
        embed.add_field(
            name="🪖 Attaquant",
            value=attacker_name,
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Défenseur",
            value=defender_name,
            inline=True
        )
        
        embed.add_field(
            name="📅 Début",
            value=war.get('started_at', 'Inconnu'),
            inline=True
        )
        
        return embed
    
    @staticmethod
    def alliance_info(alliance: Dict[str, Any]) -> discord.Embed:
        """Embed d'informations sur une alliance"""
        members = alliance.get('members', [])
        
        embed = discord.Embed(
            title=f"🤝 Alliance: {alliance['name']}",
            color=0x9932cc
        )
        
        embed.add_field(
            name="👥 Membres",
            value=f"{len(members)} pays",
            inline=True
        )
        
        embed.add_field(
            name="📅 Créée le",
            value=alliance.get('created_at', 'Inconnu'),
            inline=True
        )
        
        return embed
    
    @staticmethod
    def production_result(resource: str, amount: int, cost: int) -> discord.Embed:
        """Embed de résultat de production"""
        resource_info = GAME_CONFIG['resources'].get(resource, {})
        
        embed = discord.Embed(
            title="🏭 Production",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📦 Produit",
            value=f"{resource_info.get('emoji', '📦')} {amount:,} {resource_info.get('name', resource)}",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Coût en énergie",
            value=f"{cost:,} ⚡",
            inline=True
        )
        
        return embed
    
    @staticmethod
    def error_embed(message: str) -> discord.Embed:
        """Embed d'erreur"""
        return discord.Embed(
            title="❌ Erreur",
            description=message,
            color=0xff0000
        )
    
    @staticmethod
    def success_embed(message: str) -> discord.Embed:
        """Embed de succès"""
        return discord.Embed(
            title="✅ Succès",
            description=message,
            color=0x00ff00
        )
    
    @staticmethod
    def leaderboard(countries: list) -> discord.Embed:
        """Embed du classement des pays"""
        embed = discord.Embed(
            title="🏆 Classement Mondial",
            color=0xffd700
        )
        
        for i, country in enumerate(countries[:10], 1):
            score = country.get('economy', 0) + country.get('army_strength', 0) + country.get('stability', 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            embed.add_field(
                name=f"{medal} {country['name']}",
                value=f"Score: {score} | Éco: {country.get('economy', 0)} | Mil: {country.get('army_strength', 0)} | Stab: {country.get('stability', 0)}",
                inline=False
            )
        
        return embed
