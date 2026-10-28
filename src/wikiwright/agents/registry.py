"""Role registry — adding a role means registering here, nothing else (plugin-style).

Populated as roles land: EXP-02 (scout), EXP-03 (cartographer), EXP-04 (analyst), ...
"""

ROLE_REGISTRY: dict[str, type] = {}
