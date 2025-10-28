# 🤖 Configuration de l'IA Gemini pour World Dominion

Ce guide explique comment configurer l'intégration de l'IA Google Gemini dans le jeu World Dominion.

## 📋 Prérequis

1. Une clé API Google Gemini (gratuite via [Google AI Studio](https://makersuite.google.com/app/apikey))
2. Python 3.8+ avec les dépendances installées
3. Une base de données Supabase configurée

## 🚀 Installation

### 1. Installer la dépendance Gemini

```bash
pip install -r requirements.txt
```

Ou directement :

```bash
pip install google-generativeai>=0.3.0
```

### 2. Obtenir une clé API Gemini

1. Visitez [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Connectez-vous avec votre compte Google
3. Créez une nouvelle clé API (gratuite)
4. Copiez la clé

### 3. Configurer les variables d'environnement

Ajoutez la variable `GEMINI_API_KEY` à votre fichier `.env` :

```env
# Gemini AI
GEMINI_API_KEY=votre_cle_api_gemini_ici
```

### 4. Créer la table `elements` dans Supabase

Exécutez le fichier SQL fourni dans votre dashboard Supabase :

```bash
# Fichier: db/schema_elements.sql
```

Ou copiez-collez le contenu directement dans l'éditeur SQL de Supabase.

## 🎮 Fonctionnalités

### Commande `/construire`

Permet de construire des éléments dynamiques (aliments, objets, concepts, etc.) avec l'IA :

```
/construire element_name: "Stratégie militaire avancée" element_type: "Concept/Idée"
```

**Types d'éléments disponibles :**
- 🍎 Aliment
- 🏗️ Objet manufacturé
- 🧪 Élément chimique
- 🌿 Espèce vivante
- 💎 Minéral
- 💡 Concept/Idée

### Fonctions IA disponibles

1. **`generate_element_details()`** - Génère les détails d'un élément (matériaux, coûts, effets)
2. **`generate_event_description()`** - Génère des descriptions d'événements personnalisées
3. **`suggest_economic_strategy()`** - Suggère des stratégies économiques basées sur l'état du pays
4. **`generate_random_discovery()`** - Génère des découvertes aléatoires

## 🔧 Configuration avancée

### Base de connaissances

L'IA utilise une base de connaissances intégrée contenant :
- 118 éléments chimiques
- 8,7 millions d'espèces vivantes (exemples)
- Plus de 5,000 minéraux
- Des milliers d'aliments
- Des millions d'objets manufacturés
- Concepts et œuvres

Cette base est incluse dans `utils/ai_helper.py` et peut être étendue.

### Coûts API

⚠️ **Important** : L'API Gemini a des limites gratuites. Surveillez votre utilisation :

- Tier gratuit : 60 requêtes/minute
- Tarif payant : Voir [tarification Gemini](https://ai.google.dev/pricing)

## 🐛 Dépannage

### Erreur : "GEMINI_API_KEY n'est pas configuré"

➡️ Vérifiez que la variable est bien dans votre `.env` et que le fichier est chargé.

### Erreur : "google-generativeai n'est pas installé"

```bash
pip install google-generativeai
```

### Erreur : Rate limit

➡️ L'IA a atteint sa limite de requêtes. Attendez quelques minutes ou passez à un plan payant.

### Erreur : JSON parsing failed

➡️ L'IA a retourné un format invalide. Un fallback est automatiquement appliqué.

## 📊 Structure de la base de données

La table `elements` contient :

```sql
- id: UUID (PRIMARY KEY)
- name: Nom de l'élément
- type: Type d'élément
- category: Catégorie
- description: Description générée par l'IA
- materials: Liste des matériaux requis
- cost: Coût en argent
- rarity: Rareté (commun/rare/épique/légendaire)
- time_to_build: Temps de construction
- effects: Effets sur le pays (JSON)
- creator_id: ID du créateur (REFERENCES players)
- country_id: ID du pays (REFERENCES countries)
- created_at: Date de création
- built: Statut de construction
- built_at: Date de construction
```

## 🎯 Exemples d'utilisation

### Construire un aliment
```
/construire element_name: "Fruit exotique rare" element_type: "Aliment"
```

### Construire un objet
```
/construire element_name: "Usine de production" element_type: "Objet manufacturé"
```

### Construire un concept
```
/construire element_name: "Théorie économique révolutionnaire" element_type: "Concept/Idée"
```

## ⚙️ Intégration avec les autres systèmes

- **Économie** : Les éléments coûtent des ressources et de l'argent
- **Effets** : Les éléments appliquent des effets sur l'économie, stabilité et force militaire du pays
- **Transactions** : Chaque construction est loggée dans la table `transactions`
- **Joueurs** : Les créations sont liées au créateur et au pays

## 📝 Notes

- L'IA est utilisée pour **enrichir le gameplay**, pas pour tricher
- Tous les éléments sont validés et équilibrés automatiquement
- Les fallbacks garantissent que le jeu continue même si l'IA échoue

---

**Questions ou problèmes ?** Consultez les logs dans `logs/` ou ouvrez une issue sur GitHub.

