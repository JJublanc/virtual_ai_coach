#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes de vidéo qui causent des freezes.

Ce script analyse:
1. Les métadonnées des vidéos sources (résolution, framerate, codec)
2. La distribution des keyframes (I-frames)
3. Les incohérences entre les segments
4. Les problèmes potentiels de streaming

Usage:
    python diagnose_video_issues.py [workout_id]
    python diagnose_video_issues.py --check-sources
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


def run_ffprobe(video_path: str) -> Dict[str, Any]:
    """Exécute ffprobe sur une vidéo et retourne les métadonnées."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur ffprobe pour {video_path}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Erreur parsing JSON pour {video_path}: {e}")
        return {}


def analyze_keyframes(video_path: str) -> Dict[str, Any]:
    """Analyse la distribution des keyframes dans une vidéo."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "v:0",
        "-show_entries",
        "frame=pkt_pts_time,pict_type",
        "-of",
        "json",
        video_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        frames = data.get("frames", [])
        i_frames = [f for f in frames if f.get("pict_type") == "I"]

        # Calculer les intervalles entre les keyframes
        intervals = []
        for i in range(1, len(i_frames)):
            prev_time = float(i_frames[i - 1].get("pkt_pts_time", 0))
            curr_time = float(i_frames[i].get("pkt_pts_time", 0))
            intervals.append(curr_time - prev_time)

        return {
            "total_frames": len(frames),
            "i_frames_count": len(i_frames),
            "i_frame_interval_avg": sum(intervals) / len(intervals) if intervals else 0,
            "i_frame_interval_min": min(intervals) if intervals else 0,
            "i_frame_interval_max": max(intervals) if intervals else 0,
            "first_frame_is_keyframe": frames[0].get("pict_type") == "I"
            if frames
            else False,
        }
    except Exception as e:
        print(f"⚠️  Impossible d'analyser les keyframes pour {video_path}: {e}")
        return {}


def check_video_compatibility(videos: List[Path]) -> Dict[str, Any]:
    """Vérifie la compatibilité entre plusieurs vidéos."""
    print("\n📊 Analyse de compatibilité des vidéos sources...\n")

    video_info = []
    issues = []

    for video_path in videos:
        if not video_path.exists():
            print(f"⚠️  Vidéo non trouvée: {video_path}")
            continue

        print(f"🔍 Analyse: {video_path.name}")

        metadata = run_ffprobe(str(video_path))
        if not metadata:
            continue

        video_stream = next(
            (s for s in metadata.get("streams", []) if s["codec_type"] == "video"), None
        )

        if not video_stream:
            print("   ❌ Pas de stream vidéo trouvé")
            continue

        info = {
            "path": str(video_path),
            "name": video_path.name,
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")),
            "pix_fmt": video_stream.get("pix_fmt"),
            "duration": float(metadata.get("format", {}).get("duration", 0)),
            "bitrate": int(metadata.get("format", {}).get("bit_rate", 0)),
        }

        # Analyse des keyframes
        keyframe_info = analyze_keyframes(str(video_path))
        info.update(keyframe_info)

        video_info.append(info)

        # Affichage
        print(f"   ✓ Résolution: {info['width']}x{info['height']}")
        print(f"   ✓ Codec: {info['codec']}, Pixel Format: {info['pix_fmt']}")
        print(f"   ✓ FPS: {info['fps']:.2f}")
        print(f"   ✓ Durée: {info['duration']:.2f}s")
        print(
            f"   ✓ Keyframes: {info.get('i_frames_count', 0)} (interval moyen: {info.get('i_frame_interval_avg', 0):.2f}s)"
        )
        print(
            f"   ✓ Premier frame est keyframe: {info.get('first_frame_is_keyframe', False)}"
        )
        print()

    # Vérification de cohérence
    if len(video_info) > 1:
        print("\n🔍 Vérification de cohérence...\n")

        reference = video_info[0]

        for video in video_info[1:]:
            # Résolution différente
            if (
                video["width"] != reference["width"]
                or video["height"] != reference["height"]
            ):
                issues.append(
                    {
                        "type": "resolution_mismatch",
                        "severity": "high",
                        "video": video["name"],
                        "message": f"Résolution différente: {video['width']}x{video['height']} vs {reference['width']}x{reference['height']}",
                    }
                )

            # FPS différent
            if abs(video["fps"] - reference["fps"]) > 0.1:
                issues.append(
                    {
                        "type": "fps_mismatch",
                        "severity": "medium",
                        "video": video["name"],
                        "message": f"FPS différent: {video['fps']:.2f} vs {reference['fps']:.2f}",
                    }
                )

            # Codec différent
            if video["codec"] != reference["codec"]:
                issues.append(
                    {
                        "type": "codec_mismatch",
                        "severity": "low",
                        "video": video["name"],
                        "message": f"Codec différent: {video['codec']} vs {reference['codec']}",
                    }
                )

            # Pixel format différent
            if video["pix_fmt"] != reference["pix_fmt"]:
                issues.append(
                    {
                        "type": "pixfmt_mismatch",
                        "severity": "medium",
                        "video": video["name"],
                        "message": f"Pixel format différent: {video['pix_fmt']} vs {reference['pix_fmt']}",
                    }
                )

            # Premier frame n'est pas un keyframe
            if not video.get("first_frame_is_keyframe", False):
                issues.append(
                    {
                        "type": "no_initial_keyframe",
                        "severity": "high",
                        "video": video["name"],
                        "message": "Le premier frame n'est pas un keyframe (peut causer des freezes lors de la concaténation)",
                    }
                )

            # Keyframe interval trop grand
            if video.get("i_frame_interval_avg", 0) > 5:
                issues.append(
                    {
                        "type": "large_keyframe_interval",
                        "severity": "medium",
                        "video": video["name"],
                        "message": f"Interval entre keyframes trop grand: {video.get('i_frame_interval_avg', 0):.2f}s (peut causer des problèmes de seeking)",
                    }
                )

    return {"videos": video_info, "issues": issues}


def print_diagnostic_report(result: Dict[str, Any]):
    """Affiche un rapport de diagnostic."""
    issues = result.get("issues", [])

    if not issues:
        print("✅ Aucun problème détecté!\n")
        return

    print(f"\n⚠️  {len(issues)} problème(s) détecté(s):\n")

    # Grouper par sévérité
    high = [i for i in issues if i["severity"] == "high"]
    medium = [i for i in issues if i["severity"] == "medium"]
    low = [i for i in issues if i["severity"] == "low"]

    if high:
        print("🔴 Problèmes critiques (HAUTE priorité):")
        for issue in high:
            print(f"   • [{issue['video']}] {issue['message']}")
        print()

    if medium:
        print("🟡 Problèmes modérés (MOYENNE priorité):")
        for issue in medium:
            print(f"   • [{issue['video']}] {issue['message']}")
        print()

    if low:
        print("🟢 Problèmes mineurs (BASSE priorité):")
        for issue in low:
            print(f"   • [{issue['video']}] {issue['message']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic des vidéos pour identifier les causes de freeze"
    )
    parser.add_argument(
        "--check-sources",
        action="store_true",
        help="Vérifier les vidéos sources dans /tmp/exercise_videos",
    )
    parser.add_argument(
        "--video-dir", type=str, help="Répertoire contenant les vidéos à analyser"
    )
    parser.add_argument("videos", nargs="*", help="Vidéos spécifiques à analyser")

    args = parser.parse_args()

    videos_to_check = []

    if args.check_sources:
        video_dir = Path("/tmp/exercise_videos")
        if video_dir.exists():
            videos_to_check = list(video_dir.glob("*.mp4"))
            print(f"🔍 Analyse de {len(videos_to_check)} vidéos dans {video_dir}\n")
        else:
            print(f"❌ Répertoire non trouvé: {video_dir}")
            return

    elif args.video_dir:
        video_dir = Path(args.video_dir)
        if video_dir.exists():
            videos_to_check = list(video_dir.glob("*.mp4"))
            print(f"🔍 Analyse de {len(videos_to_check)} vidéos dans {video_dir}\n")
        else:
            print(f"❌ Répertoire non trouvé: {video_dir}")
            return

    elif args.videos:
        videos_to_check = [Path(v) for v in args.videos]

    else:
        print(
            "❌ Veuillez spécifier --check-sources, --video-dir, ou des vidéos spécifiques"
        )
        parser.print_help()
        return

    if not videos_to_check:
        print("❌ Aucune vidéo à analyser")
        return

    result = check_video_compatibility(videos_to_check)
    print_diagnostic_report(result)

    # Recommandations
    if result.get("issues"):
        print("\n💡 Recommandations:\n")

        has_keyframe_issues = any(
            i["type"] in ["no_initial_keyframe", "large_keyframe_interval"]
            for i in result["issues"]
        )
        has_format_issues = any(
            i["type"] in ["resolution_mismatch", "fps_mismatch", "pixfmt_mismatch"]
            for i in result["issues"]
        )

        if has_keyframe_issues:
            print("1. Ajouter des keyframes réguliers lors de l'encodage:")
            print("   ffmpeg -i input.mp4 -c:v libx264 -g 30 -keyint_min 30 output.mp4")
            print()

        if has_format_issues:
            print("2. Normaliser toutes les vidéos au même format:")
            print(
                "   ffmpeg -i input.mp4 -vf scale=1280:720 -r 30 -pix_fmt yuv420p output.mp4"
            )
            print()

        print(
            "3. Utiliser stream copy au lieu de réencoder si les formats sont compatibles:"
        )
        print("   Modifier workout_video_generator.py ligne 167: use_stream_copy=True")
        print()


if __name__ == "__main__":
    main()
