from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import ReconTarget
from app.services.recon_service import ADReconService
from app.services.graph_service import GraphService
from app.core.database import get_driver
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

_recon_status: dict = {"running": False, "progress": 0, "message": "", "done": False, "error": None}


async def _run_recon(target: ReconTarget):
    global _recon_status
    _recon_status = {"running": True, "progress": 0, "message": "Connexion au DC...", "done": False, "error": None}

    svc = ADReconService(
        dc_host=target.dc_host,
        domain=target.domain,
        username=target.username,
        password=target.password,
        port=target.ldap_port,
        use_ssl=target.use_ssl,
    )

    try:
        svc.connect()
        driver = await get_driver()

        async with driver.session() as session:
            graph = GraphService(session)

            _recon_status["message"] = "Énumération du domaine..."
            _recon_status["progress"] = 10
            domain_info = svc.get_domain_info()
            await graph.ingest_domain(domain_info)

            _recon_status["message"] = "Énumération des utilisateurs..."
            _recon_status["progress"] = 25
            users = svc.enumerate_users()
            await graph.ingest_users(users)

            _recon_status["message"] = "Énumération des groupes..."
            _recon_status["progress"] = 50
            groups = svc.enumerate_groups()
            await graph.ingest_groups(groups)

            _recon_status["message"] = "Énumération des machines..."
            _recon_status["progress"] = 70
            computers = svc.enumerate_computers()
            await graph.ingest_computers(computers)

            _recon_status["message"] = "Finalisation..."
            _recon_status["progress"] = 90

        _recon_status = {"running": False, "progress": 100, "message": "Reconnaissance terminée.", "done": True, "error": None}

    except Exception as e:
        logger.error(f"Recon error: {e}")
        _recon_status = {"running": False, "progress": 0, "message": "", "done": False, "error": str(e)}
    finally:
        svc.disconnect()


@router.post("/start")
async def start_recon(target: ReconTarget, background_tasks: BackgroundTasks):
    if _recon_status.get("running"):
        raise HTTPException(status_code=409, detail="Reconnaissance déjà en cours")
    background_tasks.add_task(_run_recon, target)
    return {"message": "Reconnaissance démarrée en arrière-plan"}


@router.get("/status")
async def get_status():
    return _recon_status


@router.delete("/clear")
async def clear_data():
    driver = await get_driver()
    async with driver.session() as session:
        graph = GraphService(session)
        await graph.clear_graph()
    return {"message": "Graphe effacé"}
