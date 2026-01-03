"""
Script pour vérifier que toutes les vidéos des exercices sont disponibles sur Supabase Storage.

Usage:
    python backend/scripts/verify_exercise_videos.py

    # Avec correction automatique (marque les exercices sans vidéo)
    python backend/scripts/verify_exercise_videos.py --fix
"""

import sys
import argparse
import requests
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

# Ajouter le chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ruff: noqa: E402
from app.api.exercises import load_exercises
from app.models.exercise import Exercise

# Charger les variables d'environnement
load_dotenv()


def check_video_exists(video_url: str) -> bool:
    """
    Vérifie si une vidéo existe sur Supabase Storage.

    Args:
        video_url: URL de la vidéo Supabase

    Returns:
        True si la vidéo existe, False sinon
    """
    try:
        # Faire une requête HEAD pour vérifier l'existence sans télécharger
        response = requests.head(video_url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except Exception as e:
        print(f"      Erreur lors de la vérification: {e}")
        return False


def verify_all_exercises(fix: bool = False) -> Tuple[List[Exercise], List[Exercise]]:
    """
    Vérifie tous les exercices et retourne ceux avec/sans vidéo.

    Args:
        fix: Si True, affiche les commandes pour corriger

    Returns:
        Tuple (exercises_ok, exercises_missing)
    """
    print("🔍 Chargement des exercices depuis Supabase...")
    exercises = load_exercises()
    print(f"✅ {len(exercises)} exercices chargés\n")

    print("📹 Vérification des vidéos sur Supabase Storage...")
    print("=" * 70)

    exercises_ok = []
    exercises_missing = []

    for i, exercise in enumerate(exercises, 1):
        status_prefix = f"[{i:2}/{len(exercises)}]"

        # Vérifier si la vidéo existe
        video_exists = check_video_exists(exercise.video_url)

        if video_exists:
            exercises_ok.append(exercise)
            print(f"  ✅ {status_prefix} {exercise.name:40} - Vidéo OK")
        else:
            exercises_missing.append(exercise)
            print(f"  ❌ {status_prefix} {exercise.name:40} - VIDÉO MANQUANTE")
            print(f"      URL: {exercise.video_url}")

    return exercises_ok, exercises_missing


def display_summary(exercises_ok: List[Exercise], exercises_missing: List[Exercise]):
    """Affiche un résumé des résultats."""
    total = len(exercises_ok) + len(exercises_missing)

    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 70)
    print(f"Total exercices        : {total}")
    print(
        f"✅ Vidéos disponibles  : {len(exercises_ok)} ({len(exercises_ok)/total*100:.1f}%)"
    )
    print(
        f"❌ Vidéos manquantes   : {len(exercises_missing)} ({len(exercises_missing)/total*100:.1f}%)"
    )

    if exercises_missing:
        print("\n⚠️  EXERCICES AVEC VIDÉOS MANQUANTES:")
        print("-" * 70)
        for ex in exercises_missing:
            print(f"  - {ex.name}")
            print(f"    ID: {ex.id}")
            print(f"    URL: {ex.video_url}")
            print(f"    Difficulté: {ex.difficulty.value}")
            if ex.metadata and ex.metadata.themes:
                print(f"    Thèmes: {', '.join([t.value for t in ex.metadata.themes])}")
            print()


def generate_fix_suggestions(exercises_missing: List[Exercise]):
    """Génère des suggestions pour corriger les problèmes."""
    if not exercises_missing:
        return

    print("\n" + "=" * 70)
    print("🔧 SUGGESTIONS DE CORRECTION")
    print("=" * 70)

    print("\nOption 1 : Uploader les vidéos manquantes")
    print("-" * 70)
    print("Utilisez le script d'upload pour ajouter les vidéos manquantes :")
    print("  node backend/scripts/upload_single_video.js <chemin_video> <nom_exercice>")
    print()

    print("Option 2 : Désactiver temporairement ces exercices")
    print("-" * 70)
    print("Vous pouvez marquer ces exercices comme 'premium' pour les exclure :")
    print(
        "  Modifier dans Supabase : UPDATE exercises SET access_tier = 'premium' WHERE id IN ("
    )
    for i, ex in enumerate(exercises_missing):
        print(f"    '{ex.id}'{', ' if i < len(exercises_missing) - 1 else ''}")
    print("  );")
    print()

    print("Option 3 : Supprimer ces exercices de la base")
    print("-" * 70)
    print("⚠️  ATTENTION : Cette action est irréversible !")
    print("  DELETE FROM exercises WHERE id IN (")
    for i, ex in enumerate(exercises_missing):
        print(f"    '{ex.id}'{', ' if i < len(exercises_missing) - 1 else ''}")
    print("  );")
    print()

    print("Option 4 : Filtrer automatiquement lors de la génération")
    print("-" * 70)
    print("Modifier workout_generator.py pour exclure les exercices sans vidéo valide.")


def create_validation_function():
    """Crée une fonction de validation pour workout_generator.py."""
    print("\n" + "=" * 70)
    print("📝 FONCTION DE VALIDATION À AJOUTER")
    print("=" * 70)

    validation_code = '''
# À ajouter dans workout_generator.py

def validate_exercise_has_video(exercise: Exercise) -> bool:
    """
    Vérifie si un exercice a une vidéo disponible.

    Args:
        exercise: L'exercice à vérifier

    Returns:
        True si la vidéo existe, False sinon
    """
    try:
        import requests
        response = requests.head(exercise.video_url, timeout=2)
        return response.status_code == 200
    except:
        return False


def filter_exercises_with_videos(exercises: List[Exercise]) -> List[Exercise]:
    """
    Filtre les exercices pour ne garder que ceux avec vidéo disponible.

    Args:
        exercises: Liste d'exercices

    Returns:
        Liste d'exercices avec vidéos valides
    """
    return [ex for ex in exercises if validate_exercise_has_video(ex)]
'''

    print(validation_code)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Vérifie que toutes les vidéos des exercices sont disponibles"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Affiche les suggestions de correction"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Exporte la liste des exercices sans vidéo dans un fichier",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🎬 VÉRIFICATION DES VIDÉOS D'EXERCICES")
    print("=" * 70)
    print()

    # Vérifier les exercices
    exercises_ok, exercises_missing = verify_all_exercises(args.fix)

    # Afficher le résumé
    display_summary(exercises_ok, exercises_missing)

    # Générer les suggestions si demandé
    if args.fix and exercises_missing:
        generate_fix_suggestions(exercises_missing)
        create_validation_function()

    # Exporter si demandé
    if args.export and exercises_missing:
        import json

        export_data = [
            {
                "id": str(ex.id),
                "name": ex.name,
                "video_url": ex.video_url,
                "difficulty": ex.difficulty.value,
                "themes": [t.value for t in ex.metadata.themes]
                if ex.metadata and ex.metadata.themes
                else [],
            }
            for ex in exercises_missing
        ]

        with open(args.export, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n💾 Liste exportée vers : {args.export}")

    # Code de sortie
    if exercises_missing:
        print(
            "\n⚠️  Des vidéos sont manquantes. Utilisez --fix pour voir les solutions."
        )
        return 1
    else:
        print("\n✅ Toutes les vidéos sont disponibles !")
        return 0


if __name__ == "__main__":
    sys.exit(main())
