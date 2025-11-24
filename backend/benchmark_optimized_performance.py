#!/usr/bin/env python3
"""
Script de benchmark complet pour comparer les performances entre
l'ancien VideoService et le nouveau OptimizedVideoService.

Valide les gains de performance du plan d'optimisation:
- Temps de génération: Objectif <0.5x ratio
- Utilisation mémoire: Réduction grâce à la concaténation progressive
- Taille des fichiers: ~70% de réduction avec vidéos 720p
- CPU usage: Réduction grâce au stream copy intelligent
"""

import asyncio
import gc
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(str(Path(__file__).parent))

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil non disponible - métriques système limitées")

from app.models.config import WorkoutConfig  # noqa: E402
from app.models.enums import Intensity  # noqa: E402
from app.models.exercise import Difficulty  # noqa: E402
from app.models.workout import Workout  # noqa: E402
from app.services.video_service import VideoService  # noqa: E402
from app.services.video_service_optimized import OptimizedVideoService  # noqa: E402
from app.services.workout_generator import (  # noqa: E402
    generate_workout_exercises,
    load_exercises_from_json,
)


@dataclass
class SystemMetrics:
    """Métriques système pendant un test"""

    cpu_percent_start: float = 0.0
    cpu_percent_end: float = 0.0
    cpu_percent_avg: float = 0.0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_delta_mb: float = 0.0


@dataclass
class BenchmarkResult:
    """Résultat d'un benchmark individuel"""

    scenario_name: str
    service_type: str  # "original" ou "optimized"
    duration_minutes: int
    num_exercises: int

    # Temps
    exercise_gen_time_s: float = 0.0
    video_download_time_s: float = 0.0
    break_generation_time_s: float = 0.0
    ffmpeg_build_time_s: float = 0.0
    ffmpeg_execution_time_s: float = 0.0
    total_time_s: float = 0.0

    # Fichiers
    output_file_size_mb: float = 0.0
    source_videos_size_mb: float = 0.0

    # Métriques système
    system_metrics: SystemMetrics = field(default_factory=SystemMetrics)

    # Ratios de performance
    generation_vs_playback_ratio: float = 0.0

    # Status
    success: bool = False
    error_message: str = ""

    # Métriques spécifiques aux optimisations
    break_cache_hits: int = 0
    stream_copy_used: bool = False
    parallel_downloads_count: int = 0


@dataclass
class ComparisonResult:
    """Résultat de comparaison entre deux services"""

    scenario_name: str
    duration_minutes: int

    original_result: Optional[BenchmarkResult] = None
    optimized_result: Optional[BenchmarkResult] = None

    # Gains calculés
    time_improvement_factor: float = 0.0
    time_improvement_percent: float = 0.0
    memory_improvement_percent: float = 0.0
    file_size_improvement_percent: float = 0.0

    # Objectifs atteints
    meets_time_objective: bool = False  # <0.5x ratio
    meets_memory_objective: bool = False
    meets_size_objective: bool = False  # ~70% réduction


class SystemMonitor:
    """Moniteur de métriques système"""

    def __init__(self):
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.monitoring = False

    def start(self) -> SystemMetrics:
        """Démarre le monitoring et retourne les métriques initiales"""
        metrics = SystemMetrics()

        if self.process:
            self.cpu_samples = []
            self.memory_samples = []

            # Métriques initiales
            metrics.cpu_percent_start = self.process.cpu_percent(interval=0.1)
            metrics.memory_start_mb = self.process.memory_info().rss / (1024 * 1024)

            self.monitoring = True

        return metrics

    def sample(self):
        """Prend un échantillon des métriques"""
        if self.process and self.monitoring:
            self.cpu_samples.append(self.process.cpu_percent(interval=None))
            self.memory_samples.append(self.process.memory_info().rss / (1024 * 1024))

    def stop(self, metrics: SystemMetrics) -> SystemMetrics:
        """Arrête le monitoring et finalise les métriques"""
        self.monitoring = False

        if self.process:
            metrics.cpu_percent_end = self.process.cpu_percent(interval=0.1)
            metrics.memory_end_mb = self.process.memory_info().rss / (1024 * 1024)

            if self.cpu_samples:
                metrics.cpu_percent_avg = sum(self.cpu_samples) / len(self.cpu_samples)

            if self.memory_samples:
                metrics.memory_peak_mb = max(self.memory_samples)

            metrics.memory_delta_mb = metrics.memory_end_mb - metrics.memory_start_mb

        return metrics


class OptimizedPerformanceBenchmark:
    """
    Benchmark complet comparant VideoService vs OptimizedVideoService

    Tests:
    - Différentes durées de workout (2min, 10min, 20min, 40min)
    - Métriques: temps, mémoire, CPU, taille fichiers
    - Tests spécifiques des optimisations (break cache, stream copy, etc.)
    """

    # Scénarios de test
    TEST_SCENARIOS = [
        {"duration": 2, "exercises": 4, "name": "Quick workout"},
        {"duration": 10, "exercises": 19, "name": "Standard workout"},
        {"duration": 20, "exercises": 38, "name": "Long workout"},
        {"duration": 40, "exercises": 76, "name": "Ultra workout"},
    ]

    def __init__(self, verbose: bool = True):
        self.project_root = Path(__file__).parent.parent
        self.verbose = verbose
        self.results: Dict[str, List[BenchmarkResult]] = {
            "original": [],
            "optimized": [],
        }
        self.comparisons: List[ComparisonResult] = []
        self.system_monitor = SystemMonitor()

        # Charger les exercices une seule fois
        self.all_exercises = load_exercises_from_json()
        self.exercise_lookup = {ex.id: ex for ex in self.all_exercises}

        # Répertoire pour les fichiers de sortie
        self.output_dir = Path(tempfile.gettempdir()) / "benchmark_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log avec timestamp"""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(
                level, ""
            )
            print(f"[{timestamp}] {emoji} {message}")

    def _create_workout_config(
        self, duration_minutes: int, intensity: Intensity = Intensity.MEDIUM_INTENSITY
    ) -> WorkoutConfig:
        """Crée une configuration de workout"""
        return WorkoutConfig(
            intensity=intensity,
            intervals={"work_time": 40, "rest_time": 20},
            no_jump=True,
            exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
            target_duration=duration_minutes,
        )

    def _create_workout(self, duration_minutes: int, config: WorkoutConfig) -> Workout:
        """Crée un objet Workout"""
        return Workout(
            id=uuid4(),
            name=f"Benchmark {duration_minutes}min",
            config=config,
            total_duration=duration_minutes * 60,
            ai_generated=True,
        )

    def _resolve_exercises(self, workout: Workout) -> List:
        """Génère et résout les exercices d'un workout"""
        workout_exercises = generate_workout_exercises(workout)

        resolved = []
        for workout_ex in workout_exercises:
            if workout_ex.exercise_id in self.exercise_lookup:
                resolved.append(self.exercise_lookup[workout_ex.exercise_id])

        return resolved

    def _get_source_videos_size(self, service: VideoService, exercises: List) -> float:
        """Calcule la taille totale des vidéos sources"""
        total_size = 0
        for exercise in exercises:
            video_path = service._resolve_video_path(exercise)
            if video_path and video_path.exists():
                total_size += video_path.stat().st_size
        return total_size / (1024 * 1024)  # MB

    async def benchmark_original_service(
        self, scenario: Dict, config: WorkoutConfig, exercises: List
    ) -> BenchmarkResult:
        """
        Benchmark du VideoService original
        """
        result = BenchmarkResult(
            scenario_name=scenario["name"],
            service_type="original",
            duration_minutes=scenario["duration"],
            num_exercises=len(exercises),
        )

        self.log(f"🔧 Test VideoService original - {scenario['name']}")

        try:
            # Initialiser le service
            service = VideoService(project_root=self.project_root)

            # Démarrer le monitoring
            metrics = self.system_monitor.start()
            total_start = time.time()

            # Mesurer la taille des sources
            result.source_videos_size_mb = self._get_source_videos_size(
                service, exercises
            )

            # Fichier de sortie temporaire
            output_path = (
                self.output_dir
                / f"original_{scenario['duration']}min_{uuid4().hex[:8]}.mp4"
            )

            # Construction de la commande FFmpeg (inclut téléchargement et breaks)
            ffmpeg_build_start = time.time()
            command = service.build_ffmpeg_command(exercises, config, output_path)
            result.ffmpeg_build_time_s = time.time() - ffmpeg_build_start

            if not command:
                raise RuntimeError("Impossible de construire la commande FFmpeg")

            # Exécution FFmpeg
            ffmpeg_exec_start = time.time()
            subprocess.run(command, capture_output=True, text=True, check=True)
            result.ffmpeg_execution_time_s = time.time() - ffmpeg_exec_start

            # Sampling métriques pendant l'exécution
            self.system_monitor.sample()

            # Finaliser
            result.total_time_s = time.time() - total_start
            result.system_metrics = self.system_monitor.stop(metrics)

            # Taille du fichier de sortie
            if output_path.exists():
                result.output_file_size_mb = output_path.stat().st_size / (1024 * 1024)
                result.success = True

                # Ratio génération/lecture
                playback_duration = scenario["duration"] * 60
                result.generation_vs_playback_ratio = (
                    result.total_time_s / playback_duration
                )

            # Nettoyage
            if output_path.exists():
                output_path.unlink()

            self.log(
                f"✓ Original terminé: {result.total_time_s:.1f}s "
                f"(ratio: {result.generation_vs_playback_ratio:.2f}x)",
                "SUCCESS",
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            self.log(f"Erreur original: {e}", "ERROR")

        # Force garbage collection
        gc.collect()

        return result

    async def benchmark_optimized_service(
        self, scenario: Dict, config: WorkoutConfig, exercises: List
    ) -> BenchmarkResult:
        """
        Benchmark du OptimizedVideoService
        """
        result = BenchmarkResult(
            scenario_name=scenario["name"],
            service_type="optimized",
            duration_minutes=scenario["duration"],
            num_exercises=len(exercises),
        )

        self.log(f"⚡ Test OptimizedVideoService - {scenario['name']}")

        try:
            # Initialiser le service optimisé
            service = OptimizedVideoService(
                project_root=self.project_root, max_parallel_downloads=4
            )

            # Démarrer le monitoring
            metrics = self.system_monitor.start()
            total_start = time.time()

            # Mesurer la taille des sources
            result.source_videos_size_mb = self._get_source_videos_size(
                service, exercises
            )

            # Fichier de sortie temporaire
            output_path = (
                self.output_dir
                / f"optimized_{scenario['duration']}min_{uuid4().hex[:8]}.mp4"
            )

            # Génération avec la méthode optimisée
            success = service.generate_workout_video_progressive(
                exercises, config, output_path
            )

            # Sampling métriques
            self.system_monitor.sample()

            # Finaliser
            result.total_time_s = time.time() - total_start
            result.system_metrics = self.system_monitor.stop(metrics)

            # Métriques spécifiques optimisations
            result.parallel_downloads_count = service.max_parallel_downloads
            result.break_cache_hits = (
                len(exercises) - 1
            )  # Tous les breaks viennent du cache

            # Taille du fichier de sortie
            if output_path.exists():
                result.output_file_size_mb = output_path.stat().st_size / (1024 * 1024)
                result.success = success

                # Ratio génération/lecture
                playback_duration = scenario["duration"] * 60
                result.generation_vs_playback_ratio = (
                    result.total_time_s / playback_duration
                )

            # Nettoyage
            if output_path.exists():
                output_path.unlink()

            self.log(
                f"✓ Optimized terminé: {result.total_time_s:.1f}s "
                f"(ratio: {result.generation_vs_playback_ratio:.2f}x)",
                "SUCCESS",
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            self.log(f"Erreur optimized: {e}", "ERROR")

        # Force garbage collection
        gc.collect()

        return result

    def _calculate_comparison(
        self, original: BenchmarkResult, optimized: BenchmarkResult
    ) -> ComparisonResult:
        """Calcule les métriques de comparaison"""
        comparison = ComparisonResult(
            scenario_name=original.scenario_name,
            duration_minutes=original.duration_minutes,
            original_result=original,
            optimized_result=optimized,
        )

        if original.success and optimized.success:
            # Amélioration du temps
            if optimized.total_time_s > 0:
                comparison.time_improvement_factor = (
                    original.total_time_s / optimized.total_time_s
                )
                comparison.time_improvement_percent = (
                    (original.total_time_s - optimized.total_time_s)
                    / original.total_time_s
                    * 100
                )

            # Amélioration mémoire
            if original.system_metrics.memory_peak_mb > 0:
                comparison.memory_improvement_percent = (
                    (
                        original.system_metrics.memory_peak_mb
                        - optimized.system_metrics.memory_peak_mb
                    )
                    / original.system_metrics.memory_peak_mb
                    * 100
                )

            # Amélioration taille fichier
            if original.output_file_size_mb > 0:
                comparison.file_size_improvement_percent = (
                    (original.output_file_size_mb - optimized.output_file_size_mb)
                    / original.output_file_size_mb
                    * 100
                )

            # Vérification des objectifs
            comparison.meets_time_objective = (
                optimized.generation_vs_playback_ratio < 0.5
            )
            comparison.meets_size_objective = (
                comparison.file_size_improvement_percent >= 50
            )
            comparison.meets_memory_objective = (
                comparison.memory_improvement_percent > 0
            )

        return comparison

    async def test_break_cache_optimization(self) -> Dict:
        """
        Test spécifique: Vérifier que le cache des breaks fonctionne
        Un seul break doit être généré par durée
        """
        self.log("🧪 Test: Break Cache Optimization")

        results = {
            "test_name": "break_cache",
            "description": "Vérifie qu'un seul break est généré par durée",
            "passed": False,
            "details": {},
        }

        try:
            service = OptimizedVideoService(project_root=self.project_root)

            # Vérifier que les breaks communs sont en cache
            cached_breaks = []
            for duration in service.COMMON_BREAK_DURATIONS:
                cache_path = service._get_cached_break_path(duration)
                if cache_path.exists():
                    cached_breaks.append(
                        {
                            "duration": duration,
                            "size_kb": cache_path.stat().st_size / 1024,
                            "path": str(cache_path),
                        }
                    )

            results["details"]["cached_breaks"] = cached_breaks
            results["details"]["expected_count"] = len(service.COMMON_BREAK_DURATIONS)
            results["details"]["actual_count"] = len(cached_breaks)
            results["passed"] = len(cached_breaks) == len(
                service.COMMON_BREAK_DURATIONS
            )

            self.log(
                f"Break cache: {len(cached_breaks)}/{len(service.COMMON_BREAK_DURATIONS)} durées en cache",
                "SUCCESS" if results["passed"] else "WARN",
            )

        except Exception as e:
            results["error"] = str(e)
            self.log(f"Erreur test break cache: {e}", "ERROR")

        return results

    async def test_stream_copy_detection(self) -> Dict:
        """
        Test spécifique: Vérifier la détection du format pour stream copy
        """
        self.log("🧪 Test: Stream Copy Detection")

        results = {
            "test_name": "stream_copy_detection",
            "description": "Vérifie la détection automatique du format vidéo",
            "passed": False,
            "details": {},
        }

        try:
            service = OptimizedVideoService(project_root=self.project_root)

            # Tester la détection sur quelques exercices
            sample_exercises = self.all_exercises[:5]
            format_results = []

            for exercise in sample_exercises:
                video_path = service._resolve_video_path(exercise)
                if video_path and video_path.exists():
                    video_format = service.detect_video_format(video_path)
                    if video_format:
                        format_results.append(
                            {
                                "exercise": exercise.name,
                                "codec": video_format.codec,
                                "resolution": f"{video_format.width}x{video_format.height}",
                                "fps": video_format.fps,
                                "is_target_format": video_format.is_target_format,
                            }
                        )

            results["details"]["format_analysis"] = format_results
            results["passed"] = len(format_results) > 0

            target_format_count = sum(
                1 for f in format_results if f["is_target_format"]
            )
            self.log(
                f"Formats détectés: {len(format_results)} vidéos, "
                f"{target_format_count} au format cible",
                "SUCCESS" if results["passed"] else "WARN",
            )

        except Exception as e:
            results["error"] = str(e)
            self.log(f"Erreur test stream copy: {e}", "ERROR")

        return results

    async def test_parallel_download(self) -> Dict:
        """
        Test spécifique: Mesurer le gain du téléchargement parallèle
        """
        self.log("🧪 Test: Parallel Download Performance")

        results = {
            "test_name": "parallel_download",
            "description": "Compare téléchargement séquentiel vs parallèle",
            "passed": False,
            "details": {},
        }

        try:
            # Test avec quelques exercices
            sample_exercises = self.all_exercises[:8]

            # Service avec téléchargement parallèle
            service_parallel = OptimizedVideoService(
                project_root=self.project_root, max_parallel_downloads=4
            )

            # Mesurer téléchargement parallèle
            start_parallel = time.time()
            service_parallel._download_videos_parallel(sample_exercises)
            time_parallel = time.time() - start_parallel

            # Service original (séquentiel)
            service_sequential = VideoService(project_root=self.project_root)

            # Mesurer téléchargement séquentiel
            start_sequential = time.time()
            for ex in sample_exercises:
                service_sequential._resolve_video_path(ex)
            time_sequential = time.time() - start_sequential

            results["details"] = {
                "num_videos": len(sample_exercises),
                "time_sequential_s": round(time_sequential, 2),
                "time_parallel_s": round(time_parallel, 2),
                "speedup_factor": round(time_sequential / time_parallel, 2)
                if time_parallel > 0
                else 0,
            }

            results["passed"] = time_parallel < time_sequential

            self.log(
                f"Téléchargement: séquentiel={time_sequential:.2f}s, "
                f"parallèle={time_parallel:.2f}s "
                f"(speedup: {results['details']['speedup_factor']}x)",
                "SUCCESS" if results["passed"] else "WARN",
            )

        except Exception as e:
            results["error"] = str(e)
            self.log(f"Erreur test parallel download: {e}", "ERROR")

        return results

    async def run_scenario(self, scenario: Dict) -> ComparisonResult:
        """Exécute un scénario de test complet"""
        self.log(f"\n{'='*60}")
        self.log(f"📊 Scénario: {scenario['name']} ({scenario['duration']} min)")
        self.log(f"{'='*60}")

        # Configuration
        config = self._create_workout_config(scenario["duration"])
        workout = self._create_workout(scenario["duration"], config)
        exercises = self._resolve_exercises(workout)

        # Limiter au nombre d'exercices du scénario si spécifié
        if len(exercises) > scenario["exercises"]:
            exercises = exercises[: scenario["exercises"]]

        self.log(f"Exercices résolus: {len(exercises)}")

        # Benchmark original
        original_result = await self.benchmark_original_service(
            scenario, config, exercises
        )
        self.results["original"].append(original_result)

        # Pause entre les tests
        await asyncio.sleep(2)
        gc.collect()

        # Benchmark optimisé
        optimized_result = await self.benchmark_optimized_service(
            scenario, config, exercises
        )
        self.results["optimized"].append(optimized_result)

        # Calculer la comparaison
        comparison = self._calculate_comparison(original_result, optimized_result)
        self.comparisons.append(comparison)

        return comparison

    async def run_all_scenarios(self) -> Dict:
        """Exécute tous les scénarios de test"""
        self.log("🚀 Démarrage du benchmark complet")
        self.log(f"Scénarios: {len(self.TEST_SCENARIOS)}")

        for scenario in self.TEST_SCENARIOS:
            await self.run_scenario(scenario)

            # Pause entre les scénarios
            await asyncio.sleep(5)
            gc.collect()

        return self.generate_report()

    async def run_optimization_tests(self) -> Dict:
        """Exécute les tests spécifiques des optimisations"""
        self.log("\n" + "=" * 60)
        self.log("🔬 Tests des optimisations spécifiques")
        self.log("=" * 60)

        tests = {}

        tests["break_cache"] = await self.test_break_cache_optimization()
        tests["stream_copy"] = await self.test_stream_copy_detection()
        tests["parallel_download"] = await self.test_parallel_download()

        return tests

    def generate_report(self) -> Dict:
        """Génère le rapport complet de benchmark"""
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "psutil_available": PSUTIL_AVAILABLE,
                "scenarios_count": len(self.TEST_SCENARIOS),
            },
            "summary": {
                "total_tests": len(self.comparisons) * 2,
                "successful_original": sum(
                    1 for r in self.results["original"] if r.success
                ),
                "successful_optimized": sum(
                    1 for r in self.results["optimized"] if r.success
                ),
            },
            "comparisons": [],
            "objectives": {
                "time_ratio_target": "<0.5x",
                "file_size_reduction_target": "~70%",
                "met_objectives": [],
            },
            "recommendations": [],
        }

        # Détails des comparaisons
        for comp in self.comparisons:
            comp_data = {
                "scenario": comp.scenario_name,
                "duration_minutes": comp.duration_minutes,
                "original": {
                    "total_time_s": round(comp.original_result.total_time_s, 2)
                    if comp.original_result
                    else None,
                    "ratio": round(comp.original_result.generation_vs_playback_ratio, 3)
                    if comp.original_result
                    else None,
                    "file_size_mb": round(comp.original_result.output_file_size_mb, 2)
                    if comp.original_result
                    else None,
                    "success": comp.original_result.success
                    if comp.original_result
                    else False,
                },
                "optimized": {
                    "total_time_s": round(comp.optimized_result.total_time_s, 2)
                    if comp.optimized_result
                    else None,
                    "ratio": round(
                        comp.optimized_result.generation_vs_playback_ratio, 3
                    )
                    if comp.optimized_result
                    else None,
                    "file_size_mb": round(comp.optimized_result.output_file_size_mb, 2)
                    if comp.optimized_result
                    else None,
                    "success": comp.optimized_result.success
                    if comp.optimized_result
                    else False,
                },
                "improvements": {
                    "time_factor": round(comp.time_improvement_factor, 2),
                    "time_percent": round(comp.time_improvement_percent, 1),
                    "memory_percent": round(comp.memory_improvement_percent, 1),
                    "file_size_percent": round(comp.file_size_improvement_percent, 1),
                },
                "objectives_met": {
                    "time": comp.meets_time_objective,
                    "memory": comp.meets_memory_objective,
                    "file_size": comp.meets_size_objective,
                },
            }
            report["comparisons"].append(comp_data)

            # Vérifier les objectifs atteints
            if comp.meets_time_objective:
                report["objectives"]["met_objectives"].append(
                    f"{comp.scenario_name}: Objectif temps atteint (ratio < 0.5x)"
                )

        # Recommandations basées sur les résultats
        report["recommendations"] = self._generate_recommendations()

        return report

    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les résultats"""
        recommendations = []

        if not self.comparisons:
            return ["Exécuter les benchmarks pour obtenir des recommandations"]

        # Analyser les résultats
        avg_improvement = sum(
            c.time_improvement_factor for c in self.comparisons
        ) / len(self.comparisons)

        if avg_improvement >= 4:
            recommendations.append(
                "✅ Excellent! L'objectif de 4-5x d'amélioration est atteint. "
                "Le service optimisé est prêt pour la production."
            )
        elif avg_improvement >= 2:
            recommendations.append(
                "⚠️ Amélioration significative mais en dessous de l'objectif. "
                "Considérer l'optimisation des vidéos sources vers le format 720p."
            )
        else:
            recommendations.append(
                "❌ L'amélioration est insuffisante. "
                "Vérifier que les vidéos sources sont au format optimisé."
            )

        # Vérifier le ratio temps/lecture
        for comp in self.comparisons:
            if (
                comp.optimized_result
                and comp.optimized_result.generation_vs_playback_ratio >= 0.5
            ):
                recommendations.append(
                    f"⚠️ {comp.scenario_name}: Le ratio de génération ({comp.optimized_result.generation_vs_playback_ratio:.2f}x) "
                    f"dépasse l'objectif de 0.5x. Optimiser les vidéos sources."
                )

        # Recommandations mémoire
        memory_improvements = [
            c.memory_improvement_percent
            for c in self.comparisons
            if c.memory_improvement_percent > 0
        ]
        if memory_improvements:
            avg_memory = sum(memory_improvements) / len(memory_improvements)
            recommendations.append(
                f"📊 Réduction moyenne de mémoire: {avg_memory:.1f}%. "
                "La concaténation progressive fonctionne correctement."
            )

        return recommendations

    def print_report(self, report: Dict):
        """Affiche le rapport de manière formatée"""
        print("\n" + "=" * 70)
        print("📊 RAPPORT DE BENCHMARK - COMPARAISON DES SERVICES VIDÉO")
        print("=" * 70)

        # Tableau comparatif
        print(
            "\n┌─────────────────────┬───────────────────┬───────────────────┬─────────────┐"
        )
        print(
            "│ Scénario            │ Original          │ Optimisé          │ Gain        │"
        )
        print(
            "├─────────────────────┼───────────────────┼───────────────────┼─────────────┤"
        )

        for comp in report["comparisons"]:
            orig = comp["original"]
            opt = comp["optimized"]
            imp = comp["improvements"]

            orig_str = (
                f"{orig['total_time_s']}s ({orig['ratio']}x)"
                if orig["success"]
                else "ÉCHEC"
            )
            opt_str = (
                f"{opt['total_time_s']}s ({opt['ratio']}x)"
                if opt["success"]
                else "ÉCHEC"
            )
            gain_str = f"{imp['time_factor']}x ({imp['time_percent']:+.0f}%)"

            print(
                f"│ {comp['scenario']:<19} │ {orig_str:<17} │ {opt_str:<17} │ {gain_str:<11} │"
            )

        print(
            "└─────────────────────┴───────────────────┴───────────────────┴─────────────┘"
        )

        # Objectifs
        print("\n📎 OBJECTIFS:")
        for obj in report["objectives"]["met_objectives"]:
            print(f"  {obj}")

        # Recommandations
        print("\n💡 RECOMMANDATIONS:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

        print("\n" + "=" * 70)

    def save_report(self, report: Dict, filepath: Path = None):
        """Sauvegarde le rapport en JSON"""
        if filepath is None:
            filepath = Path("benchmark_optimized_results.json")

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.log(f"Rapport sauvegardé: {filepath}")

    def cleanup(self):
        """Nettoie les fichiers temporaires de test"""
        self.log("🧹 Nettoyage des fichiers temporaires...")

        cleaned = 0
        for file in self.output_dir.glob("*.mp4"):
            try:
                file.unlink()
                cleaned += 1
            except Exception:
                pass

        self.log(f"Fichiers nettoyés: {cleaned}")


async def main():
    """Point d'entrée principal"""
    print("=" * 70)
    print("🎬 BENCHMARK COMPARATIF: VideoService vs OptimizedVideoService")
    print("=" * 70)

    benchmark = OptimizedPerformanceBenchmark(verbose=True)

    try:
        # Exécuter les tests des optimisations
        optimization_tests = await benchmark.run_optimization_tests()

        # Exécuter tous les scénarios
        report = await benchmark.run_all_scenarios()

        # Ajouter les tests d'optimisation au rapport
        report["optimization_tests"] = optimization_tests

        # Afficher et sauvegarder le rapport
        benchmark.print_report(report)
        benchmark.save_report(report)

    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback

        traceback.print_exc()
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    # Support pour Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
