import random
from typing import Dict, Any, List, Optional
from config import GAME_CONFIG

class GameHelpers:
    @staticmethod
    def calculate_production_cost(resource: str, amount: int) -> int:
        """Calculer le coût en énergie pour produire une ressource"""
        costs = {
            'money': 1,      # 1 énergie = 100 argent
            'food': 2,       # 2 énergie = 1 nourriture
            'metal': 3,      # 3 énergie = 1 métal
            'oil': 4,        # 4 énergie = 1 pétrole
            'energy': 1,     # 1 énergie = 1 énergie (auto-production)
            'materials': 5   # 5 énergie = 1 matériau
        }
        return costs.get(resource, 1) * amount

    @staticmethod
    def apply_trade_fee(amount: int, fee_percent: int) -> int:
        """Appliquer des frais à un montant de trade (arrondi)."""
        if fee_percent <= 0:
            return 0
        return max(1, int(abs(amount) * fee_percent / 100))

    @staticmethod
    def calculate_war_result(attacker: Dict[str, Any], defender: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer le résultat d'une guerre"""
        # Facteurs de guerre
        attacker_power = (
            attacker.get('army_strength', 0) * 0.4 +
            attacker.get('economy', 0) * 0.3 +
            attacker.get('stability', 0) * 0.3
        )
        defender_power = (
            defender.get('army_strength', 0) * 0.4 +
            defender.get('economy', 0) * 0.3 +
            defender.get('stability', 0) * 0.3
        )
        # Ajouter un facteur aléatoire (±20%)
        attacker_power *= random.uniform(0.8, 1.2)
        defender_power *= random.uniform(0.8, 1.2)
        if attacker_power > defender_power:
            damage = min(20, int((attacker_power - defender_power) / 10))
            return {
                'winner': 'attacker',
                'damage': damage,
                'attacker_power': int(attacker_power),
                'defender_power': int(defender_power)
            }
        else:
            damage = min(20, int((defender_power - attacker_power) / 10))
            return {
                'winner': 'defender',
                'damage': damage,
                'attacker_power': int(attacker_power),
                'defender_power': int(defender_power)
            }

    @staticmethod
    def apply_war_damage(country: Dict[str, Any], damage: int) -> Dict[str, Any]:
        """Appliquer les dégâts de guerre à un pays"""
        new_stability = max(0, country.get('stability', 0) - damage)
        new_economy = max(0, country.get('economy', 0) - damage // 2)
        new_army = max(0, country.get('army_strength', 0) - damage // 3)
        resources = country.get('resources', {}).copy()
        for resource in resources:
            resources[resource] = max(0, resources[resource] - damage * 10)
        return {
            'stability': new_stability,
            'economy': new_economy,
            'army_strength': new_army,
            'resources': resources
        }

    @staticmethod
    def can_player_use_command(player_role: str, command_type: str) -> bool:
        """Vérifier si un joueur peut utiliser une commande selon son rang"""
        role_levels = {
            'founder': 0,
            'high_council': 1,
            'chief': 1,
            'vice_chief': 2,
            'economy_minister': 3,
            'defense_minister': 4,
            'governor': 5,
            'officer': 6,
            'soldier': 7,
            'citizen': 7,
            'recruit': 8
        }
        command_requirements = {
            'budget': 1,
            'promote': 1,
            'tax': 1,
            'war': 1,
            'commerce': 2,
            'election': 2,
            'produce': 3,
            'bank': 3,
            'army': 4,
            'attack': 4,
            'spy': 4,
            'recruit': 5,
            'infra': 5,
            'train': 6,
            'defend': 6,
            'work': 7,
            'vote': 7,
            'join': 8,
            'give': 0
        }
        player_level = role_levels.get(player_role, 8)
        required_level = command_requirements.get(command_type, 8)
        return player_level <= required_level

    @staticmethod
    def format_number(number: int) -> str:
        return f"{number:,}"

    @staticmethod
    def get_random_event() -> Dict[str, Any]:
        events = [
            {
                'type': 'economic',
                'name': 'Boom économique',
                'description': 'Votre pays connaît une période de prospérité !',
                'effects': {'economy': 10, 'stability': 5}
            },
            {
                'type': 'crisis',
                'name': 'Crise économique',
                'description': 'Une crise économique frappe votre pays...',
                'effects': {'economy': -15, 'stability': -10}
            },
            {
                'type': 'natural_disaster',
                'name': 'Catastrophe naturelle',
                'description': 'Un tremblement de terre a frappé votre pays !',
                'effects': {'stability': -20, 'economy': -10}
            },
            {
                'type': 'alliance',
                'name': 'Offre d\'alliance',
                'description': 'Un pays vous propose une alliance !',
                'effects': {'stability': 5}
            },
            {
                'type': 'war',
                'name': 'Menace de guerre',
                'description': 'Un pays voisin menace de vous attaquer...',
                'effects': {'stability': -15, 'army_strength': 5}
            }
        ]
        return random.choice(events)

    @staticmethod
    def calculate_tax_revenue(population: int, tax_rate: int) -> int:
        base_revenue = population * 0.01
        tax_multiplier = tax_rate / 100.0
        return int(base_revenue * tax_multiplier)

    @staticmethod
    def calculate_tax_satisfaction_impact(tax_rate: int) -> int:
        if tax_rate <= 10:
            return 5
        elif tax_rate <= 20:
            return 0
        elif tax_rate <= 30:
            return -5
        elif tax_rate <= 40:
            return -10
        else:
            return -20
