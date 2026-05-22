from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..ai import Analyzer, ImageAnalyzer, get_analyzer, get_image_analyzer
from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse
from ..services.analyze_service import run_analyze, run_analyze_image

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(
    req: AnalyzeRequest,
    analyzer: Annotated[Analyzer, Depends(get_analyzer)],
) -> AnalyzeResponse:
    return run_analyze(req, analyzer)


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image_endpoint(
    image: Annotated[UploadFile, File(description="Кадр с места ЧС (JPEG/PNG)")],
    incident_id: Annotated[str, Form()],
    rescuer_id: Annotated[str, Form()],
    analyzer: Annotated[ImageAnalyzer, Depends(get_image_analyzer)],
) -> AnalyzeResponse:
    image_bytes = await image.read()
    return run_analyze_image(image_bytes, incident_id, rescuer_id, analyzer)
