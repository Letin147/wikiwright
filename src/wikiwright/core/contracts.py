"""Pydantic contracts: every agent's input/output schemas live here (single source of truth).

Agents exchange data ONLY through these models — a node whose output fails
its contract must retry or degrade explicitly, never pass broken data onward.
"""

from pydantic import BaseModel, ConfigDict, model_validator


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


class Entity(Contract):
    """A code object an Analyst found; ref is mandatory (it IS a code fact)."""

    name: str
    kind: str  # class | function | constant
    summary: str
    ref: str  # "path:symbol"


class InterfaceItem(Contract):
    """Public-facing symbol of a module; ref is mandatory."""

    symbol: str
    summary: str
    ref: str


class Relation(Contract):
    """How this module touches another module/file; ref is mandatory."""

    target: str  # path or dir
    kind: str  # imports | uses
    ref: str


class Conclusion(Contract):
    """A statement about the module: either grounded in code or explicitly unsure."""

    statement: str
    ref: str = ""
    unsure: bool = False

    @model_validator(mode="after")
    def _ref_or_unsure(self) -> "Conclusion":
        if not self.ref and not self.unsure:
            raise ValueError("conclusion without ref must set unsure=true")
        return self


class ModuleUnderstanding(Contract):
    """Analyst output for one cluster (EXP-04 contract, strictly validated)."""

    module: str  # cluster dir_path
    business_name: str = ""
    files: list[str] = []
    responsibility: str = ""
    entities: list[Entity] = []
    public_interface: list[InterfaceItem] = []
    relations: list[Relation] = []
    conclusions: list[Conclusion] = []
    invalid_refs: list[str] = []  # refs that failed automatic verification


class SkippedModule(Contract):
    module: str
    reason: str


class AnalysisReport(Contract):
    """Reduce output of the Analyst map-reduce."""

    source: str
    understandings: list[ModuleUnderstanding] = []
    skipped: list[SkippedModule] = []
    total_conclusions: int = 0
    unsure_conclusions: int = 0
    invalid_refs: int = 0
    llm_calls: int = 0
    cost_usd: float = 0.0
    cache_hit: bool = False
