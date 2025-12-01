import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .api import exercises, workouts

# Charger les variables d'environnement depuis .env
load_dotenv()

app = FastAPI(
    title="Virtual AI Coach Backend",
    description="Backend for generating personalized workout videos",
    version="0.1.0",
)

# Configuration CORS sécurisée pour production (Vercel + Railway + Supabase)
# Récupérer l'URL du frontend depuis les variables d'environnement
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Liste des origines autorisées
ALLOWED_ORIGINS = [
    FRONTEND_URL,  # URL Vercel en production
    "http://localhost:3000",  # Frontend local en développement
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://virtual-ai-coach.vercel.app",
    "https://virtual-ai-coach-git-dev-johans-projects-1eb56e49.vercel.app",
    "https://tyswee.com",
]

# Ajouter les domaines Vercel preview si configurés (séparés par des virgules)
VERCEL_PREVIEW_DOMAINS = os.getenv("VERCEL_PREVIEW_DOMAINS", "")
if VERCEL_PREVIEW_DOMAINS:
    ALLOWED_ORIGINS.extend(VERCEL_PREVIEW_DOMAINS.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Nécessaire pour les cookies/auth Supabase
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "apikey",  # Header Supabase
        "x-client-info",  # Header Supabase
    ],
    expose_headers=[
        "X-Workout-ID",
        "X-Exercise-Count",
        "Content-Length",
        "Content-Range",
    ],
    max_age=3600,  # Cache preflight pendant 1 heure
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
