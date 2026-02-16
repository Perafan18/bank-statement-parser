"""SQLite database for category rules and merchant mappings."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


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

DEFAULT_RULES = [
    # Shopping
    ("AMAZON", "Shopping", "*", 10),
    ("MERCADOPAGO", "Shopping", "*", 10),
    ("MERCPAGO", "Shopping", "*", 10),
    ("LIVERPOOL", "Shopping", "*", 10),
    ("PALACIO DE HIERRO", "Shopping", "*", 10),
    ("COSTCO", "Shopping", "*", 10),
    ("SORIANA", "Shopping", "*", 5),

    # Food & Dining
    ("REST ", "Food & Dining", "*", 10),
    ("RESTAUR", "Food & Dining", "*", 10),
    ("RAPPI", "Food & Dining", "*", 10),
    ("UBER EATS", "Food & Dining", "*", 15),
    ("DIDI FOOD", "Food & Dining", "*", 15),
    ("CARNICERIA", "Food & Dining", "*", 10),
    ("STARBUCKS", "Food & Dining", "*", 10),
    ("MCDONALD", "Food & Dining", "*", 10),

    # Groceries
    ("WALMART", "Groceries", "*", 10),
    ("CHEDRAUI", "Groceries", "*", 10),
    ("HEB ", "Groceries", "*", 10),
    ("LA COMER", "Groceries", "*", 10),
    ("OXXO", "Groceries", "*", 5),

    # Transportation
    ("UBRPAGOSMEX", "Transportation", "*", 10),
    ("UBER ", "Transportation", "*", 8),
    ("DIDI", "Transportation", "*", 8),
    ("GASOLINERA", "Transportation", "*", 10),
    ("PEMEX", "Transportation", "*", 10),

    # Subscriptions
    ("NETFLIX", "Subscriptions", "*", 10),
    ("SPOTIFY", "Subscriptions", "*", 10),
    ("APPLE.COM/BILL", "Subscriptions", "*", 10),
    ("MEDIUM MONTHLY", "Subscriptions", "*", 10),
    ("DISNEY+", "Subscriptions", "*", 10),
    ("YOUTUBE", "Subscriptions", "*", 10),
    ("PUSHOVER", "Subscriptions", "*", 10),
    ("WISPR", "Subscriptions", "*", 10),
    ("SHOPIFY", "Subscriptions", "*", 10),

    # Education
    ("PLATZI", "Education", "*", 10),
    ("SCALAHIGHER", "Education", "*", 10),
    ("UNIVERSIDAD", "Education", "*", 10),
    ("UTEL", "Education", "*", 10),
    ("LINGODA", "Education", "*", 10),
    ("UDEMY", "Education", "*", 10),
    ("COURSERA", "Education", "*", 10),

    # Technology
    ("DIGITALOCEAN", "Technology", "*", 10),
    ("LARAVEL FORGE", "Technology", "*", 10),
    ("MACSTORE", "Technology", "*", 10),
    ("CONEKTA", "Technology", "*", 10),
    ("WHITEPAPER", "Technology", "*", 10),
    ("GITHUB", "Technology", "*", 10),
    ("HEROKU", "Technology", "*", 10),
    ("AWS ", "Technology", "*", 10),

    # Insurance
    ("AXA SEGUROS", "Insurance", "*", 10),
    ("ZURICH ASEGURADORA", "Insurance", "*", 10),
    ("GNP SEGUROS", "Insurance", "*", 10),
    ("METLIFE", "Insurance", "*", 10),

    # Telecom
    ("ATT", "Telecom", "*", 5),
    ("TELCEL", "Telecom", "*", 10),
    ("TELMEX", "Telecom", "*", 10),
    ("IZZI", "Telecom", "*", 10),
    ("TOTALPLAY", "Telecom", "*", 10),

    # Entertainment
    ("VIAGOGO", "Entertainment", "*", 10),
    ("TICKETMASTER", "Entertainment", "*", 10),
    ("CINEPOLIS", "Entertainment", "*", 10),
    ("CINEMEX", "Entertainment", "*", 10),
    ("STEAM", "Entertainment", "*", 10),
    ("PLAYSTATION", "Entertainment", "*", 10),
    ("XBOX", "Entertainment", "*", 10),
    ("NINTENDO", "Entertainment", "*", 10),

    # Home
    ("COLCHONES", "Home", "*", 10),
    ("HOME DEPOT", "Home", "*", 10),
    ("IKEA", "Home", "*", 10),

    # Health
    ("FARMACIA", "Health", "*", 10),
    ("HOSPITAL", "Health", "*", 10),
    ("LABORATORIO", "Health", "*", 10),
    ("DOCTOR", "Health", "*", 5),

    # Finance
    ("AHORRO", "Savings", "*", 10),
    ("BUHOCONTABLE", "Accounting", "*", 10),

    # Statement-level
    ("GRACIAS POR SU PAGO", "Payment", "*", 100),
    ("PAGO RECIBIDO", "Payment", "*", 100),
    ("INTERÉS FINANCIERO", "Interest", "*", 100),
    ("INTERES FINANCIERO", "Interest", "*", 100),
    ("INTERESES ORDINARIOS", "Interest", "*", 100),
    ("CUOTA ANUAL", "Fees", "*", 100),
    ("COMISION", "Fees", "*", 50),
    ("IVA APLICABLE", "Tax", "*", 100),
    ("I.V.A.", "Tax", "*", 100),
    ("MONTO A DIFERIR", "MSI Adjustment", "*", 100),
    ("MESES EN AUTOMÁTICO", "MSI Installment", "*", 100),
]


# ─── Database class ───────────────────────────────────────────────────────────

class Database:
    """Manages the SQLite database for categories and rules."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def initialize(self):
        """Create tables and seed default data if empty."""
        self.conn.executescript(SCHEMA_SQL)

        # Check if categories exist
        count = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count == 0:
            self._seed_defaults()

        self.conn.commit()

    def _seed_defaults(self):
        """Insert default categories and rules."""
        for name, parent, icon in DEFAULT_CATEGORIES:
            self.conn.execute(
                "INSERT OR IGNORE INTO categories (name, parent_name, icon) VALUES (?, ?, ?)",
                (name, parent, icon),
            )

        for pattern, category, bank, priority in DEFAULT_RULES:
            self.conn.execute(
                "INSERT INTO category_rules (pattern, category_name, bank, priority) "
                "VALUES (?, ?, ?, ?)",
                (pattern, category, bank, priority),
            )

    def close(self):
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

    def add_category(self, name: str, parent: Optional[str] = None, icon: str = ""):
        """Add a new category."""
        self.conn.execute(
            "INSERT INTO categories (name, parent_name, icon) VALUES (?, ?, ?)",
            (name, parent, icon),
        )
        self.conn.commit()

    def remove_category(self, name: str):
        """Remove a category and its associated rules."""
        self.conn.execute("DELETE FROM category_rules WHERE category_name = ?", (name,))
        self.conn.execute("DELETE FROM categories WHERE name = ?", (name,))
        self.conn.commit()

    # ── Rule CRUD ─────────────────────────────────────────────────────────────

    def list_rules(self, bank: Optional[str] = None) -> list[dict]:
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

    def add_rule(self, pattern: str, category: str, bank: str = "*", priority: int = 10):
        """Add a new categorization rule."""
        self.conn.execute(
            "INSERT INTO category_rules (pattern, category_name, bank, priority) "
            "VALUES (?, ?, ?, ?)",
            (pattern, category, bank, priority),
        )
        self.conn.commit()

    def remove_rule(self, rule_id: int):
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
                return row["category_name"]

        return "Uncategorized"

    # ── Stats ─────────────────────────────────────────────────────────────────

    def rule_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM category_rules").fetchone()[0]

    def category_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
