"""
Module d'intégration avancée avec Google Gemini AI pour World Dominion
Génère du contenu dynamique, varié et immersif basé sur le nouveau prompt système
"""

import os
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Configuration Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# NOUVEAU PROMPT SYSTÈME COMPLET
SYSTEM_PROMPT = """
# Prompt Gemini - Générateur d'Idées pour Jeu d'Éléments Discord

Tu es un assistant créatif qui aide à imaginer des mécaniques de jeu et des idées pour un système d'attractions Discord.

## Contexte
Un bot Discord où les joueurs collectionnent des éléments réels issus de 6 catégories :
- 🧪 Éléments chimiques (118 éléments : H, C, Au, U...)
- 🌿 Espèces vivantes (~8,7M : animaux, plantes, champignons... grisons)
- 💎 Minéraux (5000+ : Quartz, Diamant, Pyrite...)
- 🍎 Aliments (milliers : fruits, viandes, fromages...)
- 🔧 Objets manufacturés (millions : outils, électronique, vêtements...)
- 💡 Concepts & œuvres (infinis : idées, art, musique...)

Base de données : Supabase avec tables `elements`, `players`, `transactions`

## Le rôle 
Quand on te demande, propose des idées pour :

### Mécaniques de jeu poussée 
- Systèmes d'attractions thématiques
- Événements temporaires (ex: "Semaine des éléments rares")
- Combos et synergies entre éléments
- Défis de collection (ex: "Collectionne tous les gaz nobles")
- Système d'échange entre joueurs

### Fonctionnalités précis 
- Commandes Discord utiles et fun
- Systèmes de progression/niveaux
- Récompenses et achievements
- Mini-jeux basés sur les éléments
- Classements et compétitions

### Contenus réaliste & éducatif
- Façons d'apprendre via le jeu
- Quiz et énigmes sur les éléments
- Faits intéressants à partager
- Liens entre différents éléments

### Équilibrage
- Systèmes de rareté cohérents
- Économie du jeu (si échanges)
- Probabilités d'obtention
- Valeur relative des éléments

## Style de réponses
- Créatif et innovant
- Ludique mais réfléchi
- Donne 3-5 idées par demande
- Explique pourquoi l'idée est intéressante
- Pense à la faisabilité technique
"""

def get_model():
    """Récupérer le modèle Gemini configuré"""
    if genai is None:
        raise ValueError("google-generativeai n'est pas installé. Installez-le avec: pip install google-generativeai")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY n'est pas configuré dans les variables d'environnement")
    
    # Utiliser gemini-1.5-flash pour une meilleure rapidité
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def generate_vibrant_element(element_type: str, element_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    GÉNÈRE UN ÉLÉMENT DYNAMIQUE ET VIVANT avec variations aléatoires
    
    Args:
        element_type: Type d'élément
        element_name: Nom de l'élément
        context: Contexte du pays
    
    Returns:
        Dict avec détails générés avec IA avancée
    """
    try:
        model = get_model()
        
        # Context enrichi
        country_context = ""
        if context:
            country_context = f"""
Contexte du pays '{context.get('country_name', 'Un pays inconnu')}' :
- Économie: {context.get('economy', 0)}/100
- Stabilité: {context.get('stability', 0)}%
- Force Militaire: {context.get('army_strength', 0)}/100
- Ressources: {context.get('resources', {})}
- Date du jour: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        # Générer des variations thématiques
        themes = [
            "élément historique et légendaire",
            "découverte scientifique récente",
            "objet manufacturé futuriste",
            "creature rare et mystique",
            "concept philosophique profond"
        ]
        theme = random.choice(themes)
        
        prompt = f"""
{SYSTEM_PROMPT}

## DEMANDE ACTUELLE

Un joueur souhaite créer un nouvel élément dans World Dominion.
{country_context}

Type d'élément : {element_type}
Nom de l'élément : {element_name}
Thème souhaité : {theme}

## À GÉNÉRER

Crée un élément unique, original et immersif. Sois créatif !

Génère au format JSON STRICT (sans markdown) :

{{
  "name": "{element_name}",
  "type": "{element_type}",
  "description": "Description vivante et immersive (2-3 phrases max, parle comme dans un jeu)",
  "lore": "Histoire/lore court de cet élément (1 phrase)",
  "materials": ["matériau1", "matériau2", "matériau3"],
  "cost": nombre_entre_100_et_5000,
  "rarity": "commun|rare|épique|légendaire|divin",
  "time_to_build": "temps comme '2h', '1j', '3j'",
  "effects": {{
    "economy": nombre_entre_-15_et_+15,
    "stability": nombre_entre_-15_et_+15,
    "army_strength": nombre_entre_-15_et_+15
  }},
  "special_abilities": ["capacité1", "capacité2"],
  "fun_fact": "Fait amusant ou éducatif sur cet élément",
  "discovery_chance": nombre_entre_0_et_100
}}

Règles IMPORTANTES :
- Description : Sois créatif, parle de manière immersive, utilise des métaphores si ça colle au thème
- Materials : Utilise des matériaux réalistes (Fer, Bois, Or, Textiles, Électronique, etc.)
- Rareté : Divin = unique, Légendaire = ultra rare, Épique = rare, Rare = peu commun, Commun = commun
- Effects : Équilibre les effets selon la rareté
- Special abilities : Ajoute des capacités fun ou intéressantes (max 2)
- Fun fact : Classification naturelle de l'élément
- Discovery chance : Probabilité qu'un joueur trouve cet élément naturellement (0-100%)

Réponds UNIQUEMENT avec le JSON, SANS markdown, SANS backticks.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Nettoyer la réponse
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Ajouter des métadonnées
        result['created_at'] = datetime.now().isoformat()
        result['theme'] = theme
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Erreur parsing JSON IA: {e}")
        return _get_fallback_element(element_name, element_type)
    except Exception as e:
        print(f"Erreur génération IA: {e}")
        return _get_fallback_element(element_name, element_type)

def _get_fallback_element(name: str, element_type: str) -> Dict[str, Any]:
    """Fallback si l'IA échoue"""
    materials_map = {
        "chimique": ["Laboratoire", "Réactifs", "Energie"],
        "vivant": ["Écosystème", "Nourriture", "Eau"],
        "minéral": ["Extraction", "Minerai brut", "Outils"],
        "aliment": ["Ingrédients", "Épices", "Chaleur"],
        "objet": ["Métal", "Électronique", "Textiles"],
        "concept": ["Inspiration", "Sagesse", "Innovation"]
    }
    
    return {
        'name': name,
        'type': element_type,
        'description': f"Un {name} fascinant pour enrichir votre pays.",
        'lore': "Découvert dans les archives anciennes du monde.",
        'materials': materials_map.get(element_type, ["Matières premières", "Main d'œuvre"]),
        'cost': random.randint(300, 1500),
        'rarity': 'commun',
        'time_to_build': '2h',
        'effects': {'economy': 0, 'stability': 0, 'army_strength': 0},
        'special_abilities': ["Capacité de base"],
        'fun_fact': f"L'élément {name} est unique dans sa catégorie.",
        'discovery_chance': 50,
        'theme': 'standard'
    }

def generate_economic_analysis(country_data: Dict[str, Any]) -> str:
    """Génère une analyse économique poussée avec l'IA"""
    try:
        model = get_model()
        
        prompt = f"""
{SYSTEM_PROMPT}

## ANALYSE ÉCONOMIQUE DEMANDÉE

Analyse l'état économique du pays suivant et propose une stratégie détaillée :

```json
{json.dumps(country_data, indent=2)}
```

Donne une analyse en 3 parties :
1. État actuel (forces et faiblesses)
2. Opportunités disponibles
3. Recommandations stratégiques (3 actions concrètes)

Réponds de manière concise et actionnable (150 mots max).
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erreur génération analyse: {e}")
        return "Analyse en cours de génération..."

def generate_event_narrative(event_type: str, country_data: Dict[str, Any]) -> str:
    """Génère un récit d'événement immersif"""
    try:
        model = get_model()
        
        prompt = f"""
{SYSTEM_PROMPT}

## GÉNÉRATION D'ÉVÉNEMENT

Type d'événement : {event_type}
Pays concerné : {country_data.get('name', 'Un pays')}

Génère un récit court (3-4 phrases) décrivant cet événement de manière immersive et narrative.
Utilise un ton approprié au type d'événement (dramatique pour crise, positif pour boom, etc.).

Réponds UNIQUEMENT avec le récit, sans introduction.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erreur génération événement: {e}")
        return f"Un événement de type {event_type} a frappé le pays."

def generate_discovery_idea() -> Dict[str, Any]:
    """Génère une idée de découverte aléatoire"""
    try:
        model = get_model()
        
        element_types = ["chimique", "vivant", "minéral", "aliment", "objet", "concept"]
        random_type = random.choice(element_types)
        
        prompt = f"""
{SYSTEM_PROMPT}

## DÉCOUVERTE ALÉATOIRE

Génère une idée de découverte surprenante de type "{random_type}" qui pourrait être trouvée dans le jeu.

Format JSON :
{{
  "name": "nom créatif et original",
  "type": "{random_type}",
  "description": "ce qui a été découvert",
  "rarity": "rare|épique|légendaire",
  "potential_uses": ["usage1", "usage2"],
  "real_world_fact": "fait réel sur cet élément"
}}

Réponds UNIQUEMENT avec le JSON.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        print(f"Erreur génération découverte: {e}")
        return {
            'name': 'Découverte mystérieuse',
            'type': 'concept',
            'description': 'Une découverte fascinante attend d\'être explorée.',
            'rarity': 'rare',
            'potential_uses': ['recherche', 'innovation']
        }

# Fonction de compatibilité avec l'ancienne version
def generate_element_details(element_type: str, element_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Wrapper pour compatibilité avec l'ancien code"""
    return generate_vibrant_element(element_type, element_name, context)

