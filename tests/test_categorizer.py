"""Tests for the database and categorizer."""

import sqlite3
from datetime import date

import pytest

from bankparser.categorizer import Categorizer
from bankparser.database import SYSTEM_CATEGORIES
from bankparser.models import Transaction, TransactionType


class TestDatabase:
    def test_initialize_creates_tables(self, tmp_db):
        assert tmp_db.category_count() > 0
        assert tmp_db.rule_count() == 0

    def test_default_categories_seeded(self, tmp_db):
        cats = tmp_db.list_categories()
        names = [c["name"] for c in cats]
        assert "Shopping" in names
        assert "Food & Dining" in names
        assert "Uncategorized" in names

    def test_add_category(self, tmp_db):
        initial = tmp_db.category_count()
        tmp_db.add_category("Pets", icon="🐕")
        assert tmp_db.category_count() == initial + 1

    def test_add_duplicate_category_raises(self, tmp_db):
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db.add_category("Shopping")  # Already exists

    def test_remove_category(self, tmp_db):
        tmp_db.add_category("Temporary")
        tmp_db.add_rule("TEMP_STORE", "Temporary")
        tmp_db.remove_category("Temporary")

        cats = tmp_db.list_categories()
        names = [c["name"] for c in cats]
        assert "Temporary" not in names

    def test_add_rule(self, tmp_db):
        initial = tmp_db.rule_count()
        tmp_db.add_rule("COSTCO", "Groceries", priority=15)
        assert tmp_db.rule_count() == initial + 1

    def test_remove_rule(self, tmp_db):
        tmp_db.add_rule("DELETE_ME", "Shopping")
        rules = tmp_db.list_rules()
        rule_id = [r for r in rules if r["pattern"] == "DELETE_ME"][0]["id"]

        tmp_db.remove_rule(rule_id)
        rules = tmp_db.list_rules()
        patterns = [r["pattern"] for r in rules]
        assert "DELETE_ME" not in patterns

    def test_match_category_basic(self, tmp_db):
        tmp_db.add_rule("AMAZON", "Shopping")
        tmp_db.add_rule("NETFLIX", "Subscriptions")
        assert tmp_db.match_category("AMAZON MX MARKETPLACE") == "Shopping"
        assert tmp_db.match_category("NETFLIX.COM") == "Subscriptions"
        assert tmp_db.match_category("UNKNOWN MERCHANT XYZ") == "Uncategorized"

    def test_match_category_case_insensitive(self, tmp_db):
        tmp_db.add_rule("AMAZON", "Shopping")
        assert tmp_db.match_category("amazon mx marketplace") == "Shopping"

    def test_match_category_priority(self, tmp_db):
        tmp_db.add_rule("PAGO", "Shopping", priority=5)
        tmp_db.add_rule("GRACIAS POR SU PAGO", "Payment", priority=100)
        assert tmp_db.match_category("GRACIAS POR SU PAGO EN LINEA") == "Payment"

    def test_match_bank_specific_rule(self, tmp_db):
        tmp_db.add_rule("SPECIAL_AMEX", "Entertainment", bank="amex", priority=20)
        assert tmp_db.match_category("SPECIAL_AMEX STORE", bank="amex") == "Entertainment"
        # With a different bank, the rule shouldn't match (unless * rules match)
        assert tmp_db.match_category("SPECIAL_AMEX STORE", bank="bbva") == "Uncategorized"

    def test_add_duplicate_category_does_not_corrupt_connection(self, tmp_db):
        """After a duplicate category insert fails, the connection should still work."""
        tmp_db.add_category("TestCat")
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db.add_category("TestCat")  # duplicate
        # Connection should still be usable
        cats = tmp_db.list_categories()
        assert any(c["name"] == "TestCat" for c in cats)

    def test_list_rules_filtered_by_bank(self, tmp_db):
        tmp_db.add_rule("AMAZON", "Shopping")
        tmp_db.add_rule("BBVA_ONLY", "Shopping", bank="bbva")
        rules = tmp_db.list_rules(bank="bbva")
        patterns = [r["pattern"] for r in rules]
        # Should include bank-specific AND wildcard rules
        assert "BBVA_ONLY" in patterns
        assert "AMAZON" in patterns  # wildcard rule

    def test_list_user_categories(self, tmp_db):
        user_cats = tmp_db.list_user_categories()
        # Should include user-facing categories
        assert "Shopping" in user_cats
        assert "Food & Dining" in user_cats
        # Should exclude system categories
        for sys_cat in SYSTEM_CATEGORIES:
            assert sys_cat not in user_cats


class TestCategorizer:
    def test_type_override(self, tmp_db):
        cat = Categorizer(tmp_db)
        tx = Transaction(
            date=date(2026, 1, 1),
            description="ANYTHING",
            amount=100.0,
            tx_type=TransactionType.PAYMENT,
        )
        assert cat.categorize(tx) == "Payment"

    def test_interest_override(self, tmp_db):
        cat = Categorizer(tmp_db)
        tx = Transaction(
            date=date(2026, 1, 1),
            description="INTERÉS FINANCIERO",
            amount=5000.0,
            tx_type=TransactionType.INTEREST,
        )
        assert cat.categorize(tx) == "Interest"

    def test_rule_matching_for_charges(self, tmp_db):
        tmp_db.add_rule("AMAZON", "Shopping")
        cat = Categorizer(tmp_db)
        tx = Transaction(
            date=date(2026, 1, 1),
            description="AMAZON MX MARKETPLACE*A MEXICO CITY",
            amount=499.0,
            bank="amex",
        )
        assert cat.categorize(tx) == "Shopping"

    def test_uncategorized_fallback(self, tmp_db):
        cat = Categorizer(tmp_db)
        tx = Transaction(
            date=date(2026, 1, 1),
            description="TOTALLY UNKNOWN MERCHANT 12345",
            amount=99.0,
        )
        assert cat.categorize(tx) == "Uncategorized"

    def test_categorize_all(self, tmp_db, sample_transactions):
        tmp_db.add_rule("AMAZON", "Shopping")
        cat = Categorizer(tmp_db)
        result = cat.categorize_all(sample_transactions)

        # All should have a category
        for tx in result:
            assert tx.category != ""

        # Check specific ones
        payment = [tx for tx in result if tx.tx_type == TransactionType.PAYMENT][0]
        assert payment.category == "Payment"

        amazon = [tx for tx in result if "AMAZON" in tx.description][0]
        assert amazon.category == "Shopping"

        interest = [tx for tx in result if tx.tx_type == TransactionType.INTEREST][0]
        assert interest.category == "Interest"

    def test_collect_uncategorized(self, tmp_db):
        cat = Categorizer(tmp_db)
        txs = [
            Transaction(date=date(2026, 1, 1), description="OXXO TONALA", amount=48.0),
            Transaction(date=date(2026, 1, 2), description="OXXO TONALA", amount=35.0),
            Transaction(date=date(2026, 1, 3), description="RANDOM SHOP", amount=100.0),
        ]
        cat.categorize_all(txs)
        groups = cat.collect_uncategorized(txs)
        assert "OXXO TONALA" in groups
        assert len(groups["OXXO TONALA"]) == 2
        assert "RANDOM SHOP" in groups
        assert len(groups["RANDOM SHOP"]) == 1

    def test_recategorize_uncategorized(self, tmp_db):
        cat = Categorizer(tmp_db)
        txs = [
            Transaction(date=date(2026, 1, 1), description="OXXO TONALA", amount=48.0),
            Transaction(
                date=date(2026, 1, 2),
                description="PAGO",
                amount=-1000.0,
                tx_type=TransactionType.PAYMENT,
            ),
        ]
        cat.categorize_all(txs)
        assert txs[0].category == "Uncategorized"
        assert txs[1].category == "Payment"

        # Add a rule and recategorize
        tmp_db.add_rule("OXXO", "Groceries")
        cat.recategorize_uncategorized(txs)
        assert txs[0].category == "Groceries"
        assert txs[1].category == "Payment"  # unchanged
