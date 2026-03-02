"""Tests for interactive categorization prompts."""

from __future__ import annotations

from datetime import date

from bankparser.interactive import prompt_categorize
from bankparser.models import Transaction


class TestPromptCategorize:
    def test_empty_returns_zero(self, tmp_db):
        assert prompt_categorize({}, tmp_db) == 0

    def test_user_selects_category_and_pattern(self, tmp_db, monkeypatch):
        txs = [Transaction(date=date(2026, 1, 1), description="OXXO TONALA", amount=48.5)]
        uncategorized = {"OXXO TONALA": txs}

        cats = tmp_db.list_user_categories()
        groceries_idx = cats.index("Groceries") + 1

        # Simulate: select category number, then enter custom pattern
        inputs = iter([str(groceries_idx), "OXXO"])
        monkeypatch.setattr("click.prompt", lambda *a, **kw: next(inputs))

        result = prompt_categorize(uncategorized, tmp_db)
        assert result == 1
        assert tmp_db.match_category("OXXO TONALA") == "Groceries"

    def test_user_accepts_default_pattern(self, tmp_db, monkeypatch):
        txs = [
            Transaction(date=date(2026, 1, 1), description="FARMACIA BENAVIDES", amount=120.0)
        ]
        uncategorized = {"FARMACIA BENAVIDES": txs}

        cats = tmp_db.list_user_categories()
        health_idx = cats.index("Health") + 1

        # Simulate: select category, then press Enter (empty = use full description)
        inputs = iter([str(health_idx), ""])
        monkeypatch.setattr("click.prompt", lambda *a, **kw: next(inputs))

        result = prompt_categorize(uncategorized, tmp_db)
        assert result == 1
        assert tmp_db.match_category("FARMACIA BENAVIDES GDL") == "Health"

    def test_user_skips_with_zero(self, tmp_db, monkeypatch):
        txs = [Transaction(date=date(2026, 1, 1), description="MYSTERY SHOP", amount=99.0)]
        uncategorized = {"MYSTERY SHOP": txs}

        inputs = iter(["0"])
        monkeypatch.setattr("click.prompt", lambda *a, **kw: next(inputs))

        result = prompt_categorize(uncategorized, tmp_db)
        assert result == 0
        assert tmp_db.rule_count() == 0

    def test_user_quits_with_q(self, tmp_db, monkeypatch):
        txs1 = [Transaction(date=date(2026, 1, 1), description="SHOP A", amount=50.0)]
        txs2 = [Transaction(date=date(2026, 1, 2), description="SHOP B", amount=60.0)]
        uncategorized = {"SHOP A": txs1, "SHOP B": txs2}

        inputs = iter(["q"])
        monkeypatch.setattr("click.prompt", lambda *a, **kw: next(inputs))

        result = prompt_categorize(uncategorized, tmp_db)
        assert result == 0
        assert tmp_db.rule_count() == 0
