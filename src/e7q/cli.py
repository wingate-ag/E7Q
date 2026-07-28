# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for E7Q."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .language import E7QError, load, openqasm, proof_json, run, verify


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="e7q")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("source")
        command.add_argument("--proof", type=Path)
    export = commands.add_parser("export")
    export.add_argument("source")
    export.add_argument("--format", choices=["openqasm"], default="openqasm")
    export.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        program = load(args.source)
        if args.command == "export":
            content = openqasm(program)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
            else:
                print(content, end="")
            return 0
        result = verify(run(program))
        if args.proof:
            args.proof.write_text(proof_json(result), encoding="utf-8")
        if args.command == "run":
            print(json.dumps(result["counts"], sort_keys=True))
        else:
            for check in result["checks"]:
                print(f"{'PASS' if check['passed'] else 'FAIL'}  {check['name']}")
            print("\nProbabilities:")
            for outcome, probability in sorted(result["probabilities"].items()):
                print(f"{outcome}  {probability:.3f}")
            if args.proof:
                print(f"\nProof-of-Path: {args.proof}")
        return 0 if result["status"] == "PASS" else 1
    except (E7QError, OSError) as exc:
        print(f"e7q: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
