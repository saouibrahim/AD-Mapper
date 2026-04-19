from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api import recon, graph, misconfigs, reports, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AD Recon & Attack Path Mapper",
    description="Outil Red Team pour l'énumération et l'analyse des chemins d'attaque Active Directory",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentification"])
app.include_router(recon.router, prefix="/api/recon", tags=["Reconnaissance AD"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graphe d'attaque"])
app.include_router(misconfigs.router, prefix="/api/misconfigs", tags=["Mauvaises configurations"])
app.include_router(reports.router, prefix="/api/reports", tags=["Rapports Red Team"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AD Mapper"}
