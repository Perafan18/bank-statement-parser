"""SQLite database for category rules and merchant mappings."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Default location: ~/.bankparser/bankparser.db
DEFAULT_DB_PATH = Path.home() / ".bankparser" / "bankparser.db"

# ─── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    parent_name TEXT,                          -- optional parent for subcategories
    icon        TEXT DEFAULT '',               -- emoji or icon name
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS category_rules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern       TEXT NOT NULL,               -- substring match on description (case-insensitive)
    category_name TEXT NOT NULL REFERENCES categories(name),
    bank          TEXT DEFAULT '*',            -- '*' = all banks, or 'amex', 'bbva', 'hsbc'
    priority      INTEGER DEFAULT 0,           -- higher = checked first
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rules_priority ON category_rules(priority DESC);
CREATE INDEX IF NOT EXISTS idx_rules_bank ON category_rules(bank);
"""

# ─── Default seed data ────────────────────────────────────────────────────────

DEFAULT_CATEGORIES = [
    # Top-level
    ("Shopping", None, "🛒"),
    ("Food & Dining", None, "🍽️"),
    ("Groceries", None, "🥑"),
    ("Transportation", None, "🚗"),
    ("Subscriptions", None, "📱"),
    ("Education", None, "📚"),
    ("Technology", None, "💻"),
    ("Insurance", None, "🛡️"),
    ("Telecom", None, "📡"),
    ("Entertainment", None, "🎭"),
    ("Home", None, "🏠"),
    ("Utilities", None, "💡"),
    ("Health", None, "🏥"),
    ("Travel", None, "✈️"),
    ("Savings", None, "🏦"),
    ("Accounting", None, "📊"),
    ("Payment", None, "💳"),
    ("Interest", None, "📈"),
    ("Fees", None, "💸"),
    ("Tax", None, "🧾"),
    ("MSI Installment", None, "📅"),
    ("MSI Adjustment", None, "🔄"),
    ("Uncategorized", None, "❓"),
]

# Categories managed by type-based overrides (not shown in interactive prompts)
SYSTEM_CATEGORIES = frozenset(
    {
        "Payment",
        "Interest",
        "Fees",
        "Tax",
        "MSI Installment",
        "MSI Adjustment",
        "Uncategorized",
    }
)


# ─── Database class ───────────────────────────────────────────────────────────


class Database:
    """Manages the SQLite database for categories and rules."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def initialize(self) -> None:
        """Create tables and seed default data if empty."""
        self.conn.executescript(SCHEMA_SQL)

        # Check if categories exist
        count = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count == 0:
            self._seed_defaults()

        self.conn.commit()

    def _seed_defaults(self) -> None:
        """Insert default categories."""
        for name, parent, icon in DEFAULT_CATEGORIES:
            self.conn.execute(
                "INSERT OR IGNORE INTO categories (name, parent_name, icon) VALUES (?, ?, ?)",
                (name, parent, icon),
            )

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Category CRUD ─────────────────────────────────────────────────────────

    def list_categories(self) -> list[dict]:
        """List all categories."""
        rows = self.conn.execute(
            "SELECT name, parent_name, icon FROM categories ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_user_categories(self) -> list[str]:
        """List category names excluding system-managed ones (for interactive prompts)."""
        rows = self.conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
        return [r["name"] for r in rows if r["name"] not in SYSTEM_CATEGORIES]

    def add_category(self, name: str, parent: str | None = None, icon: str = "") -> None:
        """Add a new category."""
        try:
            self.conn.execute(
                "INSERT INTO categories (name, parent_name, icon) VALUES (?, ?, ?)",
                (name, parent, icon),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise

    def remove_category(self, name: str) -> None:
        """Remove a category and its associated rules."""
        self.conn.execute("DELETE FROM category_rules WHERE category_name = ?", (name,))
        self.conn.execute("DELETE FROM categories WHERE name = ?", (name,))
        self.conn.commit()

    # ── Rule CRUD ─────────────────────────────────────────────────────────────

    def list_rules(self, bank: str | None = None) -> list[dict]:
        """List category rules, optionally filtered by bank."""
        if bank:
            rows = self.conn.execute(
                "SELECT id, pattern, category_name, bank, priority "
                "FROM category_rules WHERE bank IN (?, '*') ORDER BY priority DESC",
                (bank,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, pattern, category_name, bank, priority "
                "FROM category_rules ORDER BY priority DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def add_rule(self, pattern: str, category: str, bank: str = "*", priority: int = 10) -> None:
        """Add a new categorization rule."""
        try:
            self.conn.execute(
                "INSERT INTO category_rules (pattern, category_name, bank, priority) "
                "VALUES (?, ?, ?, ?)",
                (pattern, category, bank, priority),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise

    def remove_rule(self, rule_id: int) -> None:
        """Remove a rule by ID."""
        self.conn.execute("DELETE FROM category_rules WHERE id = ?", (rule_id,))
        self.conn.commit()

    # ── Matching ──────────────────────────────────────────────────────────────

    def match_category(self, description: str, bank: str = "*") -> str:
        """Find the best matching category for a transaction description.

        Returns the category name or 'Uncategorized' if no match.
        """
        rows = self.conn.execute(
            "SELECT pattern, category_name FROM category_rules "
            "WHERE bank IN (?, '*') ORDER BY priority DESC",
            (bank,),
        ).fetchall()

        desc_upper = description.upper()
        for row in rows:
            if row["pattern"].upper() in desc_upper:
                return str(row["category_name"])

        return "Uncategorized"

    # ── Stats ─────────────────────────────────────────────────────────────────

    def rule_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM category_rules").fetchone()[0])

    def category_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0])
