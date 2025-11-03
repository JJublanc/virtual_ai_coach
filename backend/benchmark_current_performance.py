#!/usr/bin/env python3
"""
Script de benchmark pour mesurer les performances actuelles de génération vidéo.
À exécuter avant les optimisations pour établir une baseline.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from app.models.config import WorkoutConfig  # noqa: E402
from app.models.enums import Intensity  # noqa: E402
from app.models.exercise import Difficulty  # noqa: E402
from app.models.workout import Workout  # noqa: E402
from app.services.video_service import VideoService  # noqa: E402
from app.services.workout_generator import generate_workout_exercises  # noqa: E402


class PerformanceBenchmark:
    def __init__(self):
        self.results = {}
        self.project_root = Path(__file__).parent.parent
        self.video_service = VideoService(project_root=self.project_root)

    def log(self, message: str):
        """Log avec timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    async def benchmark_workout_generation(
        self, duration_minutes: int, intensity: Intensity = Intensity.MEDIUM_INTENSITY
    ):
        """
        Benchmark complet d'un workout de la durée spécifiée
        """
        self.log(
            f"🎯 Début benchmark workout {duration_minutes} minutes (intensité: {intensity.value})"
        )

        # Configuration du workout
        config = WorkoutConfig(
            intensity=intensity,
            intervals={"work_time": 40, "rest_time": 20},
            no_jump=True,
            exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
            target_duration=30,
        )

        total_duration = duration_minutes * 60  # Conversion en secondes

        # Créer l'objet Workout
        workout = Workout(
            id=uuid4(),
            name=f"Benchmark {duration_minutes}min",
            config=config,
            total_duration=total_duration,
            ai_generated=True,
        )

        # Mesures de performance
        start_time = time.time()

        # 1. Génération des exercices
        self.log("📝 Génération de la liste d'exercices...")
        exercise_gen_start = time.time()

        try:
            workout_exercises = generate_workout_exercises(workout)
            exercise_gen_time = time.time() - exercise_gen_start

            self.log(
                f"✅ {len(workout_exercises)} exercices générés en {exercise_gen_time:.2f}s"
            )

            # Charger tous les exercices pour résoudre les noms
            from app.services.workout_generator import load_exercises_from_json

            all_exercises = load_exercises_from_json()
            exercise_lookup = {ex.id: ex for ex in all_exercises}

            # Résoudre les exercices complets
            resolved_exercises = []
            for workout_ex in workout_exercises:
                if workout_ex.exercise_id in exercise_lookup:
                    resolved_exercises.append(exercise_lookup[workout_ex.exercise_id])
                else:
                    self.log(f"⚠️ Exercice non trouvé: {workout_ex.exercise_id}")

            # Afficher la liste des exercices
            exercise_names = [ex.name for ex in resolved_exercises]
            self.log(
                f"📋 Exercices: {', '.join(exercise_names[:5])}{'...' if len(exercise_names) > 5 else ''}"
            )

        except Exception as e:
            self.log(f"❌ Erreur génération exercices: {e}")
            return None

        # 2. Vérification des fichiers vidéo
        self.log("🔍 Vérification des fichiers vidéo...")
        missing_videos = []
        total_video_size = 0

        for exercise in resolved_exercises:
            video_path = self.video_service._resolve_video_path(exercise)
            if video_path and video_path.exists():
                size = video_path.stat().st_size
                total_video_size += size
                self.log(f"  ✅ {exercise.name}: {video_path.name} ({size // 1024}KB)")
            else:
                missing_videos.append(exercise.name)
                self.log(f"  ❌ {exercise.name}: fichier manquant")

        if missing_videos:
            self.log(
                f"⚠️ {len(missing_videos)} vidéos manquantes: {missing_videos[:3]}{'...' if len(missing_videos) > 3 else ''}"
            )
            return None

        self.log(
            f"📊 Taille totale des vidéos sources: {total_video_size // (1024 * 1024)}MB"
        )

        # 3. Construction de la commande FFmpeg
        self.log("🔧 Construction de la commande FFmpeg...")
        ffmpeg_build_start = time.time()

        # Créer un fichier de sortie temporaire
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            output_path = Path(temp_file.name)

        try:
            command = self.video_service.build_ffmpeg_command(
                resolved_exercises, config, output_path
            )
            ffmpeg_build_time = time.time() - ffmpeg_build_start

            if not command:
                self.log("❌ Impossible de construire la commande FFmpeg")
                return None

            self.log(f"✅ Commande FFmpeg construite en {ffmpeg_build_time:.2f}s")
            self.log(f"🔧 Commande: {' '.join(command[:10])}...")

        except Exception as e:
            self.log(f"❌ Erreur construction FFmpeg: {e}")
            return None

        # 4. Exécution FFmpeg avec mesures détaillées
        self.log("🎬 Début génération vidéo FFmpeg...")
        ffmpeg_start = time.time()

        try:
            # Exécuter FFmpeg avec capture des logs
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Surveiller le processus
            poll_interval = 5  # Vérifier toutes les 5 secondes
            last_check = time.time()

            while process.poll() is None:
                current_time = time.time()
                if current_time - last_check >= poll_interval:
                    elapsed = current_time - ffmpeg_start
                    self.log(f"⏳ FFmpeg en cours... {elapsed:.0f}s écoulées")
                    last_check = current_time

                time.sleep(1)

            # Récupérer les résultats
            stdout, stderr = process.communicate()
            ffmpeg_time = time.time() - ffmpeg_start

            if process.returncode == 0:
                self.log(f"✅ FFmpeg terminé avec succès en {ffmpeg_time:.2f}s")
            else:
                self.log(f"❌ FFmpeg échoué (code {process.returncode})")
                self.log(f"Stderr: {stderr[:500]}...")
                return None

        except Exception as e:
            self.log(f"❌ Erreur exécution FFmpeg: {e}")
            return None

        # 5. Vérification du fichier de sortie
        if output_path.exists():
            output_size = output_path.stat().st_size
            self.log(f"📁 Fichier généré: {output_size // (1024 * 1024)}MB")

            # Obtenir les infos vidéo
            try:
                video_info = self.video_service.get_video_info(output_path)
                if video_info and "format" in video_info:
                    duration = float(video_info["format"].get("duration", 0))
                    self.log(
                        f"⏱️ Durée vidéo: {duration:.1f}s ({duration / 60:.1f} min)"
                    )
            except Exception as e:
                self.log(f"⚠️ Impossible d'obtenir les infos vidéo: {e}")
        else:
            self.log("❌ Fichier de sortie non créé")
            return None

        # 6. Calcul des métriques finales
        total_time = time.time() - start_time

        results = {
            "workout_duration_minutes": duration_minutes,
            "total_exercises": len(resolved_exercises),
            "source_videos_size_mb": total_video_size // (1024 * 1024),
            "output_video_size_mb": output_size // (1024 * 1024),
            "times": {
                "exercise_generation_s": round(exercise_gen_time, 2),
                "ffmpeg_build_s": round(ffmpeg_build_time, 2),
                "ffmpeg_execution_s": round(ffmpeg_time, 2),
                "total_s": round(total_time, 2),
                "total_minutes": round(total_time / 60, 2),
            },
            "performance_ratios": {
                "generation_time_vs_video_duration": round(
                    total_time / (duration_minutes * 60), 2
                ),
                "ffmpeg_time_vs_video_duration": round(
                    ffmpeg_time / (duration_minutes * 60), 2
                ),
            },
        }

        # Nettoyage
        try:
            output_path.unlink()
        except Exception as e:
            self.log(f"⚠️ Impossible de supprimer le fichier temporaire: {e}")

        self.log("📊 === RÉSULTATS BENCHMARK ===")
        self.log(f"Durée workout: {duration_minutes} minutes")
        self.log(f"Nombre d'exercices: {len(resolved_exercises)}")
        self.log(f"Temps total: {total_time:.1f}s ({total_time / 60:.1f} min)")
        self.log(f"Temps FFmpeg: {ffmpeg_time:.1f}s ({ffmpeg_time / 60:.1f} min)")
        self.log(f"Ratio temps/durée: {total_time / (duration_minutes * 60):.1f}x")
        self.log(f"Taille sortie: {output_size // (1024 * 1024)}MB")

        return results

    async def run_comprehensive_benchmark(self):
        """Exécute un benchmark complet avec plusieurs durées"""

        self.log("🚀 Début du benchmark complet")

        # Tests avec différentes durées
        test_cases = [(2, "Test rapide"), (10, "Test moyen"), (40, "Test cible")]

        all_results = {}

        for duration, description in test_cases:
            self.log(f"\n{'=' * 50}")
            self.log(f"🎯 {description}: {duration} minutes")
            self.log(f"{'=' * 50}")

            result = await self.benchmark_workout_generation(duration)
            if result:
                all_results[f"{duration}min"] = result
            else:
                self.log(f"❌ Échec du test {duration} minutes")

            # Pause entre les tests
            if duration < 40:
                self.log("⏸️ Pause 10s avant le test suivant...")
                time.sleep(10)

        # Sauvegarde des résultats
        results_file = Path("benchmark_results.json")
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)

        self.log(f"\n📄 Résultats sauvegardés dans {results_file}")

        # Résumé final
        self.log("\n📊 === RÉSUMÉ FINAL ===")
        for test_name, result in all_results.items():
            times = result["times"]
            ratios = result["performance_ratios"]
            self.log(
                f"{test_name}: {times['total_minutes']:.1f}min total, ratio {ratios['generation_time_vs_video_duration']:.1f}x"
            )

        return all_results


async def main():
    """Point d'entrée principal"""
    benchmark = PerformanceBenchmark()

    if len(sys.argv) > 1:
        # Test d'une durée spécifique
        try:
            duration = int(sys.argv[1])
            await benchmark.benchmark_workout_generation(duration)
        except ValueError:
            print("Usage: python benchmark_current_performance.py [durée_en_minutes]")
            sys.exit(1)
    else:
        # Benchmark complet
        await benchmark.run_comprehensive_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
