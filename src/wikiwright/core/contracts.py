"""Pydantic contracts: every agent's input/output schemas live here (single source of truth).

Agents exchange data ONLY through these models — a node whose output fails
its contract must retry or degrade explicitly, never pass broken data onward.
"""

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    """Base model for all agent IO contracts."""

    model_config = ConfigDict(frozen=True)
