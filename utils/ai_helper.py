"""
Module d'intégration avec Google Gemini AI pour le jeu World Dominion
Génère du contenu dynamique pour les éléments, événements et interactions économiques
"""

import os
import json
from typing import Dict, Any, List, Optional
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Configuration Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Base de connaissances des éléments
KNOWLEDGE_BASE = """
Éléments chimiques : 118 connus (Hydrogène, Hélium, Lithium, Béryllium, Bore, Carbone, Azote, Oxygène, Fluor, Néon, Sodium, Magnésium, Aluminium, Silicium, Phosphore, Soufre, Chlore, Argon, Potassium, Calcium, Scandium, Titane, Vanadium, Chrome, Manganèse, Fer, Cobalt, Nickel, Cuivre, Zinc, Gallium, Germanium, Arsenic, Sélénium, Brome, Krypton, Rubidium, Strontium, Yttrium, Zirconium, Niobium, Molybdène, Technétium, Ruthénium, Rhodium, Palladium, Argent, Cadmium, Indium, Étain, Antimoine, Tellure, Iode, Xénon, Césium, Baryum, Lanthane, Cérium, Praséodyme, Néodyme, Prométhium, Samarium, Europium, Gadolinium, Terbium, Dysprosium, Holmium, Erbium, Thulium, Ytterbium, Lutécium, Hafnium, Tantale, Tungstène, Rhénium, Osmium, Iridium, Platine, Or, Mercure, Thallium, Plomb, Bismuth, Polonium, Astate, Radon, Francium, Radium, Actinium, Thorium, Protactinium, Uranium, Neptunium, Plutonium, Américium, Curium, Berkélium, Californium, Einsteinium, Fermium, Mendélévium, Nobélium, Lawrencium, Rutherfordium, Dubnium, Seaborgium, Bohrium, Hassium, Meitnérium, Darmstadtium, Roentgenium, Copernicium, Nihonium, Flérovium, Moscovium, Livermorium, Tennesse, Oganesson)

Espèces vivantes : environ 8,7 millions estimées (Animaux : Être humain, Baleine bleue, Tigre, Chauve-souris, Aigle royal, Manchot empereur, Cobra royal, Requin blanc, Fourmi, Abeille domestique, Calmar géant, Escargot de Bourgogne | Végétaux : Séquoia géant, Chêne pédonculé, Baobab, Rose, Tournesol, Orchidée, Blé, Maïs, Riz, Pomme de terre | Champignons : Cèpe de Bordeaux, Truffe noire, Levure de bière, Penicillium | Protistes, Bactéries : Amibe, Euglène, Plasmodium, Escherichia coli, Lactobacilles)

Minéraux : plus de 5,000 types (Silicates : Quartz, Améthyste, Citrine, Silex, Feldspaths, Micas, Olivine, Grenat, Talc, Amiante | Éléments natifs : Or, Argent, Cuivre, Diamant, Graphite, Soufre | Carbonates : Calcite, aragonite, Malachite | Oxydes : Hématite, Bauxite, Corindon, Uraninite | Sulfures : Pyrite, Galène, Cinabre | Halogénures : Halite, Fluorine)

Aliments : des dizaines de milliers (Fruits : Pomme, Banane, Orange, Fraise, Raisin, Mangue, Avocat | Légumes : Carotte, Pomme de terre, Brocoli, Tomate, Oignon, Laitue, Épinard | Céréales : Blé, Riz, Maïs, Avoine, Orge, Quinoa | Viandes : Bœuf, Porc, Poulet, Agneau, Canard | Poissons et fruits de mer : Saumon, Thon, Cabillaud, Crevettes, Huîtres | Produits laitiers : Lait, Fromage, Yaourt, Beurre | Produits transformés : Pain, Pâtes, Huile d'olive, Sucre, Chocolat, Café, Vin | Épices : Sel, Poivre, Curcuma, Paprika)

Objets manufacturés : des millions de produits (Électronique : Smartphone, Ordinateur, Téléviseur, Puce électronique | Transport : Voiture, Vélo, Avion, Navire, Train | Outils : Marteau, Tournevis, Perceuse, Scie | Vêtements : T-shirt, Jean, Chaussures, Manteau | Mobilier : Chaise, Table, Lit, Armoire | Contenants : Bouteille, Canette, Boîte, Bocal | Armes : Bertrand militaire varié | Médical : Seringue, Stéthoscope, IRM)

Concepts et œuvres : infinis (Philosophie : Vérité, Justice, Liberté, Devoir | Scientifique : Gravité, Relativité, Évolution, Atome | Mathématiques : Infini, Pi, Nombre premier, Algorithme | Politique : Démocratie, Monarchie, Capitalisme, Socialisme | Littéraires : L'Odyssée, Hamlet, Les Misérables | Musicaux : Symphonies, œuvres modernes | Arts : La Joconde, Guernica, Le Penseur)
"""

def get_model():
    """Récupérer le modèle Gemini configuré"""
    if genai is None:
        raise ValueError("google-generativeai n'est pas installé. Installez-le avec: pip install google-generativeai")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY n'est pas configuré dans les variables d'environnement")
    
    model = genai.GenerativeModel('gemini-pro')
    return model

def generate_element_details(element_type: str, element_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Génère les détails d'un élément pour le jeu en utilisant Gemini AI
    
    Args:
        element_type: Type d'élément (chimique, vivant, minéral, aliment, objet, concept)
        element_name: Nom de l'élément一寸 demandé
        context: Contexte du joueur/pays (optionnel)
    
    Returns:
        Dict avec les détails générés (materials, description, rarity, etc.)
    """
    try:
        model = get_model()
        
        # Contexte du pays si disponible
        country_context = ""
        if context:
            country_context = f"\nContexte pays : {context.get('country_name', 'Pays inconnu')}, Economie: {context.get('economy', 0)}/100, Stabilité: {context.get('stability', 0)}/100"
        
        prompt = f"""
Tu es un assistant expert dans le jeu de stratégie World Dominion.

{KNOWLEDGE_BASE}

Un joueur souhaite construire/créer l'élément suivant :
- Type : {element_type}
- Nom : {element_name}
{country_context}

Génère les informations suivantes au format JSON VALIDE (sans markdown, juste le JSON) :

{{
  "description": "Description courte et immers yesterday de l'élément dans le contexte World Dominion",
  "materials": ["matériau1", "matériau2", "..."],
  "cost": nombre,
  "rarity": "commun|rare|épique|légendaire",
  "time_to_build": "temps en heures",
  "effects": {{
    "economy": nombre,
    "stability": nombre,
    "army_strength": nombre
  }},
  "category": "{element_type}"
}}

Règles importantes :
- Les matériaux doivent être réalistes et tirés de la base de connaissances
- Coût entre 100 et 10000
- Les effets doivent être équilibrés (-10 à +10)
- Rareté selon la complexité (un smartphone = rare, un clavier = commun)
- Time_to_build en heures (ex: "2h" ou "24h")

Réponds UNIQUEMENT avec le JSON, sans explications supplémentaires.
"""
        
        response = model.generate_content(prompt)
        
        # Parser la réponse JSON
        response_text = response.text.strip()
        
        # Nettoyer si markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Ajouter le nom et type
        result['name'] = element_name
        result['type'] = element_type
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Erreur parsing JSON de Gemini: {e}")
        # Fallback
        return {
            'name': element_name,
            'type': element_type,
            'description': f"Un {element_name} pour améliorer votre pays.",
            'materials': ['metal', 'materials'],
            'cost': 500,
            'rarity': 'commun',
            'time_to_build': '2h',
            'effects': {'economy': 0, 'stability': 0, 'army_strength': 0},
            'category': element_type
        }
    except Exception as e:
        print(f"Erreur génération AI: {e}")
        # Fallback
        return {
            'name': element_name,
            'type': element_type,
            'description': f"Un {element_name} pour améliorer votre pays.",
            'materials': ['metal', 'materials'],
            'cost': 500,
            'rarity': 'commun',
            'time_to_build': '2h',
            'effects': {'economy': 0, 'stability': 0, 'army_strength': 0},
            'category': element_type
        }

def generate_event_description(event_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Génère une description d'événement aléatoire en utilisant l'IA
    
    Args:
        event_type: Type d'événement (economic, crisis, natural_disaster, alliance, war)
        context: Contexte du pays concerné
    
    Returns:
        Description générée par l'IA
    """
    try:
        model = get_model()
        
        prompt = f"""
Tu es un narrateur d'événements pour le jeu World Dominion.

Un événement de type "{event_type}" vient d'arriver dans le pays {context.get('country_name', 'Un pays') if context else 'Un pays'}.

Génère une description courte (2-3 phrases max) de cet événement, immersive et réaliste, qui s'intègre dans le contexte d'un jeu de stratégie mondiale.

Ne donne QUE la description, sans introduction ni explication supplémentaire.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Erreur génération event description: {e}")
        return f"Un événement de type {event_type} a frappé le pays."

def suggest_economic_strategy(country_data: Dict[str, Any]) -> str:
    """
    Suggère une stratégie économique basée sur l'état actuel du pays
    
    Args:
        country_data: Données du pays (économie, ressources, stabilité)
    
    Returns:
        Suggestion stratégique textuelle
    """
    try:
        model = get_model()
        
        prompt = f"""
Tu es un conseiller économique pour World Dominion.

Analyse l'état du pays suivant et propose une stratégie économique (2-3 phrases max) :

- Economie: {country_data.get('economy', 0)}/100
- Ressources: {country_data.get('resources', {})}
- Stabilité: {country_data.get('stability', 0)}/100
- Force militaire: {country_data.get('army_strength', 0)}/100

Ne donne QUE la suggestion, sans introduction.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Erreur génération strategy: {e}")
        return "Analyse en cours..."

def generate_random_discovery() -> Dict[str, Any]:
    """
    Génère une découverte aléatoire d'élément nouveau pour le jeu
    
    Returns:
        Dict avec la découverte générée
    """
    try:
        import random
        model = get_model()
        
        element_types = ["chimique", "vivant", "minéral", "aliment", "objet", "concept"]
        random_type = random.choice(element_types)
        
        prompt = f"""
Tu es un générateur de découvertes scientifiques pour World Dominion.

Crée une découverte aléatoire d'un élément de type "{random_type}" qui pourrait être trouvé dans le jeu.

Format JSON (sans markdown) :
{{
  "name": "nom de l'élément",
  "type": "{random_type}",
  "description": "Description de cette découverte",
  "rarity": "rare|épique|légendaire",
  "potential_uses": ["usage1", "usage2"]
}}

Réponds UNIQUEMENT avec le JSON.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
        
    except Exception as e:
        print(f"Erreur génération discovery: {e}")
        return {
            'name': 'Découverte mystérieuse',
            'type': 'concept',
            'description': 'Une découverte fascinante attend d\'être explorée.',
            'rarity': 'rare',
            'potential_uses': ['recherche', 'innovation']
        }

