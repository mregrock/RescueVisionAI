import logging

from fastapi import HTTPException, status

from ..ai import Analyzer, ImageAnalyzer
from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger(__name__)


def run_analyze(req: AnalyzeRequest, analyzer: Analyzer) -> AnalyzeResponse:
    logger.info(
        "analyze: incident=%s rescuer=%s scenario=%s",
        req.incident_id,
        req.rescuer_id,
        req.scenario.value,
    )

    try:
        result = analyzer(req.scenario.value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return AnalyzeResponse.model_validate(result)


def run_analyze_image(
    image_bytes: bytes,
    incident_id: str,
    rescuer_id: str,
    analyzer: ImageAnalyzer,
) -> AnalyzeResponse:
    logger.info("analyze_image: incident=%s rescuer=%s bytes=%d", incident_id, rescuer_id, len(image_bytes))
    result = analyzer(image_bytes)
    return AnalyzeResponse.model_validate(result)
