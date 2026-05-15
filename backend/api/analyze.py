from typing import Annotated

from fastapi import APIRouter, Depends

from ..ai import Analyzer, get_analyzer
from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse
from ..services.analyze_service import run_analyze

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(
    req: AnalyzeRequest,
    analyzer: Annotated[Analyzer, Depends(get_analyzer)],
) -> AnalyzeResponse:
    return run_analyze(req, analyzer)
