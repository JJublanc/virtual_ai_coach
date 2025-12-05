#!/usr/bin/env python3
"""
Script pour générer les vidéos de break localement.
Ces vidéos seront ensuite uploadées sur Supabase.

Usage:
    python backend/scripts/generate_break_videos.py
"""

import sys
from pathlib import Path
from backend.app.services.video_service import VideoService

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Génère toutes les vidéos de break nécessaires"""

    # Durées de break à générer (en secondes)
    BREAK_DURATIONS = [5, 10, 15, 20, 25, 30, 35, 40]

    # Créer le dossier de sortie
    output_dir = Path(__file__).parent.parent / "break_videos"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("GÉNÉRATION DES VIDÉOS DE BREAK")
    print("=" * 60)
    print(f"Dossier de sortie: {output_dir}")
    print(f"Nombre de vidéos: {len(BREAK_DURATIONS)}")
    print()

    # Initialiser le service vidéo
    project_root = Path(__file__).parent.parent.parent
    video_service = VideoService(project_root=project_root)

    # Générer chaque vidéo de break
    success_count = 0
    for duration in BREAK_DURATIONS:
        output_path = output_dir / f"break_{duration}s.mp4"

        print(f"⏳ Génération break {duration}s...")

        if video_service.generate_break_video(duration, output_path):
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"✅ Break {duration}s généré: {file_size:.1f} KB")
            success_count += 1
        else:
            print(f"❌ Échec génération break {duration}s")

    print()
    print("=" * 60)
    print(f"RÉSULTAT: {success_count}/{len(BREAK_DURATIONS)} vidéos générées")
    print("=" * 60)

    if success_count == len(BREAK_DURATIONS):
        print("✅ Toutes les vidéos ont été générées avec succès!")
        print(f"📁 Emplacement: {output_dir}")
        print()
        print("Prochaine étape:")
        print("  python backend/scripts/upload_breaks_to_supabase.py")
        return 0
    else:
        print("⚠️ Certaines vidéos n'ont pas pu être générées")
        return 1


if __name__ == "__main__":
    sys.exit(main())
