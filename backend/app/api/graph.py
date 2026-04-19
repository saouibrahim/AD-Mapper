from fastapi import APIRouter
from app.services.graph_service import GraphService
from app.core.database import get_driver

router = APIRouter()


@router.get("/full")
async def get_full_graph():
    driver = await get_driver()
    async with driver.session() as session:
        svc = GraphService(session)
        return await svc.get_full_graph()


@router.get("/attack-paths")
async def get_attack_paths():
    driver = await get_driver()
    async with driver.session() as session:
        svc = GraphService(session)
        return await svc.get_attack_paths()


@router.get("/statistics")
async def get_statistics():
    driver = await get_driver()
    async with driver.session() as session:
        svc = GraphService(session)
        return await svc.get_statistics()
