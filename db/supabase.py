from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import asyncio
from typing import Optional, Dict, Any, List

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # ===== PLAYERS =====
    async def create_player(self, discord_id: str, username: str) -> Dict[str, Any]:
        """Créer un nouveau joueur"""
        try:
            result = self.supabase.table('players').insert({
                'discord_id': discord_id,
                'username': username,
                'role': 'recruit',
                'balance': 0
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur création joueur: {e}")
            return None
    
    async def get_player(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un joueur par son ID Discord"""
        try:
            result = self.supabase.table('players').select('*').eq('discord_id', discord_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur récupération joueur: {e}")
            return None
    
    async def get_player_by_id(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un joueur par son ID interne"""
        try:
            result = self.supabase.table('players').select('*').eq('id', player_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur récupération joueur par ID: {e}")
            return None
    
    async def update_player(self, discord_id: str, updates: Dict[str, Any]) -> bool:
        """Mettre à jour un joueur"""
        try:
            self.supabase.table('players').update(updates).eq('discord_id', discord_id).execute()
            return True
        except Exception as e:
            print(f"Erreur mise à jour joueur: {e}")
            return False
    
    # ===== COUNTRIES =====
    async def create_country(self, name: str, leader_id: str) -> Dict[str, Any]:
        """Créer un nouveau pays"""
        try:
            # Créer le pays
            country_result = self.supabase.table('countries').insert({
                'name': name,
                'leader_id': leader_id,
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
                'stability': 80
            }).execute()
            
            if country_result.data:
                country = country_result.data[0]
                # Mettre à jour le joueur pour qu'il devienne le leader
                await self.update_player(leader_id, {
                    'country_id': country['id'],
                    'role': 'chief'
                })
                return country
            return None
        except Exception as e:
            print(f"Erreur création pays: {e}")
            return None
    
    async def get_country(self, country_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un pays par son ID"""
        try:
            result = self.supabase.table('countries').select('*').eq('id', country_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur récupération pays: {e}")
            return None
    
    async def get_country_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Récupérer un pays par son nom"""
        try:
            result = self.supabase.table('countries').select('*').eq('name', name).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur récupération pays par nom: {e}")
            return None
    
    async def update_country(self, country_id: str, updates: Dict[str, Any]) -> bool:
        """Mettre à jour un pays"""
        try:
            self.supabase.table('countries').update(updates).eq('id', country_id).execute()
            return True
        except Exception as e:
            print(f"Erreur mise à jour pays: {e}")
            return False
    
    async def get_all_countries(self) -> List[Dict[str, Any]]:
        """Récupérer tous les pays"""
        try:
            result = self.supabase.table('countries').select('*').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erreur récupération tous pays: {e}")
            return []
    
    async def get_available_countries(self) -> List[Dict[str, Any]]:
        """Récupérer tous les pays non verrouillés"""
        try:
            result = self.supabase.table('countries').select('*').eq('is_locked', False).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erreur récupération pays disponibles: {e}")
            return []
    
    async def lock_country(self, country_id: str) -> bool:
        """Verrouiller un pays"""
        try:
            self.supabase.table('countries').update({'is_locked': True}).eq('id', country_id).execute()
            return True
        except Exception as e:
            print(f"Erreur verrouillage pays: {e}")
            return False
    
    async def unlock_country(self, country_id: str) -> bool:
        """Déverrouiller un pays"""
        try:
            self.supabase.table('countries').update({'is_locked': False}).eq('id', country_id).execute()
            return True
        except Exception as e:
            print(f"Erreur déverrouillage pays: {e}")
            return False
    
    # ===== WARS =====
    async def create_war(self, attacker_id: str, defender_id: str) -> Dict[str, Any]:
        """Créer une nouvelle guerre"""
        try:
            result = self.supabase.table('wars').insert({
                'attacker_id': attacker_id,
                'defender_id': defender_id
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur création guerre: {e}")
            return None
    
    async def get_active_wars(self, country_id: str) -> List[Dict[str, Any]]:
        """Récupérer les guerres actives d'un pays"""
        try:
            result = self.supabase.table('wars').select('*').or_(
                f'attacker_id.eq.{country_id},defender_id.eq.{country_id}'
            ).is_('ended_at', 'null').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Erreur récupération guerres actives: {e}")
            return []
    
    # ===== ALLIANCES =====
    async def create_alliance(self, name: str, leader_id: str) -> Dict[str, Any]:
        """Créer une nouvelle alliance"""
        try:
            result = self.supabase.table('alliances').insert({
                'name': name,
                'members': [leader_id]
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur création alliance: {e}")
            return None
    
    async def get_alliance(self, alliance_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une alliance par son ID"""
        try:
            result = self.supabase.table('alliances').select('*').eq('id', alliance_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erreur récupération alliance: {e}")
            return None
    
    async def join_alliance(self, alliance_id: str, country_id: str) -> bool:
        """Rejoindre une alliance"""
        try:
            alliance = await self.get_alliance(alliance_id)
            if alliance:
                members = alliance.get('members', [])
                if country_id not in members:
                    members.append(country_id)
                    self.supabase.table('alliances').update({'members': members}).eq('id', alliance_id).execute()
                    return True
            return False
        except Exception as e:
            print(f"Erreur rejoindre alliance: {e}")
            return False

# Instance globale
db = DatabaseManager()
