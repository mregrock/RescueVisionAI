from pydantic import BaseModel, Field


class ProtocolSummary(BaseModel):
    """Короткая карточка протокола для списка."""

    id: str
    title: str
    tags: list[str] = Field(default_factory=list)


class Protocol(BaseModel):
    """Полный протокол с шагами и предупреждениями."""

    id: str
    title: str
    tags: list[str] = Field(default_factory=list)
    summary: str | None = None
    steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str | None = None


class ProtocolsList(BaseModel):
    protocols: list[ProtocolSummary]
