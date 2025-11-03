#!/usr/bin/env python3
"""
Script de benchmark pour mesurer les performances du STREAMING PROGRESSIF.
Ce script teste la nouvelle approche avec les endpoints /start-workout-generation et /stream-workout.

Métriques clés:
- Temps jusqu'au premier byte (Time To First Byte - TTFB)
- Temps jusqu'au début de lecture possible
- Comparaison avec l'ancienne approche
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import aiohttp

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(str(Path(__file__).parent))


class StreamingPerformanceBenchmark:
    def __init__(self):
        self.results = {}
        self.api_base_url = "http://localhost:8000/api"

    def log(self, message: str):
        """Log avec timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    async def benchmark_streaming_approach(
        self, duration_minutes: int
    ) -> Optional[Dict[str, Any]]:
        """
        Benchmark de la nouvelle approche streaming progressif
        Mesure le temps jusqu'au premier byte et la possibilité de lecture
        """
        self.log(
            f"🚀 Benchmark STREAMING PROGRESSIF - Workout {duration_minutes} minutes"
        )

        # Configuration du workout
        config = {
            "intensity": "medium_intensity",
            "intervals": {"work_time": 40, "rest_time": 20},
            "no_jump": True,
            "exercice_intensity_levels": ["easy", "medium"],
            "target_duration": 30,
            "no_repeat": False,
            "include_warm_up": True,
            "include_cool_down": True,
        }

        total_duration_seconds = duration_minutes * 60
        workout_id = str(uuid4())  # Générer un UUID valide

        results = {
            "approach": "streaming_progressif",
            "workout_duration_minutes": duration_minutes,
            "workout_id": workout_id,
            "timestamps": {},
            "times": {},
            "success": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                # ============================================================================
                # PHASE 1: Démarrage de la génération (nouveau endpoint)
                # ============================================================================

                self.log("📡 Étape 1: Démarrage génération en arrière-plan...")
                start_generation_time = time.time()

                generation_payload = {
                    "config": config,
                    "total_duration": total_duration_seconds,
                    "name": f"Benchmark Streaming {duration_minutes}min",
                    "workout_id": workout_id,
                }

                async with session.post(
                    f"{self.api_base_url}/start-workout-generation",
                    json=generation_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.log(
                            f"❌ Erreur démarrage génération: {response.status} - {error_text}"
                        )
                        return None

                    generation_result = await response.json()
                    generation_start_time = time.time() - start_generation_time

                    results["timestamps"]["generation_started"] = start_generation_time
                    results["times"]["generation_start_s"] = generation_start_time
                    results["total_exercises"] = generation_result.get(
                        "total_exercises", 0
                    )

                    self.log(f"✅ Génération démarrée en {generation_start_time:.3f}s")
                    self.log(f"📊 {results['total_exercises']} exercices à traiter")

                # ============================================================================
                # PHASE 2: Test du streaming (Time To First Byte)
                # ============================================================================

                self.log("🎥 Étape 2: Test du streaming progressif...")
                streaming_url = f"{self.api_base_url}/stream-workout/{workout_id}"

                # Mesurer le temps jusqu'au premier byte
                first_byte_start = time.time()
                first_byte_received = False
                total_bytes_received = 0
                chunk_count = 0

                async with session.get(streaming_url) as stream_response:
                    if stream_response.status != 200:
                        error_text = await stream_response.text()
                        self.log(
                            f"❌ Erreur streaming: {stream_response.status} - {error_text}"
                        )
                        return None

                    # Analyser les headers de réponse
                    headers = dict(stream_response.headers)
                    self.log(
                        f"📋 Headers reçus: Accept-Ranges={headers.get('Accept-Ranges', 'N/A')}"
                    )
                    self.log(
                        f"📋 Content-Length: {headers.get('Content-Length', 'N/A')} bytes"
                    )

                    # Lire les premiers chunks pour mesurer TTFB
                    timeout_start = time.time()
                    timeout_duration = 10  # 10 secondes de timeout

                    async for chunk in stream_response.content.iter_chunked(
                        64 * 1024
                    ):  # 64KB chunks
                        if not first_byte_received:
                            first_byte_time = time.time() - first_byte_start
                            results["timestamps"]["first_byte"] = time.time()
                            results["times"]["time_to_first_byte_s"] = first_byte_time
                            first_byte_received = True

                            self.log(
                                f"🎯 PREMIER BYTE reçu en {first_byte_time:.3f}s !"
                            )
                            self.log(f"📦 Taille du premier chunk: {len(chunk)} bytes")

                        total_bytes_received += len(chunk)
                        chunk_count += 1

                        # Arrêter après avoir reçu suffisamment de données pour tester
                        # (simule le moment où la vidéo peut commencer à jouer)
                        if total_bytes_received >= 1024 * 1024:  # 1MB reçu
                            playback_possible_time = time.time() - first_byte_start
                            results["timestamps"]["playback_possible"] = time.time()
                            results["times"][
                                "time_to_playback_s"
                            ] = playback_possible_time

                            self.log(
                                f"▶️ LECTURE POSSIBLE après {playback_possible_time:.3f}s"
                            )
                            self.log(
                                f"📊 {total_bytes_received / (1024 * 1024):.1f}MB reçus en {chunk_count} chunks"
                            )
                            break

                        # Timeout si aucune donnée n'arrive
                        if time.time() - timeout_start > timeout_duration:
                            self.log(
                                f"⏰ Timeout après {timeout_duration}s - Aucune donnée reçue"
                            )
                            break

                    # Vérifier si nous avons reçu des données
                    if not first_byte_received:
                        self.log("❌ Aucune donnée reçue du streaming FFmpeg")
                        results["error"] = "No data received from FFmpeg streaming"
                        results["times"]["time_to_first_byte_s"] = 0
                        results["times"]["time_to_playback_s"] = 0
                        return results

                # ============================================================================
                # PHASE 3: Calculs et métriques finales
                # ============================================================================

                total_benchmark_time = time.time() - start_generation_time
                results["times"]["total_benchmark_s"] = total_benchmark_time
                results["times"]["user_wait_time_s"] = results["times"].get(
                    "time_to_first_byte_s", 0
                )

                # Métriques de performance
                results["performance_metrics"] = {
                    "ttfb_ms": results["times"]["time_to_first_byte_s"] * 1000,
                    "playback_ready_ms": results["times"]["time_to_playback_s"] * 1000,
                    "bytes_per_second": total_bytes_received
                    / results["times"]["time_to_playback_s"],
                    "chunks_received": chunk_count,
                }

                # Comparaison avec baseline (3.2 minutes pour 40min)
                baseline_wait_time = 3.2 * 60  # 192 secondes pour 40min
                estimated_baseline = (duration_minutes / 40) * baseline_wait_time

                improvement_factor = (
                    estimated_baseline / results["times"]["user_wait_time_s"]
                )
                improvement_percentage = (
                    (estimated_baseline - results["times"]["user_wait_time_s"])
                    / estimated_baseline
                ) * 100

                results["comparison"] = {
                    "estimated_baseline_s": estimated_baseline,
                    "improvement_factor": improvement_factor,
                    "improvement_percentage": improvement_percentage,
                    "time_saved_s": estimated_baseline
                    - results["times"]["user_wait_time_s"],
                }

                results["success"] = True

                # Affichage des résultats
                self.log("=" * 60)
                self.log("📊 RÉSULTATS STREAMING PROGRESSIF")
                self.log("=" * 60)
                self.log(
                    f"⏱️ Temps jusqu'au premier byte: {results['times']['time_to_first_byte_s']:.3f}s"
                )
                self.log(
                    f"▶️ Temps jusqu'à lecture possible: {results['times']['time_to_playback_s']:.3f}s"
                )
                self.log(
                    f"📈 Amélioration vs baseline: {improvement_factor:.1f}x plus rapide"
                )
                self.log(
                    f"💾 Temps économisé: {results['comparison']['time_saved_s']:.1f}s"
                )
                self.log(
                    f"📊 Pourcentage d'amélioration: {improvement_percentage:.1f}%"
                )

                return results

        except Exception as e:
            self.log(f"❌ Erreur lors du benchmark: {e}")
            results["error"] = str(e)
            return results

    async def benchmark_legacy_approach(
        self, duration_minutes: int
    ) -> Optional[Dict[str, Any]]:
        """
        Benchmark de l'ancienne approche (pour comparaison)
        Utilise l'endpoint /generate-auto-workout-video avec attente complète
        """
        self.log(f"🐌 Benchmark APPROCHE LEGACY - Workout {duration_minutes} minutes")

        config = {
            "intensity": "medium_intensity",
            "intervals": {"work_time": 40, "rest_time": 20},
            "no_jump": True,
            "exercice_intensity_levels": ["easy", "medium"],
            "target_duration": 30,
            "no_repeat": False,
            "include_warm_up": True,
            "include_cool_down": True,
        }

        total_duration_seconds = duration_minutes * 60

        results = {
            "approach": "legacy_blob",
            "workout_duration_minutes": duration_minutes,
            "timestamps": {},
            "times": {},
            "success": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                self.log("📡 Démarrage génération legacy (attente complète)...")
                start_time = time.time()

                payload = {
                    "config": config,
                    "total_duration": total_duration_seconds,
                    "name": f"Benchmark Legacy {duration_minutes}min",
                }

                async with session.post(
                    f"{self.api_base_url}/generate-auto-workout-video",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.log(
                            f"❌ Erreur génération legacy: {response.status} - {error_text}"
                        )
                        return None

                    # Lire tout le blob (approche legacy)
                    video_data = await response.read()
                    total_time = time.time() - start_time

                    results["timestamps"]["generation_complete"] = time.time()
                    results["times"]["total_generation_s"] = total_time
                    results["times"][
                        "user_wait_time_s"
                    ] = total_time  # L'utilisateur attend tout
                    results["video_size_bytes"] = len(video_data)
                    results["video_size_mb"] = len(video_data) / (1024 * 1024)
                    results["success"] = True

                    self.log(f"✅ Génération legacy terminée en {total_time:.1f}s")
                    self.log(f"📁 Taille vidéo: {results['video_size_mb']:.1f}MB")

                    return results

        except Exception as e:
            self.log(f"❌ Erreur lors du benchmark legacy: {e}")
            results["error"] = str(e)
            return results

    def save_results(self, results: Dict[str, Any], filename_suffix: str = ""):
        """Sauvegarde les résultats dans le dossier evaluation"""
        eval_dir = Path(__file__).parent.parent / "evaluation"
        eval_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approach = results.get("approach", "unknown")
        duration = results.get("workout_duration_minutes", "unknown")

        filename = f"benchmark_streaming_{approach}_{duration}min_{timestamp}{filename_suffix}.json"
        filepath = eval_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        self.log(f"💾 Résultats sauvegardés: {filepath}")
        return filepath


async def main():
    """Test comparatif des deux approches"""

    duration = 40  # minutes
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("Usage: python benchmark_streaming_performance.py [duration_minutes]")
            sys.exit(1)

    benchmark = StreamingPerformanceBenchmark()

    print("🎯 BENCHMARK COMPARATIF - STREAMING PROGRESSIF vs LEGACY")
    print("=" * 70)
    print(f"📅 Test démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Durée du workout: {duration} minutes")
    print()

    # Test de l'approche streaming progressif
    print("🚀 TEST 1: APPROCHE STREAMING PROGRESSIF")
    print("-" * 50)
    streaming_results = await benchmark.benchmark_streaming_approach(duration)

    if streaming_results:
        benchmark.save_results(streaming_results, "_streaming")
        print()

    # Test de l'approche legacy (optionnel, peut être long)
    print("🐌 TEST 2: APPROCHE LEGACY (pour comparaison)")
    print("-" * 50)
    print("⚠️ Ce test peut prendre plusieurs minutes...")

    try:
        legacy_results = await benchmark.benchmark_legacy_approach(duration)
        if legacy_results:
            benchmark.save_results(legacy_results, "_legacy")
    except KeyboardInterrupt:
        print("\n⏹️ Test legacy interrompu par l'utilisateur")
        legacy_results = None

    # Comparaison finale
    print("\n" + "=" * 70)
    print("📊 COMPARAISON FINALE")
    print("=" * 70)

    if streaming_results and streaming_results.get("success"):
        ttfb = streaming_results["times"]["time_to_first_byte_s"]
        playback = streaming_results["times"]["time_to_playback_s"]
        improvement = streaming_results["comparison"]["improvement_percentage"]

        print("🚀 Streaming Progressif:")
        print(f"   • Premier byte: {ttfb:.3f}s")
        print(f"   • Lecture possible: {playback:.3f}s")
        print(f"   • Amélioration: {improvement:.1f}%")

    if legacy_results and legacy_results.get("success"):
        legacy_time = legacy_results["times"]["user_wait_time_s"]
        print("🐌 Approche Legacy:")
        print(f"   • Temps d'attente total: {legacy_time:.1f}s")

    print("\n✅ Benchmark terminé!")


if __name__ == "__main__":
    asyncio.run(main())
