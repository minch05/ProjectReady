import argparse
import json
from pathlib import Path

from . import __version__
from .checks import check_project, exit_code, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="projectready", description="Read-only Python project readiness checks")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Inspect a Python project without modifying it")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=("terminal", "json"), default="terminal")
    check.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)
    checks = check_project(args.path)
    if args.json or args.format == "json":
        print(json.dumps(report(checks), ensure_ascii=True, indent=2))
    else:
        for result in checks:
            print(f"{result.status:4} {result.name}: {result.message}")
        print(f"Exit code: {exit_code(checks)}")
    return exit_code(checks)
