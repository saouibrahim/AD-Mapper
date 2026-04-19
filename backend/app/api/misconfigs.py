from fastapi import APIRouter
from app.services.misconfig_service import MisconfigService
from app.core.database import get_driver

router = APIRouter()


@router.get("/")
async def get_misconfigs():
    driver = await get_driver()
    async with driver.session() as session:
        svc = MisconfigService(session)
        return await svc.detect_all()
