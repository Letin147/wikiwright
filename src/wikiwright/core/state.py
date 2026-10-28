"""Global run state — the single source of truth shared by all graph nodes.

Fields arrive with EXP-02+ (ingest results) and EXP-03+ (module map).
Contract changes to this state must go through docs/adr/.
"""

from typing import TypedDict


class RunState(TypedDict, total=False):
    """One WikiWright run, from source repository to wiki output."""

    source: str  # repo URL or local path (EXP-02)
    run_id: str  # checkpoint/run identifier for replay (EXP-02)
