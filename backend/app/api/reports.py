from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.models.schemas import ReportRequest
from app.services.report_service import ReportService
from app.services.graph_service import GraphService
from app.services.misconfig_service import MisconfigService
from app.core.database import get_driver
from app.core.config import settings
import os

router = APIRouter()


@router.post("/generate")
async def generate_report(req: ReportRequest):
    driver = await get_driver()
    async with driver.session() as session:
        graph_svc = GraphService(session)
        misconfig_svc = MisconfigService(session)

        stats = await graph_svc.get_statistics()
        misconfigs = await misconfig_svc.detect_all()
        paths = await graph_svc.get_attack_paths()

        # Filter by severity if requested
        if req.severity_filter:
            sf = [s.value for s in req.severity_filter]
            misconfigs = [m for m in misconfigs if m.get("severity") in sf]

        svc = ReportService(settings.REPORTS_DIR)
        filename = svc.generate(
            title=req.title,
            mission=req.mission,
            operator=req.operator,
            stats=stats,
            misconfigs=misconfigs if req.include_misconfigs else [],
            attack_paths=paths if req.include_paths else [],
        )

    return {"filename": filename, "download_url": f"/api/reports/download/{filename}"}


@router.get("/download/{filename}")
async def download_report(filename: str):
    filepath = os.path.join(settings.REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@router.get("/list")
async def list_reports():
    reports = []
    for f in os.listdir(settings.REPORTS_DIR):
        if f.endswith(".pdf"):
            path = os.path.join(settings.REPORTS_DIR, f)
            reports.append({"filename": f, "size": os.path.getsize(path)})
    return sorted(reports, key=lambda x: x["filename"], reverse=True)
