#!/usr/bin/env python3
"""Build a Design Element Appeal PowerPoint from an analysis JSON export.

Usage:
    python generate_report.py analysis_data.json
    python generate_report.py analysis_data.json -o report.pptx
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportgen.build import build_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn an analysis JSON file into the appeal report deck.")
    parser.add_argument("json_path", type=Path, help="Path to analysis_data.json")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .pptx path. Defaults to <json name> — Appeal Report.pptx beside the JSON.",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Build the deck without downloading element artwork.",
    )
    parser.add_argument(
        "--study-type",
        choices=("layer", "grid", "text", "hybrid"),
        default=None,
        help="Override the study type stored in the analysis. Hybrid uses the layer layout.",
    )
    parser.add_argument(
        "--logo",
        type=Path,
        default=None,
        help="Brand logo placed on the cover instead of the Rexona and MGA marks.",
    )
    args = parser.parse_args()
    if not args.json_path.exists():
        raise SystemExit(f"File not found: {args.json_path}")
    output = args.output
    if output is None:
        output = args.json_path.with_name(f"{args.json_path.stem} — Appeal Report.pptx")
    print(f"Reading {args.json_path}")
    destination = build_report(
        args.json_path,
        output,
        download_images=not args.skip_images,
        logo_path=args.logo,
        study_type=args.study_type,
    )
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
