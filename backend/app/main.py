from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .api import exercises, workouts

app = FastAPI(
    title="Virtual AI Coach Backend",
    description="Backend for generating personalized workout videos",
    version="0.1.0",
)

# Configuration CORS pour permettre les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Workout-ID",
        "X-Exercise-Count",
    ],  # Exposer les headers personnalisés
)

# Inclusion des routers
app.include_router(exercises.router)
app.include_router(workouts.router)


@app.get("/", tags=["Root"])
async def root():
    """
    Redirige vers la documentation Swagger UI.
    """
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de vérification de santé du serveur.
    Retourne un statut 200 OK si le serveur est opérationnel.
    """
    return {"status": "healthy", "message": "Virtual AI Coach Backend is running"}
