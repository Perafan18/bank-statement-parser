"""Command-line interface for bankparser.

Usage:
    bankparse parse statement.pdf
    bankparse parse statement.pdf --bank amex --format sure -o output.csv
    bankparse categories list
    bankparse rules add "COSTCO" "Groceries"
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from bankparser import __version__
from bankparser.categorizer import Categorizer
from bankparser.database import Database
from bankparser.exporters import available_formats, get_exporter
from bankparser.interactive import prompt_categorize
from bankparser.models import Transaction, TransactionType
from bankparser.parsers import create_default_registry


def get_db() -> Database:
    db = Database()
    db.initialize()
    return db


@click.group()
@click.version_option(__version__, prog_name="bankparse")
def main() -> None:
    """🏦 Parse Mexican bank statement PDFs into CSV.

    Supports: American Express, BBVA, HSBC Mexico.

    \b
    Quick start:
      bankparse parse statement.pdf
      bankparse parse statement.pdf --format sure -o output.csv
      bankparse parse *.pdf -f sure
    """
    pass


@main.command()
@click.argument("files", nargs=-1, required=True, type=click.Path())
@click.option("--bank", "-b", default=None, help="Force bank type (amex, bbva, hsbc)")
@click.option(
    "--format",
    "-f",
    "fmt",
    default="generic",
    type=click.Choice(available_formats()),
    help="Output CSV format",
)
@click.option("--output", "-o", default=None, help="Output CSV path")
@click.option("--no-fees", is_flag=True, help="Exclude fees, interest, tax")
@click.option("--no-msi", is_flag=True, help="Exclude MSI installments")
@click.option("--charges-only", is_flag=True, help="Only actual charges and credits")
@click.option("--cardholder", default=None, help="Filter by cardholder name")
@click.option("--no-ask", is_flag=True, help="Skip interactive categorization")
def parse(
    files: tuple[str, ...],
    bank: str | None,
    fmt: str,
    output: str | None,
    no_fees: bool,
    no_msi: bool,
    charges_only: bool,
    cardholder: str | None,
    no_ask: bool,
) -> None:
    """Parse one or more PDF statements into CSV.

    \b
    Examples:
      bankparse parse statement.pdf
      bankparse parse statement.pdf --bank amex --format sure
      bankparse parse *.pdf -f sure -o all.csv
      bankparse parse statement.pdf --charges-only
    """
    registry = create_default_registry()
    db = get_db()
    categorizer = Categorizer(db)
    all_transactions: list[Transaction] = []

    try:
        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                click.echo(f"⚠️  File not found: {path}", err=True)
                continue
            if path.suffix.lower() != ".pdf":
                click.echo(f"⚠️  Skipping non-PDF: {path.name}", err=True)
                continue

            click.echo(f"📄 Parsing: {path.name}...", err=True)
            try:
                result = registry.parse(path, bank=bank)
            except Exception as e:
                click.echo(f"❌ {e}", err=True)
                continue

            for w in result.warnings:
                click.echo(f"  ⚠️  {w}", err=True)

            msg = f"  ✅ {result.transaction_count} transactions (bank: {result.info.bank})"
            click.echo(msg, err=True)
            categorizer.categorize_all(result.transactions)
            all_transactions.extend(result.transactions)

        if not all_transactions:
            click.echo("❌ No transactions found!", err=True)
            sys.exit(1)

        # Interactive categorization for new descriptions
        if not no_ask:
            uncategorized = categorizer.collect_uncategorized(all_transactions)
            if uncategorized:
                prompt_categorize(uncategorized, db)
                categorizer.recategorize_uncategorized(all_transactions)
    finally:
        db.close()

    # Filters
    if no_fees:
        exclude = {
            TransactionType.FEE,
            TransactionType.INTEREST,
            TransactionType.TAX,
            TransactionType.MSI_ADJUSTMENT,
        }
        all_transactions = [tx for tx in all_transactions if tx.tx_type not in exclude]
    if no_msi:
        all_transactions = [tx for tx in all_transactions if tx.tx_type != TransactionType.MSI]
    if charges_only:
        keep = {TransactionType.CHARGE, TransactionType.CREDIT}
        all_transactions = [tx for tx in all_transactions if tx.tx_type in keep]
    if cardholder:
        f = cardholder.upper()
        all_transactions = [tx for tx in all_transactions if f in tx.cardholder.upper()]

    all_transactions.sort(key=lambda tx: tx.date)

    # Export
    if output is None:
        output = (Path(files[0]).stem + ".csv") if len(files) == 1 else "transactions.csv"

    exporter = get_exporter(fmt)
    exporter.export(all_transactions, output)

    charges = sum(tx.amount for tx in all_transactions if tx.amount > 0)
    credits = sum(tx.amount for tx in all_transactions if tx.amount < 0)
    click.echo(f"\n📊 Exported {len(all_transactions)} transactions → {output}", err=True)
    click.echo(f"   Format: {fmt}", err=True)
    click.echo(f"   Charges: ${charges:,.2f} MXN", err=True)
    click.echo(f"   Credits: ${credits:,.2f} MXN", err=True)


@main.group()
def categories() -> None:
    """Manage transaction categories."""
    pass


@categories.command("list")
def categories_list() -> None:
    """List all categories."""
    db = get_db()
    cats = db.list_categories()
    db.close()
    click.echo(f"\n{'Icon':<5} {'Category':<25} {'Parent'}")
    click.echo("─" * 50)
    for c in cats:
        click.echo(f"{c['icon'] or ' ':<5} {c['name']:<25} {c['parent_name'] or ''}")
    click.echo(f"\n{len(cats)} categories total")


@categories.command("add")
@click.argument("name")
@click.option("--parent", default=None)
@click.option("--icon", default="")
def categories_add(name: str, parent: str | None, icon: str) -> None:
    """Add a new category."""
    db = get_db()
    try:
        db.add_category(name, parent, icon)
        click.echo(f"✅ Added category: {name}")
    except Exception as e:
        click.echo(f"❌ {e}", err=True)
    db.close()


@categories.command("remove")
@click.argument("name")
@click.confirmation_option(prompt="Remove category and associated rules?")
def categories_remove(name: str) -> None:
    """Remove a category and its rules."""
    db = get_db()
    db.remove_category(name)
    db.close()
    click.echo(f"✅ Removed category: {name}")


@main.group()
def rules() -> None:
    """Manage categorization rules."""
    pass


@rules.command("list")
@click.option("--bank", default=None, help="Filter by bank")
def rules_list(bank: str | None) -> None:
    """List categorization rules."""
    db = get_db()
    rule_list = db.list_rules(bank)
    db.close()
    click.echo(f"\n{'ID':<5} {'Pri':<5} {'Bank':<6} {'Pattern':<30} {'Category'}")
    click.echo("─" * 75)
    for r in rule_list:
        line = (
            f"{r['id']:<5} {r['priority']:<5} {r['bank']:<6}"
            f" {r['pattern']:<30} {r['category_name']}"
        )
        click.echo(line)
    click.echo(f"\n{len(rule_list)} rules total")


@rules.command("add")
@click.argument("pattern")
@click.argument("category")
@click.option("--bank", default="*", help="Bank (* = all)")
@click.option("--priority", default=10, help="Higher = checked first")
def rules_add(pattern: str, category: str, bank: str, priority: int) -> None:
    """Add a categorization rule. Example: bankparse rules add "COSTCO" "Groceries" """
    db = get_db()
    db.add_rule(pattern, category, bank, priority)
    db.close()
    click.echo(f"✅ '{pattern}' → {category} (bank={bank}, priority={priority})")


@rules.command("remove")
@click.argument("rule_id", type=int)
def rules_remove(rule_id: int) -> None:
    """Remove a rule by ID."""
    db = get_db()
    db.remove_rule(rule_id)
    db.close()
    click.echo(f"✅ Removed rule #{rule_id}")


@main.command()
def info() -> None:
    """Show database info and stats."""
    db = get_db()
    click.echo(f"\n📁 Database: {db.db_path}")
    click.echo(f"   Categories: {db.category_count()}")
    click.echo(f"   Rules: {db.rule_count()}")
    db.close()


if __name__ == "__main__":
    main()
