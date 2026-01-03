# Guide de Migration : Ajout des Thèmes d'Exercices

## 📋 Vue d'ensemble

Cette migration ajoute le support des thèmes d'exercices (`themes`) dans le champ `metadata` de la table `exercises` pour permettre la génération de workouts par blocs thématiques.

## 🎯 Changements

### Base de données (Supabase)
- ✅ Index GIN sur `metadata->'themes'` pour recherches optimisées
- ✅ Fonction de validation des thèmes
- ✅ Trigger automatique pour valider les thèmes à l'insertion/update

### Données
- ✅ Ajout du champ `themes` dans `metadata` de chaque exercice
- ✅ Catégorisation automatique basée sur `muscles_targeted`

## 🚀 Procédure de Migration

### Étape 1 : Appliquer la migration SQL

```bash
# Depuis la racine du projet
cd backend

# Vérifier que Supabase est configuré
supabase status

# Appliquer la migration
supabase db push
```

La migration [`20260103140000_add_exercise_themes_support.sql`](../supabase/migrations/20260103140000_add_exercise_themes_support.sql) sera automatiquement appliquée.

### Étape 2 : Migrer les exercices existants

```bash
# Depuis la racine du projet
python backend/scripts/migrate_exercise_themes.py
```

Ce script va :
1. ✅ Lire le fichier `exercises.json`
2. ✅ Créer une sauvegarde `exercises.json.backup`
3. ✅ Analyser les `muscles_targeted` de chaque exercice
4. ✅ Assigner automatiquement les thèmes appropriés
5. ✅ Mettre à jour le fichier `exercises.json`
6. ✅ (Optionnel) Mettre à jour la base Supabase si configurée

### Étape 3 : Vérifier les résultats

```bash
# Vérifier le fichier exercises.json
cat backend/scripts/exercises.json | grep -A 5 "themes"

# Exemple de résultat attendu:
# "metadata": {
#     "muscles_targeted": ["chest", "triceps"],
#     "themes": ["upper_body"]
# }
```

### Étape 4 : Synchroniser avec Supabase

Si vous utilisez Supabase, resynchronisez les exercices :

```bash
# Uploader les exercices mis à jour
node backend/scripts/seed_exercises.js
```

## 📊 Mapping Automatique des Thèmes

Le script utilise le mapping suivant :

| Muscles | Thème |
|---------|-------|
| chest, shoulders, triceps, upper_back | `upper_body` |
| quadriceps, glutes, hamstrings, calves | `legs` |
| abs, core, obliques, lower_abs | `abs` |
| - | `cardio` |
| full_body, exercices multi-zones | `full_body` |

### Règles spéciales

1. **has_jump = true** → Ajoute automatiquement `cardio`
2. **3+ zones musculaires** → Ajoute `full_body`
3. **Aucun muscle identifié** → Défaut : `full_body`

## 🔍 Exemples de Catégorisation

### Avant migration

```json
{
  "name": "Push-ups",
  "metadata": {
    "muscles_targeted": ["chest", "triceps", "shoulders"]
  }
}
```

### Après migration

```json
{
  "name": "Push-ups",
  "metadata": {
    "muscles_targeted": ["chest", "triceps", "shoulders"],
    "themes": ["upper_body"]
  }
}
```

### Exercice multi-thèmes

```json
{
  "name": "Burpees",
  "has_jump": true,
  "metadata": {
    "muscles_targeted": ["full_body"],
    "themes": ["cardio", "full_body"]
  }
}
```

### Exercice complexe

```json
{
  "name": "Mountain Climbers",
  "metadata": {
    "muscles_targeted": ["core", "cardio", "shoulders"],
    "themes": ["abs", "cardio", "full_body"]
  }
}
```

## ⚠️ Validation des Thèmes

La migration crée un trigger SQL qui valide automatiquement les thèmes :

```sql
-- Thèmes autorisés
- upper_body
- legs
- cardio
- abs
- full_body

-- Si un thème invalide est inséré:
ERROR: Invalid theme: invalid_theme. Valid themes are: {upper_body,legs,cardio,abs,full_body}
```

## 🧪 Tests

Après la migration, lancez les tests :

```bash
# Tests unitaires
pytest backend/tests/test_block_generation.py -v

# Tests d'intégration (si configurés)
pytest backend/tests/ -v
```

## 🔄 Rollback (en cas de problème)

### Restaurer exercises.json

```bash
# La sauvegarde est automatiquement créée
cp backend/scripts/exercises.json.backup backend/scripts/exercises.json
```

### Rollback Supabase

```bash
# Supprimer le trigger et l'index
supabase db reset
# Puis ré-appliquer les migrations précédentes
supabase db push
```

Ou manuellement en SQL :

```sql
-- Supprimer le trigger
DROP TRIGGER IF EXISTS validate_themes_trigger ON exercises;
DROP FUNCTION IF EXISTS validate_exercise_themes();

-- Supprimer l'index
DROP INDEX IF EXISTS idx_exercises_themes;

-- Nettoyer le champ themes (optionnel)
UPDATE exercises
SET metadata = metadata - 'themes';
```

## 📋 Checklist de Migration

- [ ] Sauvegarder la base de données
- [ ] Appliquer la migration SQL (`supabase db push`)
- [ ] Exécuter le script Python (`python backend/scripts/migrate_exercise_themes.py`)
- [ ] Vérifier les résultats (fichier exercises.json)
- [ ] Synchroniser avec Supabase (`node backend/scripts/seed_exercises.js`)
- [ ] Lancer les tests (`pytest backend/tests/test_block_generation.py`)
- [ ] Vérifier en production (environnement de staging)

## 🐛 Dépannage

### Erreur : "Module supabase not found"

```bash
pip install supabase python-dotenv
```

### Erreur : "SUPABASE_URL not configured"

Créer un fichier `.env` dans `backend/` :

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Erreur : "Invalid theme"

Les thèmes doivent être exactement l'un de :
- `upper_body`
- `legs`
- `cardio`
- `abs`
- `full_body`

Vérifier la casse (minuscules) et les underscores.

### Exercices sans thèmes après migration

Le script assigne `full_body` par défaut. Vous pouvez manuellement corriger :

```python
# Dans exercises.json
{
  "name": "Mon Exercice",
  "metadata": {
    "themes": ["abs", "cardio"]  # Corriger manuellement
  }
}
```

Puis re-synchroniser avec Supabase.

## 📚 Ressources

- [Migration SQL](../supabase/migrations/20260103140000_add_exercise_themes_support.sql)
- [Script de migration](./migrate_exercise_themes.py)
- [Documentation](../../docs/workout_block_generation.md)
- [Tests](../tests/test_block_generation.py)

## ✅ Validation Finale

Une fois la migration terminée, vérifiez :

```bash
# 1. Tous les exercices ont des thèmes
python -c "
import json
with open('backend/scripts/exercises.json') as f:
    exercises = json.load(f)
    no_themes = [ex['name'] for ex in exercises if not ex.get('metadata', {}).get('themes')]
    print(f'Exercices sans thèmes: {len(no_themes)}')
    if no_themes:
        print(no_themes)
"

# 2. Tester la génération par blocs
pytest backend/tests/test_block_generation.py::test_filter_exercises_by_theme -v
```

## 🎉 Résultat Attendu

```
📊 STATISTIQUES DE MIGRATION
============================================================
Total exercices       : 47
Exercices mis à jour  : 47
Avaient déjà themes   : 0

Distribution des thèmes:
  abs             :  12 ( 25.5%)
  cardio          :  15 ( 31.9%)
  full_body       :   8 ( 17.0%)
  legs            :  18 ( 38.3%)
  upper_body      :  14 ( 29.8%)
============================================================
```

La somme peut dépasser 100% car les exercices peuvent avoir plusieurs thèmes.
