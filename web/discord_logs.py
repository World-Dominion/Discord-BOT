"""
Module pour les logs Discord améliorés et lisibles
"""
import requests
import os
from datetime import datetime
from typing import Optional, Dict, Any

def format_number(n: int) -> str:
    """Formate un nombre avec des séparateurs de milliers"""
    try:
        return f"{n:,}".replace(",", " ")
    except:
        return str(n)

def send_discord_log(action: str, details: str, color: int = 0x00ff00, username: str = "Inconnu", user_id: str = "Inconnu"):
    """Envoie un log formaté et lisible sur Discord avec embed"""
    try:
        # Déterminer la couleur selon l'action
        action_lower = action.lower()
        if any(word in action_lower for word in ['créé', 'création', 'nouveau', 'ajouté']):
            color = 0x00ff00  # Vert
            emoji = "✅"
        elif any(word in action_lower for word in ['modifié', 'modification', 'mise à jour', 'changé']):
            color = 0xffa500  # Orange
            emoji = "✏️"
        elif any(word in action_lower for word in ['supprimé', 'suppression', 'effacé', 'retiré']):
            color = 0xff0000  # Rouge
            emoji = "🗑️"
        elif any(word in action_lower for word in ['réinitialis', 'reset', 'remise à zéro']):
            color = 0xff6b6b  # Rouge clair
            emoji = "🔄"
        elif any(word in action_lower for word in ['don', 'distribution', 'attribué', 'donné']):
            color = 0x9b59b6  # Violet
            emoji = "🎁"
        elif any(word in action_lower for word in ['sauvegarde', 'backup', 'export']):
            color = 0x3498db  # Bleu
            emoji = "💾"
        elif any(word in action_lower for word in ['guerre', 'attaque', 'conflit']):
            color = 0xe74c3c  # Rouge foncé
            emoji = "⚔️"
        elif any(word in action_lower for word in ['événement', 'event', 'déclenché']):
            color = 0xf39c12  # Jaune
            emoji = "⚡"
        else:
            color = 0x5865f2  # Bleu Discord par défaut
            emoji = "🔧"
        
        # Créer un embed Discord plus lisible
        embed = {
            "title": f"{emoji} {action}",
            "description": details,
            "color": color,
            "fields": [
                {
                    "name": "👤 Administrateur",
                    "value": f"**{username}**\n`{user_id}`",
                    "inline": True
                },
                {
                    "name": "🕐 Date/Heure",
                    "value": f"<t:{int(datetime.now().timestamp())}:F>",
                    "inline": True
                }
            ],
            "footer": {
                "text": "World Dominion Admin Panel",
            },
            "timestamp": datetime.now().isoformat(),
            "thumbnail": {
                "url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            }
        }
        
        payload = {
            "embeds": [embed],
            "username": "🌍 World Dominion Admin",
        }
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                print(f"Log Discord envoye: {action}")
                return True
            else:
                print(f"Erreur envoi log Discord: {response.status_code}")
                return False
        else:
            print("DISCORD_WEBHOOK_URL non configure")
            return False
    except Exception as e:
        print(f"Erreur envoi log Discord: {e}")
        return False

def log_country_created(country_data: Dict[str, Any], username: str, user_id: str):
    """Log pour la création d'un pays"""
    details = (
        f"**Nouveau pays créé :**\n"
        f"• **Nom :** {country_data.get('name', 'Inconnu')}\n"
        f"• **ID :** `{country_data.get('id')}`\n"
        f"• **Population :** {format_number(country_data.get('population', 0))}\n"
        f"• **Économie :** {country_data.get('economy', 0)}/100\n"
        f"• **Stabilité :** {country_data.get('stability', 0)}%\n"
        f"• **Armée :** {country_data.get('army_strength', 0)}/100"
    )
    return send_discord_log("🏗️ Création de pays", details, 0x00ff00, username, user_id)

def log_country_modified(country_data: Dict[str, Any], changes: list, username: str, user_id: str):
    """Log pour la modification d'un pays"""
    changes_text = "\n".join([f"• {change}" for change in changes]) if changes else "Aucun détail"
    details = (
        f"**Pays modifié :** {country_data.get('name', 'Inconnu')}\n"
        f"**ID :** `{country_data.get('id')}`\n\n"
        f"**Changements :**\n{changes_text}"
    )
    return send_discord_log("✏️ Modification de pays", details, 0xffa500, username, user_id)

def log_country_deleted(country_name: str, country_id: str, username: str, user_id: str):
    """Log pour la suppression d'un pays"""
    details = (
        f"**Pays supprimé :** {country_name}\n"
        f"**ID :** `{country_id}`\n\n"
        f"⚠️ **Attention :** Tous les joueurs de ce pays ont été réinitialisés"
    )
    return send_discord_log("🗑️ Suppression de pays", details, 0xff0000, username, user_id)

def log_player_modified(player_data: Dict[str, Any], changes: list, username: str, user_id: str):
    """Log pour la modification d'un joueur"""
    changes_text = "\n".join([f"• {change}" for change in changes]) if changes else "Aucun détail"
    details = (
        f"**Joueur modifié :** {player_data.get('username', 'Inconnu')}\n"
        f"**ID :** `{player_data.get('id')}`\n"
        f"**Rôle :** {player_data.get('role', 'recruit')}\n\n"
        f"**Changements :**\n{changes_text}"
    )
    return send_discord_log("✏️ Modification de joueur", details, 0xffa500, username, user_id)

def log_war_ended(war_id: str, username: str, user_id: str):
    """Log pour la fin d'une guerre"""
    details = f"**Guerre terminée :** `{war_id}`\n\nGuerre mise fin par un administrateur"
    return send_discord_log("⚔️ Fin de guerre", details, 0xe74c3c, username, user_id)

def log_event_triggered(event_data: Dict[str, Any], username: str, user_id: str):
    """Log pour un événement déclenché"""
    details = (
        f"**Événement déclenché :**\n"
        f"• **Type :** {event_data.get('type', 'Inconnu')}\n"
        f"• **Description :** {event_data.get('description', 'Aucune')}\n"
        f"• **Pays cible :** `{event_data.get('target_country', 'Inconnu')}`"
    )
    return send_discord_log("⚡ Événement déclenché", details, 0xf39c12, username, user_id)

def log_tools_action(action: str, details: str, count: int = 0, username: str = "Inconnu", user_id: str = "Inconnu"):
    """Log pour les actions d'outils"""
    if count > 0:
        details += f"\n\n**Nombre d'éléments affectés :** {count}"
    
    return send_discord_log(f"🔧 {action}", details, 0x5865f2, username, user_id)

def log_admin_give(target_type: str, target_id: str, resource: str, amount: int, username: str, user_id: str):
    """Log pour les dons administrateur"""
    details = (
        f"**Don administrateur :**\n"
        f"• **Cible :** {target_type} `{target_id or 'Tous'}`\n"
        f"• **Ressource :** {resource}\n"
        f"• **Montant :** {format_number(amount)}"
    )
    return send_discord_log("🎁 Don administrateur", details, 0x9b59b6, username, user_id)

def log_player_deleted(player_name: str, player_id: str, username: str, user_id: str):
    """Log pour la suppression d'un joueur"""
    details = (
        f"**Joueur supprimé :** {player_name}\n"
        f"**ID :** `{player_id}`\n\n"
        f"⚠️ **Attention :** Le joueur a été définitivement supprimé"
    )
    return send_discord_log("🗑️ Suppression de joueur", details, 0xff0000, username, user_id)

def log_war_deleted(war_id: str, username: str, user_id: str):
    """Log pour la suppression d'une guerre"""
    details = f"**Guerre supprimée :** `{war_id}`\n\nGuerre supprimée de la base de données"
    return send_discord_log("🗑️ Suppression de guerre", details, 0xff0000, username, user_id)
