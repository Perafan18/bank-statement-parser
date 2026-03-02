"""Interactive categorization prompts for new transaction descriptions."""

from __future__ import annotations

import click

from bankparser.database import Database
from bankparser.models import Transaction


def prompt_categorize(uncategorized: dict[str, list[Transaction]], db: Database) -> int:
    """Interactively ask the user to categorize each new description.

    Returns the number of rules created.
    """
    if not uncategorized:
        return 0

    categories = db.list_user_categories()
    if not categories:
        click.echo("No user categories available. Add some first.", err=True)
        return 0

    total = len(uncategorized)
    click.echo(f"\n=== {total} conceptos nuevos sin categorizar ===\n", err=True)
    _print_category_grid(categories)

    rules_created = 0
    for i, (desc, txs) in enumerate(uncategorized.items(), 1):
        sample = txs[0]
        count_label = f" ({len(txs)}x)" if len(txs) > 1 else ""
        click.echo(
            f"\n[{i}/{total}] {desc}{count_label}"
            f" -- ${sample.amount:,.2f} ({sample.date.strftime('%d-%b-%Y')})",
            err=True,
        )

        choice = _prompt_choice(len(categories))
        if choice is None:  # quit
            break
        if choice == 0:  # skip
            continue

        category = categories[choice - 1]

        # Ask for pattern — Enter keeps full description, or type a shorter keyword
        click.echo("  Pattern (Enter = full, or type shorter keyword):", err=True)
        raw_pattern = click.prompt(f"  [{desc}]", default="", err=True, show_default=False)
        pattern = raw_pattern.strip() or desc

        db.add_rule(pattern, category, bank="*", priority=10)
        click.echo(f'  -> Rule: "{pattern}" -> {category}', err=True)
        rules_created += 1

    return rules_created


def _print_category_grid(names: list[str]) -> None:
    """Print categories in a numbered 3-column grid."""
    cols = 3
    col_width = 25
    click.echo("  Categories:", err=True)
    for i, name in enumerate(names, 1):
        cell = f"  {i:>2}. {name}"
        if i % cols == 0 or i == len(names):
            click.echo(cell, err=True)
        else:
            click.echo(cell.ljust(col_width), err=True, nl=False)
    click.echo("   0. Skip (Uncategorized)    q. Quit", err=True)


def _prompt_choice(max_num: int) -> int | None:
    """Prompt user for a category number. Returns None for quit, 0 for skip."""
    while True:
        raw = click.prompt("  #", err=True).strip().lower()
        if raw == "q":
            return None
        try:
            num = int(raw)
        except ValueError:
            click.echo(f"  Enter a number (0-{max_num}) or 'q'", err=True)
            continue
        if 0 <= num <= max_num:
            return num
        click.echo(f"  Enter a number (0-{max_num}) or 'q'", err=True)
