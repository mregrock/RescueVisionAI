from pydantic import BaseModel, ConfigDict, Field

from .common import RiskLevel, Scenario, VictimStatus


class Gps(BaseModel):
    lat: float
    lon: float


class AnalyzeRequest(BaseModel):
    incident_id: str
    rescuer_id: str
    scenario: Scenario
    gps: Gps | None = None
    timestamp: str | None = Field(default=None, description="ISO 8601")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "incident_id": "inc-001",
                "rescuer_id": "resc-42",
                "scenario": "single_unconscious",
                "gps": {"lat": 55.7558, "lon": 37.6173},
                "timestamp": "2026-05-14T12:34:56Z",
            }
        }
    )


class Scene(BaseModel):
    people_count: int = Field(ge=0)
    observations: list[str] = Field(default_factory=list)


class Victim(BaseModel):
    id: int
    priority: int = Field(ge=1, le=4, description="1 — наивысший приоритет")
    severity_score: float = Field(ge=0.0, le=1.0)
    severity_label: RiskLevel
    status: VictimStatus
    bbox: list[int] | None = Field(
        default=None,
        min_length=4,
        max_length=4,
        description="[x1, y1, x2, y2]; null в mock-режиме",
    )
    signals: list[str] = Field(default_factory=list)
    first_aid: list[str] = Field(default_factory=list)
    protocols: list[str] = Field(default_factory=list)


class Action(BaseModel):
    id: str
    title: str
    description: str
    priority: int = Field(ge=1, description="Порядок в чеклисте")
    critical: bool = False


class Quality(BaseModel):
    low_confidence: bool
    notes: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    analysis_id: str
    overall_risk: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    scene: Scene
    victims: list[Victim] = Field(default_factory=list)
    recommended_actions: list[Action] = Field(default_factory=list)
    protocols: list[str] = Field(default_factory=list)
    quality: Quality
    disclaimer: str
    scenario: Scenario | None = None
