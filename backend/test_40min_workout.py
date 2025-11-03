#!/usr/bin/env python3
"""
Test rapide spécifique pour un workout de 40 minutes.
Script simplifié pour mesurer les performances actuelles avec sauvegarde automatique.
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(str(Path(__file__).parent))

# Import après modification du sys.path (nécessaire pour les modules locaux)
# ruff: noqa: E402
from benchmark_streaming_performance import StreamingPerformanceBenchmark


def get_git_info():
    """Récupère les informations Git du projet"""
    try:
        # Obtenir le hash du commit actuel
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent.parent, text=True
        ).strip()

        # Obtenir le hash court
        commit_short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent.parent,
            text=True,
        ).strip()

        # Obtenir la branche actuelle
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=Path(__file__).parent.parent,
            text=True,
        ).strip()

        # Vérifier s'il y a des modifications non commitées
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).parent.parent,
            text=True,
        ).strip()

        has_uncommitted = len(status) > 0

        return {
            "commit_hash": commit_hash,
            "commit_short": commit_short,
            "branch": branch,
            "has_uncommitted_changes": has_uncommitted,
            "status": status if has_uncommitted else None,
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": f"Impossible de récupérer les infos Git: {e}",
            "commit_hash": "unknown",
            "commit_short": "unknown",
            "branch": "unknown",
            "has_uncommitted_changes": False,
        }


def analyze_streaming_results(result):
    """Analyse les résultats du streaming progressif"""
    if not result or not result.get("success"):
        return {
            "rating": "failed",
            "description": "Test échoué",
            "wait_time_seconds": 0,
            "improvement": "N/A",
        }

    # Temps d'attente utilisateur = temps jusqu'au premier byte
    user_wait_time = result["times"]["time_to_first_byte_s"]

    if user_wait_time < 1:  # Moins d'1 seconde
        ux_rating = "excellent"
        ux_description = "Streaming progressif optimal - lecture quasi-immédiate"
    elif user_wait_time < 5:  # Moins de 5 secondes
        ux_rating = "very_good"
        ux_description = "Streaming progressif très efficace"
    elif user_wait_time < 10:  # Moins de 10 secondes
        ux_rating = "good"
        ux_description = "Streaming progressif efficace"
    else:
        ux_rating = "needs_improvement"
        ux_description = "Streaming progressif à optimiser"

    return {
        "rating": ux_rating,
        "description": ux_description,
        "wait_time_seconds": user_wait_time,
        "ttfb_ms": result["performance_metrics"]["ttfb_ms"],
        "playback_ready_ms": result["performance_metrics"]["playback_ready_ms"],
        "improvement_factor": result["comparison"]["improvement_factor"],
        "improvement_percentage": result["comparison"]["improvement_percentage"],
    }


async def main():
    """Test spécifique pour 40 minutes avec la nouvelle approche streaming progressif"""
    test_start_time = datetime.now()

    print("🚀 Test de performance STREAMING PROGRESSIF - Workout 40 minutes")
    print("=" * 70)
    print(f"📅 Démarré le: {test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Test de la Phase 1 : Streaming Progressif Immédiat")

    # Récupérer les infos Git
    print("\n🔍 Récupération des informations Git...")
    git_info = get_git_info()
    if "error" not in git_info:
        print(f"📝 Commit: {git_info['commit_short']} ({git_info['branch']})")
        if git_info["has_uncommitted_changes"]:
            print("⚠️ Modifications non commitées détectées")
    else:
        print(f"⚠️ {git_info['error']}")

    print("\n🚀 Lancement du benchmark streaming progressif...")
    benchmark = StreamingPerformanceBenchmark()

    start_time = time.time()
    result = await benchmark.benchmark_streaming_approach(40)
    total_time = time.time() - start_time

    if result and result.get("success"):
        print("\n✅ Test streaming progressif terminé avec succès!")
        print("=" * 50)

        # Métriques clés du streaming progressif
        ttfb = result["times"]["time_to_first_byte_s"]
        playback_time = result["times"]["time_to_playback_s"]
        improvement = result["comparison"]["improvement_percentage"]

        print(f"⚡ Temps jusqu'au premier byte: {ttfb:.3f}s")
        print(f"▶️ Temps jusqu'à lecture possible: {playback_time:.3f}s")
        print(f"📈 Amélioration vs baseline: {improvement:.1f}%")
        print(
            f"🎯 Facteur d'amélioration: {result['comparison']['improvement_factor']:.1f}x"
        )

        # Analyse UX
        ux_analysis = analyze_streaming_results(result)
        print(f"\n👤 Expérience utilisateur: {ux_analysis['description']}")

        if ux_analysis["rating"] == "excellent":
            print("🌟 Streaming progressif EXCELLENT - Objectif atteint!")
        elif ux_analysis["rating"] == "very_good":
            print("✅ Streaming progressif TRÈS BON")
        elif ux_analysis["rating"] == "good":
            print("✅ Streaming progressif BON")
        else:
            print("⚠️ Streaming progressif à améliorer")

        # Sauvegarde du rapport
        print("\n💾 Sauvegarde du rapport...")
        try:
            # Utiliser la méthode de sauvegarde du benchmark
            report_path = benchmark.save_results(result, "_phase1_test")
            print(f"📄 Rapport sauvegardé: {report_path}")

            # Rapport complémentaire avec infos Git
            eval_dir = Path(__file__).parent.parent / "evaluation"
            timestamp = test_start_time.strftime("%Y%m%d_%H%M%S")
            commit_short = git_info.get("commit_short", "unknown")
            summary_filename = f"streaming_test_summary_{timestamp}_{commit_short}.json"

            summary_report = {
                "test_info": {
                    "test_type": "streaming_progressif_40min",
                    "timestamp": test_start_time.isoformat(),
                    "duration_seconds": round(total_time, 2),
                    "script_version": "2.0_streaming",
                    "phase": "Phase 1 - Streaming Progressif",
                },
                "git_info": git_info,
                "streaming_results": result,
                "analysis": {
                    "user_experience": ux_analysis,
                    "key_metrics": {
                        "ttfb_seconds": ttfb,
                        "playback_ready_seconds": playback_time,
                        "improvement_percentage": improvement,
                    },
                    "success_criteria": {
                        "target_ttfb": "< 10s",
                        "achieved_ttfb": f"{ttfb:.3f}s",
                        "target_met": ttfb < 10,
                    },
                },
            }

            summary_path = eval_dir / summary_filename
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False, default=str)

            print(f"📋 Résumé sauvegardé: {summary_path}")

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return 1

    else:
        print("❌ Test streaming progressif échoué")
        if result and "error" in result:
            print(f"💥 Erreur: {result['error']}")
        return 1

    print("\n🎉 Phase 1 testée avec succès!")
    print("💡 Prochaines étapes possibles:")
    print("   • Phase 2: Cache Intelligent des exercices")
    print("   • Phase 3: Streaming par segments")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
