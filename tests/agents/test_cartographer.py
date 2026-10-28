"""Cartographer tests: graph edges/roles, cycles, determinism, LLM naming cache."""

from pathlib import Path

from wikiwright.agents.cartographer import build_import_graph, cartographize, detect_cycles


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    def chat(self, messages, **kwargs):  # noqa: ARG002 (test double)
        self.calls += 1
        return '{"business_name": "核心|core"}', None


def _fixture(root: Path) -> Path:
    (root / "proj").mkdir()
    (root / "proj" / "__init__.py").write_text("from . import alpha\nfrom . import beta\n")
    (root / "proj" / "alpha.py").write_text("from .beta import util\nVALUE = 1\n")
    (root / "proj" / "beta.py").write_text("def util():\n    return 1\n")
    (root / "proj" / "gamma.py").write_text("import proj.alpha\n")
    (root / "setup.py").write_text("from proj import alpha\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("import proj\n")
    (root / "vendor").mkdir()
    (root / "vendor" / "lib.py").write_text("x = 1\n")
    return root


def test_graph_edges_and_roles(tmp_path):
    nodes, edges = build_import_graph(_fixture(tmp_path))
    paths = {node.path: node for node in nodes}
    assert "vendor/lib.py" not in paths
    assert not any(path.startswith("tests/") for path in paths)
    assert ("proj/alpha.py", "proj/beta.py") in edges
    assert ("proj/gamma.py", "proj/alpha.py") in edges
    assert ("proj/__init__.py", "proj/alpha.py") in edges
    assert paths["proj/alpha.py"].role == "core"  # in_degree 3: __init__ + gamma + setup
    assert paths["proj/beta.py"].role == "peripheral"  # in_degree 2 < CORE_MIN 3
    assert paths["proj/__init__.py"].role == "core"  # aggregator rule
    assert paths["setup.py"].role == "entry"


def test_cycle_detection(tmp_path):
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import a\n")
    _, edges = build_import_graph(tmp_path)
    cycles = detect_cycles(edges)
    assert any({"a.py", "b.py"} <= set(cycle) for cycle in cycles)


def test_offline_map_never_calls_llm(tmp_path):
    module_map = cartographize(str(_fixture(tmp_path)), cache_dir=tmp_path / "c", offline=True)
    assert module_map.clusters
    assert all(not cluster.name_grounded for cluster in module_map.clusters)


def test_naming_cached_and_map_deterministic(tmp_path):
    root = _fixture(tmp_path)
    cache = tmp_path / "cache"

    first_llm = FakeLLM()
    first = cartographize(str(root), cache_dir=cache, llm=first_llm)
    assert first_llm.calls >= 1
    assert all(cluster.name_grounded for cluster in first.clusters)

    second_llm = FakeLLM()
    second = cartographize(str(root), cache_dir=cache, llm=second_llm)
    assert second_llm.calls == 0  # names fully cached -> zero LLM cost (C-09)
    assert first.model_dump_json() == second.model_dump_json()


def test_cluster_change_renames_only_that_cluster(tmp_path):
    root = _fixture(tmp_path)
    cache = tmp_path / "cache"
    cartographize(str(root), cache_dir=cache, llm=FakeLLM())

    (root / "proj" / "delta.py").write_text("from .beta import util\n")
    third_llm = FakeLLM()
    cartographize(str(root), cache_dir=cache, llm=third_llm)
    assert third_llm.calls == 1  # only the changed proj/ cluster re-named
