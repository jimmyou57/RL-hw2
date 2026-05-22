"""Submission entrypoint for Task A hover evaluation."""

from __future__ import annotations

import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from part2.evaluate import main as evaluate_main


def main() -> None:
    evaluate_main()


if __name__ == "__main__":
    main()
