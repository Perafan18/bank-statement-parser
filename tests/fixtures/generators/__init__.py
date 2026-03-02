"""PDF fixture generators. Run with: python -m tests.fixtures.generators"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

GENERATORS_DIR = Path(__file__).parent
PDFS_DIR = GENERATORS_DIR.parent / "pdfs"


def main() -> None:
    PDFS_DIR.mkdir(exist_ok=True)
    for script in sorted(GENERATORS_DIR.glob("generate_*.py")):
        print(f"Running {script.name}...")
        subprocess.run([sys.executable, str(script)], check=True)
    print("All PDFs generated.")


if __name__ == "__main__":
    main()
