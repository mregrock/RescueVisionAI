from fastapi import APIRouter

from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse
from ..services.analyze_service import run_analyze

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    return run_analyze(req)
