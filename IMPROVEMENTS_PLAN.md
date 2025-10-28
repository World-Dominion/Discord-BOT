# 📋 Plan d'Améliorations World Dominion

## ✅ À faire immédiatement (14 tâches)

### 🐛 BUGS CRITIQUES

1. **`/attaquer` ne marche pas** - À vérifier la logique de guerre
2. **`/travail` pas de cooldown** - Argent infini exploit
3. **`/espionner` inutile** - Pas de vol de ressources

### ✨ AMÉLIORATIONS UX

4. **`/give` trop complexe** - Utiliser @mention Discord au lieu d'IDs
5. **`/construire` répétitif** - IA génère toujours la même chose
6. **`/profil` manque inventaire** - Ajouter inventaire joueur
7. **`/banque` manque de détails** - Enrichir avec IA
8. **`/classement` à supprimer** - Option retirée
9. **`/embargo` besoin menu** - Ajouter select dropdown
10. **`/lock-pays` besoin menu** - Ajouter select dropdown

### 🤖 AMÉLIORATIONS IA

11. **Nouveau prompt IA** - ✅ FAIT (`utils/ai_helper_gemini.py`)
12. **Site web - Gestion éléments** - À implémenter
13. **Site web - IA Gemini** - À intégrer  
14. **Site web - Interface Discord** - Rendre toutes commandes accessibles

---

## 🚀 PROCHAINES ÉTAPES

### Phase 1 : Corrections critiques (URGENT)
- Corriger `/travail` (cooldown + taxe)
- Corriger `/attaquer` 
- Améliorer `/espionner` avec vol

### Phase 2 : Améliorations UX
- Simplifier `/give`
- Réparer `/construire` avec nouvelle IA
- Ajouter inventaire à `/profil`
- Enrichir `/banque`
- Supprimer `/classement`
- Ajouter menus pour `/embargo` et `/lock-pays`

### Phase 3 : Site Web
- Intégrer gestion éléments
- Ajouter IA Gemini interface
- Créer interface toutes commandes

---

## 📝 NOTES

- Le nouveau `utils/ai_helper_gemini.py` est prêt avec le prompt système complet
- Besoin de migrer `cogs/economy.py` pour utiliser la nouvelle IA
- Les améliorations web nécessitent Flask + Socket.IO

**Souhaitez-vous commencer par les bugs critiques ou par une refonte complète ?**

