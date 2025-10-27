"""Tests pour l'API des exercices."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.exercise import Exercise

client = TestClient(app)


class TestGetExercises:
    """Tests pour l'endpoint GET /api/exercises"""

    def test_get_exercises_returns_list(self):
        """Vérifie que l'endpoint retourne une liste d'exercices"""
        response = client.get("/api/exercises")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_exercises_returns_valid_exercises(self):
        """Vérifie que chaque exercice retourné est valide"""
        response = client.get("/api/exercises")
        exercises = response.json()

        assert len(exercises) > 0, "La liste d'exercices ne devrait pas être vide"

        # Valider chaque exercice avec le modèle Pydantic
        for exercise_data in exercises:
            exercise = Exercise(**exercise_data)
            assert exercise.name
            assert exercise.description
            assert exercise.video_url
            assert exercise.default_duration > 0
            assert exercise.difficulty in ["easy", "medium", "hard"]

    def test_get_exercises_contains_expected_fields(self):
        """Vérifie que chaque exercice contient tous les champs requis"""
        response = client.get("/api/exercises")
        exercises = response.json()

        required_fields = {
            "name",
            "description",
            "icon",
            "video_url",
            "default_duration",
            "difficulty",
            "has_jump",
            "access_tier",
            "metadata",
        }

        for exercise in exercises:
            exercise_fields = set(exercise.keys())
            assert required_fields.issubset(
                exercise_fields
            ), f"Champs manquants: {required_fields - exercise_fields}"

    def test_get_exercises_metadata_structure(self):
        """Vérifie la structure des métadonnées des exercices"""
        response = client.get("/api/exercises")
        exercises = response.json()

        for exercise in exercises:
            metadata = exercise["metadata"]
            assert "muscles_targeted" in metadata
            assert "equipment_needed" in metadata
            assert "calories_per_min" in metadata
            assert isinstance(metadata["muscles_targeted"], list)
            assert isinstance(metadata["equipment_needed"], list)
            assert isinstance(metadata["calories_per_min"], (int, float))


class TestGetExerciseByName:
    """Tests pour l'endpoint GET /api/exercises/{exercise_name}"""

    def test_get_exercise_by_name_success(self):
        """Vérifie qu'on peut récupérer un exercice par son nom"""
        response = client.get("/api/exercises/Push-ups")

        assert response.status_code == 200
        exercise = response.json()
        assert exercise["name"] == "Push-ups"
        assert exercise["icon"] == "💪"

    def test_get_exercise_by_name_case_insensitive(self):
        """Vérifie que la recherche est insensible à la casse"""
        response1 = client.get("/api/exercises/push-ups")
        response2 = client.get("/api/exercises/PUSH-UPS")
        response3 = client.get("/api/exercises/Push-ups")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Tous doivent retourner le même exercice
        assert response1.json()["name"] == response2.json()["name"]
        assert response2.json()["name"] == response3.json()["name"]

    def test_get_exercise_not_found(self):
        """Vérifie qu'un exercice inexistant retourne 404"""
        response = client.get("/api/exercises/NonexistentExercise")

        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"].lower()

    def test_get_exercise_returns_complete_data(self):
        """Vérifie qu'un exercice spécifique retourne toutes les données"""
        response = client.get("/api/exercises/Air%20Squat")

        assert response.status_code == 200
        exercise = response.json()

        # Vérifier les champs principaux
        assert exercise["name"] == "Air Squat"
        assert exercise["difficulty"] == "easy"
        assert exercise["has_jump"] is False
        assert exercise["access_tier"] == "free"

        # Vérifier les métadonnées
        assert "quadriceps" in exercise["metadata"]["muscles_targeted"]
        assert "glutes" in exercise["metadata"]["muscles_targeted"]


class TestExerciseFiltering:
    """Tests pour les filtres sur les exercices"""

    def test_filter_by_difficulty(self):
        """Vérifie qu'on peut filtrer les exercices par difficulté"""
        response = client.get("/api/exercises")
        exercises = response.json()

        easy_exercises = [ex for ex in exercises if ex["difficulty"] == "easy"]
        medium_exercises = [ex for ex in exercises if ex["difficulty"] == "medium"]

        assert len(easy_exercises) > 0
        assert len(medium_exercises) > 0

    def test_filter_by_access_tier(self):
        """Vérifie qu'on peut filtrer par tier d'accès"""
        response = client.get("/api/exercises")
        exercises = response.json()

        free_exercises = [ex for ex in exercises if ex["access_tier"] == "free"]

        assert len(free_exercises) > 0
        # Tous les exercices du mock doivent être gratuits
        assert all(ex["access_tier"] == "free" for ex in exercises)

    def test_filter_no_jump_exercises(self):
        """Vérifie qu'on peut identifier les exercices sans saut"""
        response = client.get("/api/exercises")
        exercises = response.json()

        no_jump_exercises = [ex for ex in exercises if not ex["has_jump"]]

        assert len(no_jump_exercises) > 0


class TestAPIDocumentation:
    """Tests pour la documentation de l'API"""

    def test_openapi_schema_available(self):
        """Vérifie que le schéma OpenAPI est disponible"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/exercises" in schema["paths"]

    def test_docs_endpoint_available(self):
        """Vérifie que la documentation Swagger est accessible"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestCORS:
    """Tests pour la configuration CORS"""

    def test_cors_headers_present(self):
        """Vérifie que les headers CORS sont présents"""
        response = client.get(
            "/api/exercises", headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
