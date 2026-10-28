"""Router unit tests: cost math, .env parsing, missing key, budget fuse (no network)."""

import pytest

from wikiwright.models.router import (
    BudgetExceeded,
    LLMClient,
    LLMError,
    estimate_cost_usd,
    load_env_file,
)


def test_cost_math_uses_peak_prices():
    assert estimate_cost_usd("deepseek-flash", 1_000_000, 0, 0) == pytest.approx(0.30)
    assert estimate_cost_usd("deepseek-flash", 0, 1_000_000, 0) == pytest.approx(0.006)
    assert estimate_cost_usd("deepseek-flash", 0, 0, 1_000_000) == pytest.approx(1.20)
    assert estimate_cost_usd("deepseek-v4-pro", 1_000_000, 0, 0) == pytest.approx(1.32)


def test_env_file_parsing_skips_comments_and_broken_lines(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nA=1\nB=\"quoted\"\n\nBROKEN LINE\n", encoding="utf-8")
    assert load_env_file(env_file) == {"A": "1", "B": "quoted"}
    assert load_env_file(tmp_path / "missing.env") == {}


def test_missing_key_raises_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env in this cwd
    with pytest.raises(LLMError, match="DEEPSEEK_API_KEY"):
        LLMClient()


def test_budget_fuse_trips_before_any_network(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-only")
    monkeypatch.chdir(tmp_path)
    client = LLMClient(budget_cny=0.001)
    client.spent_usd = client.budget_usd  # simulate an exhausted run
    with pytest.raises(BudgetExceeded):
        client.chat([{"role": "user", "content": "x"}])
