#!/usr/bin/env python3
"""Build a Design Combination Readout from saved combination groups.

Usage:
    python generate_combinations.py saved_combinations.json study_data.json
    python generate_combinations.py saved_combinations.json study_data.json -o readout.pptx
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportgen.combinations import build_combination_readout


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn saved combination groups into the combination readout deck.")
    parser.add_argument("combinations", type=Path, help="Path to saved_combinations.json")
    parser.add_argument("study", type=Path, help="Path to study_data.json")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .pptx path. Defaults beside the combinations file.",
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        default=None,
        help="Optional analysis JSON for the baseline and sample size. Matched by study id when omitted.",
    )
    parser.add_argument("--skip-images", action="store_true", help="Build the deck without downloading artwork.")
    args = parser.parse_args()
    if not args.combinations.exists():
        raise SystemExit(f"File not found: {args.combinations}")
    if not args.study.exists():
        raise SystemExit(f"File not found: {args.study}")
    output = args.output or args.combinations.with_name("Design Combination Readout v2.pptx")
    print(f"Reading {args.combinations}")
    destination = build_combination_readout(
        args.combinations,
        args.study,
        output,
        analysis_path=args.analysis,
        download_images=not args.skip_images,
    )
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
