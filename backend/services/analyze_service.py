import logging

from fastapi import HTTPException, status

from ..ai import analyze as ai_analyze
from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger(__name__)


def run_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    logger.info(
        "analyze: incident=%s rescuer=%s scenario=%s",
        req.incident_id,
        req.rescuer_id,
        req.scenario.value,
    )

    try:
        result = ai_analyze(req.scenario.value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return AnalyzeResponse.model_validate(result)
