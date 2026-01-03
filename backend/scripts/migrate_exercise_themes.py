"""
Script de migration pour ajouter les thèmes aux exercices existants.

Ce script analyse les muscles_targeted de chaque exercice et assigne
automatiquement les thèmes appropriés.

Usage:
    python backend/scripts/migrate_exercise_themes.py
"""

import json
import os
from pathlib import Path
from typing import List

# Mapping des muscles vers les thèmes
MUSCLE_TO_THEME_MAPPING = {
    # UPPER_BODY
    "chest": "upper_body",
    "shoulders": "upper_body",
    "triceps": "upper_body",
    "upper_back": "upper_body",
    "upper_chest": "upper_body",
    # LEGS
    "quadriceps": "legs",
    "glutes": "legs",
    "hamstrings": "legs",
    "calves": "legs",
    "hip_flexors": "legs",
    "adductors": "legs",
    "hip_stabilizers": "legs",
    # ABS
    "abs": "abs",
    "core": "abs",
    "obliques": "abs",
    "lower_abs": "abs",
    # CARDIO (basé sur le contexte)
    "cardio": "cardio",
    # FULL_BODY
    "full_body": "full_body",
    "lower_back": "full_body",  # Souvent travaillé avec tout le corps
}


def determine_themes_from_muscles(
    muscles_targeted: List[str], has_jump: bool = False
) -> List[str]:
    """
    Détermine les thèmes d'un exercice basé sur ses muscles ciblés.

    Args:
        muscles_targeted: Liste des muscles ciblés
        has_jump: Si l'exercice contient des sauts (=> CARDIO)

    Returns:
        Liste des thèmes appropriés
    """
    if not muscles_targeted:
        return ["full_body"]

    themes = set()

    # Mapper chaque muscle à un thème
    for muscle in muscles_targeted:
        muscle_lower = muscle.lower()
        if muscle_lower in MUSCLE_TO_THEME_MAPPING:
            themes.add(MUSCLE_TO_THEME_MAPPING[muscle_lower])

    # Si l'exercice a des sauts, ajouter CARDIO
    if has_jump:
        themes.add("cardio")

    # Si plusieurs thèmes ou aucun thème clair, ajouter FULL_BODY
    if not themes:
        themes.add("full_body")
    elif len(themes) >= 3:
        # Si l'exercice sollicite 3+ zones différentes, c'est du FULL_BODY
        themes.add("full_body")

    # Si contient "full_body" dans muscles_targeted
    if "full_body" in [m.lower() for m in muscles_targeted]:
        themes.add("full_body")

    return sorted(list(themes))


def migrate_exercises_json():
    """
    Migre le fichier exercises.json pour ajouter les thèmes.
    """
    exercises_file = Path(__file__).parent / "exercises.json"

    if not exercises_file.exists():
        print(f"❌ Fichier non trouvé: {exercises_file}")
        return

    print(f"📖 Lecture de {exercises_file}")
    with open(exercises_file, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    print(f"✅ {len(exercises)} exercices chargés")

    # Statistiques
    stats = {
        "total": len(exercises),
        "updated": 0,
        "already_had_themes": 0,
        "themes_distribution": {
            "upper_body": 0,
            "legs": 0,
            "cardio": 0,
            "abs": 0,
            "full_body": 0,
        },
    }

    # Traiter chaque exercice
    for exercise in exercises:
        metadata = exercise.get("metadata", {})

        # Si l'exercice a déjà des thèmes, les garder
        if "themes" in metadata and metadata["themes"]:
            stats["already_had_themes"] += 1
            existing_themes = metadata["themes"]
            print(f"  ℹ️  {exercise['name']}: thèmes existants {existing_themes}")
        else:
            # Déterminer les thèmes automatiquement
            muscles_targeted = metadata.get("muscles_targeted", [])
            has_jump = exercise.get("has_jump", False)

            themes = determine_themes_from_muscles(muscles_targeted, has_jump)

            # Ajouter les thèmes au metadata
            if "metadata" not in exercise:
                exercise["metadata"] = {}
            exercise["metadata"]["themes"] = themes

            stats["updated"] += 1
            print(f"  ✅ {exercise['name']}: {muscles_targeted} → {themes}")

        # Compter les thèmes
        for theme in metadata.get("themes", []):
            if theme in stats["themes_distribution"]:
                stats["themes_distribution"][theme] += 1

    # Sauvegarder le fichier mis à jour
    backup_file = exercises_file.with_suffix(".json.backup")
    print(f"\n💾 Sauvegarde de l'original vers {backup_file}")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=4)

    print(f"💾 Écriture du fichier mis à jour vers {exercises_file}")
    with open(exercises_file, "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=4)

    # Afficher les statistiques
    print("\n" + "=" * 60)
    print("📊 STATISTIQUES DE MIGRATION")
    print("=" * 60)
    print(f"Total exercices       : {stats['total']}")
    print(f"Exercices mis à jour  : {stats['updated']}")
    print(f"Avaient déjà themes   : {stats['already_had_themes']}")
    print("\nDistribution des thèmes:")
    for theme, count in sorted(stats["themes_distribution"].items()):
        percentage = (count / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {theme:15} : {count:3} ({percentage:5.1f}%)")
    print("=" * 60)


def migrate_supabase_database():
    """
    Migre les exercices dans Supabase pour ajouter les thèmes.

    Note: Nécessite la configuration Supabase et les credentials.
    """
    try:
        from supabase import create_client
        from dotenv import load_dotenv

        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            print("⚠️  SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY non configurés")
            print(
                "   Migration Supabase ignorée (utilisez migrate_exercises_json uniquement)"
            )
            return

        print("\n🔗 Connexion à Supabase...")
        supabase = create_client(supabase_url, supabase_key)

        # Récupérer tous les exercices
        response = supabase.table("exercises").select("*").execute()
        exercises = response.data

        print(f"✅ {len(exercises)} exercices récupérés de Supabase")

        updated_count = 0

        for exercise in exercises:
            metadata = exercise.get("metadata", {})

            # Si pas de thèmes, les générer
            if "themes" not in metadata or not metadata["themes"]:
                muscles_targeted = metadata.get("muscles_targeted", [])
                has_jump = exercise.get("has_jump", False)

                themes = determine_themes_from_muscles(muscles_targeted, has_jump)

                # Mettre à jour le metadata
                metadata["themes"] = themes

                # Mettre à jour dans Supabase
                supabase.table("exercises").update({"metadata": metadata}).eq(
                    "id", exercise["id"]
                ).execute()

                print(f"  ✅ {exercise['name']}: thèmes ajoutés {themes}")
                updated_count += 1

        print(f"\n✅ {updated_count} exercices mis à jour dans Supabase")

    except ImportError:
        print("⚠️  Module supabase non installé. Installation:")
        print("   pip install supabase python-dotenv")
    except Exception as e:
        print(f"❌ Erreur lors de la migration Supabase: {e}")


if __name__ == "__main__":
    print("🚀 MIGRATION DES THÈMES D'EXERCICES")
    print("=" * 60)

    # 1. Migrer le fichier JSON local
    print("\n📝 Étape 1: Migration du fichier exercises.json")
    migrate_exercises_json()

    # 2. Migrer la base Supabase (optionnel)
    print("\n📝 Étape 2: Migration de la base Supabase (optionnel)")
    migrate_supabase_database()

    print("\n✨ Migration terminée !")
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifier le fichier exercises.json mis à jour")
    print("   2. Vérifier exercises.json.backup en cas de problème")
    print("   3. Appliquer la migration SQL: supabase db push")
    print("   4. Lancer les tests: pytest backend/tests/test_block_generation.py")
