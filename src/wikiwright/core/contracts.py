"""Pydantic contracts: every agent's input/output schemas live here (single source of truth).

Agents exchange data ONLY through these models — a node whose output fails
its contract must retry or degrade explicitly, never pass broken data onward.
"""

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    """Base model for all agent IO contracts."""

    model_config = ConfigDict(frozen=True)


class IngestResult(Contract):
    """Outcome of one Scout ingestion run (EXP-02)."""

    source: str
    run_id: str
    repo_dir: str
    license_family: str | None = None
    files_total: int = 0
    files_indexed: int = 0
    files_filtered: int = 0
    chunks: int = 0
    cache_hit: bool = False
    duration_s: float = 0.0
