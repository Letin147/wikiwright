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


class FileNode(Contract):
    """One python file in the import graph (EXP-03)."""

    path: str
    in_degree: int = 0
    out_degree: int = 0
    role: str = "peripheral"  # entry | core | peripheral


class Cluster(Contract):
    """A directory-level business module; the only place LLM is allowed (naming)."""

    dir_path: str
    files: list[str]
    business_name: str = ""
    name_grounded: bool = False


class ModuleMap(Contract):
    """Cartographer output: file-level import graph + named directory clusters."""

    source: str
    nodes: list[FileNode]
    edges: list[tuple[str, str]]  # (importer, imported) relative paths
    clusters: list[Cluster]
    entry_candidates: list[str]
    core_files: list[str]
    cycles: list[list[str]] = []
