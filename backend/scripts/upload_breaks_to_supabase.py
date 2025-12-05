#!/usr/bin/env python3
"""
Script pour uploader les vidéos de break vers Supabase Storage.

Prérequis:
    - Les vidéos doivent avoir été générées avec generate_break_videos.py
    - Les variables d'environnement SUPABASE_URL et SUPABASE_KEY doivent être définies

Usage:
    python backend/scripts/upload_breaks_to_supabase.py
"""

import sys
import os
from pathlib import Path
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv()


def main():
    """Upload toutes les vidéos de break vers Supabase Storage"""

    # Vérifier les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Erreur: Variables d'environnement manquantes")
        print("   Définissez SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY")
        print(
            "   ⚠️  Utilisez la SERVICE_ROLE_KEY (pas l'anon key) pour uploader des fichiers"
        )
        return 1

    # Chemin des vidéos générées
    videos_dir = Path(__file__).parent.parent / "break_videos"

    if not videos_dir.exists():
        print(f"❌ Erreur: Dossier {videos_dir} introuvable")
        print("   Exécutez d'abord: python backend/scripts/generate_break_videos.py")
        return 1

    # Lister les vidéos à uploader
    video_files = sorted(videos_dir.glob("break_*.mp4"))

    if not video_files:
        print(f"❌ Erreur: Aucune vidéo trouvée dans {videos_dir}")
        return 1

    print("=" * 60)
    print("UPLOAD DES VIDÉOS DE BREAK VERS SUPABASE")
    print("=" * 60)
    print(f"Nombre de vidéos: {len(video_files)}")
    print("Bucket: exercise-videos")
    print("Dossier: breaks/")
    print()

    # Initialiser le client Supabase
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connexion à Supabase établie")
    except Exception as e:
        print(f"❌ Erreur de connexion à Supabase: {e}")
        return 1

    # Uploader chaque vidéo
    success_count = 0
    uploaded_urls = {}

    for video_file in video_files:
        file_name = video_file.name
        storage_path = f"breaks/{file_name}"

        print(f"⏳ Upload {file_name}...")

        try:
            # Lire le fichier
            with open(video_file, "rb") as f:
                file_data = f.read()

            # Uploader vers Supabase Storage
            supabase.storage.from_("exercise-videos").upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": "video/mp4", "upsert": "true"},
            )

            # Générer l'URL publique
            public_url = supabase.storage.from_("exercise-videos").get_public_url(
                storage_path
            )

            file_size = video_file.stat().st_size / 1024  # KB
            print(f"✅ {file_name} uploadé: {file_size:.1f} KB")
            print(f"   URL: {public_url}")

            uploaded_urls[file_name] = public_url
            success_count += 1

        except Exception as e:
            print(f"❌ Erreur upload {file_name}: {e}")

    print()
    print("=" * 60)
    print(f"RÉSULTAT: {success_count}/{len(video_files)} vidéos uploadées")
    print("=" * 60)

    if success_count == len(video_files):
        print("✅ Toutes les vidéos ont été uploadées avec succès!")
        print()
        print("📋 URLs générées:")
        for file_name, url in uploaded_urls.items():
            duration = file_name.replace("break_", "").replace("s.mp4", "")
            print(f"  {duration}s: {url}")
        print()
        print("Prochaine étape:")
        print("  Mettre à jour backend/app/services/video_service_optimized.py")
        print("  avec ces URLs dans la constante BREAK_URLS")
        return 0
    else:
        print("⚠️ Certaines vidéos n'ont pas pu être uploadées")
        return 1


if __name__ == "__main__":
    sys.exit(main())
