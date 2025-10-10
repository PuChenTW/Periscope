#!/usr/bin/env python3

"""Run backend test coverage and refresh the README badge."""

import json
import re
import subprocess
from pathlib import Path
from typing import Final

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
BACKEND_DIR: Final[Path] = SCRIPT_DIR.parent
REPO_ROOT: Final[Path] = BACKEND_DIR.parent
README_PATH: Final[Path] = BACKEND_DIR / "README.md"
BADGE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(https://img\.shields\.io/badge/test%20coverage-)(\d+)%25-([a-z]+)",
    re.IGNORECASE,
)


def run_command(args: list[str], cwd: Path) -> None:
    """Run a command and raise on failure."""
    subprocess.run(args, cwd=cwd, check=True)


def run_tests_and_generate_report() -> Path:
    """Execute coverage tests and emit a JSON report."""
    run_command(["make", "test-cov"], BACKEND_DIR)
    json_path = BACKEND_DIR / "coverage.json"
    run_command(["uv", "run", "coverage", "json", "-o", str(json_path)], BACKEND_DIR)
    return json_path


def load_total_coverage(json_path: Path) -> int:
    """Extract the total coverage percentage rounded to the nearest integer."""
    with json_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    totals = data.get("totals")
    if not totals or "percent_covered" not in totals:
        raise ValueError("coverage.json missing totals.percent_covered")

    percent = totals["percent_covered"]
    if not isinstance(percent, (int, float)):
        raise TypeError("totals.percent_covered is not numeric")

    return round(percent)


def coverage_color(percent: int) -> str:
    """Pick a shields.io color for the coverage percentage."""
    if percent >= 80:
        return "brightgreen"
    if percent >= 70:
        return "green"
    if percent >= 60:
        return "yellowgreen"
    if percent >= 50:
        return "yellow"
    if percent >= 40:
        return "orange"
    return "red"


def update_readme_badge(percent: int) -> bool:
    """Rewrite the README coverage badge, returning True when modified."""
    if not README_PATH.exists():
        raise FileNotFoundError(f"README not found at {README_PATH}")

    badge_color = coverage_color(percent)
    new_fragment = f"https://img.shields.io/badge/test%20coverage-{percent}%25-{badge_color}"

    original_text = README_PATH.read_text(encoding="utf-8")
    if not BADGE_PATTERN.search(original_text):
        raise ValueError("Coverage badge pattern not found in README.md")

    updated_text = BADGE_PATTERN.sub(new_fragment, original_text, count=1)

    if updated_text == original_text:
        return False

    README_PATH.write_text(updated_text, encoding="utf-8")
    return True


def main() -> int:
    json_path = run_tests_and_generate_report()
    try:
        percent = load_total_coverage(json_path)
    finally:
        json_path.unlink(missing_ok=True)

    changed = update_readme_badge(percent)
    print(f"Coverage total: {percent}%")
    if changed:
        print("Updated backend/README.md coverage badge.")
    else:
        print("Coverage badge already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
