"""
Configuration des URLs des vidéos de break sur Supabase Storage.

Ces URLs pointent vers les vidéos de break pré-générées et uploadées sur Supabase.
Pour régénérer ces vidéos, exécutez:
    1. python backend/scripts/generate_break_videos.py
    2. python backend/scripts/upload_breaks_to_supabase.py
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def _get_supabase_project_id() -> str:
    """Récupère le PROJECT_ID depuis les variables d'environnement"""
    project_id = os.getenv("SUPABASE_PROJECT_ID")
    if not project_id:
        raise ValueError(
            "Variable d'environnement SUPABASE_PROJECT_ID non définie. "
            "Ajoutez-la dans votre fichier .env"
        )
    return project_id


def _build_break_video_urls() -> dict:
    """Construit les URLs des vidéos de break depuis Supabase"""
    project_id = _get_supabase_project_id()
    base_url = f"https://{project_id}.supabase.co/storage/v1/object/public/exercise-videos/breaks"
    
    return {
        5: f"{base_url}/break_5s.mp4",
        10: f"{base_url}/break_10s.mp4",
        15: f"{base_url}/break_15s.mp4",
        20: f"{base_url}/break_20s.mp4",
        25: f"{base_url}/break_25s.mp4",
        30: f"{base_url}/break_30s.mp4",
        35: f"{base_url}/break_35s.mp4",
        40: f"{base_url}/break_40s.mp4",
    }


# Initialiser les URLs au chargement du module
BREAK_VIDEO_URLS = _build_break_video_urls()


def get_break_video_url(duration: int) -> str:
    """
    Retourne l'URL Supabase de la vidéo de break pour une durée donnée.
    
    Args:
        duration: Durée du break en secondes
        
    Returns:
        URL de la vidéo de break sur Supabase
        
    Raises:
        ValueError: Si la durée n'est pas supportée
    """
    if duration not in BREAK_VIDEO_URLS:
        raise ValueError(
            f"Durée de break {duration}s non supportée. "
            f"Durées disponibles: {list(BREAK_VIDEO_URLS.keys())}"
        )
    
    return BREAK_VIDEO_URLS[duration]