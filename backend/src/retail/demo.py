"""Validate a local layout and export DXF, SVG and validation evidence."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .layout import RetailLayout, export_dxf, validate_layout
from .preview import export_svg


def main(argv: list[str] | None = None) -> int:
    """Return nonzero without exporting when input fails declared checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Layout JSON (UTF-8)")
    parser.add_argument("output", type=Path, help="New or empty output directory")
    args = parser.parse_args(argv)
    try:
        layout = RetailLayout.model_validate_json(
            args.input.read_text(encoding="utf-8")
        )
        issues = validate_layout(layout)
        if issues:
            raise ValueError("; ".join(issues))
        # Build all outputs before creating the directory; no remote client is used.
        outputs = {
            "retail-layout.dxf": export_dxf(layout),
            "retail-layout.svg": export_svg(layout),
            "validation.json": json.dumps(
                {
                    "valid": True,
                    "scope": "declared_geometry_only",
                    "issues": [],
                    "units": "meters",
                    "checks_executed": [
                        "schema",
                        "unique_ids",
                        "zone_references",
                        "bounds",
                        "fixture_overlap",
                        "clear_zone_invasion",
                        "zone_rectangle_width",
                        "declared_zone_connectivity",
                        "height_in_entrance_visibility_zone",
                    ],
                    "pending": [
                        "inventory_fidelity",
                        "physical_accesses",
                        "connection_usable_width",
                        "commercial_route",
                        "queues_and_restocking",
                        "commercial_review",
                        "lighting_calculation",
                        "technical_compliance",
                    ],
                    "commercial_strength": {
                        "value": layout.commercial_strength,
                        "status": "declared_intent",
                    },
                    "lighting_intent": {
                        "value": layout.lighting_intent,
                        "status": "declared_intent",
                    },
                    "data_provenance": "not_verified_by_this_command",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        }
        # Avoid confusing old approved exports with a failed rerun.
        if args.output.exists() and (
            not args.output.is_dir() or any(args.output.iterdir())
        ):
            raise ValueError(
                "Output directory must be new or empty; use another directory"
            )
        args.output.mkdir(parents=True, exist_ok=True)
        try:
            for filename, content in outputs.items():
                (args.output / filename).write_text(content, encoding="utf-8")
        except OSError:
            for filename in outputs:
                (args.output / filename).unlink(missing_ok=True)
            raise
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Exported DXF, SVG and validation.json to {args.output}")
    print("Scope: declared_geometry_only; see validation.json for pending checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
