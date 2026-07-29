# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for E7Q."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .adapters import adapt, adapter_result
from .assessment import assess_receipt, load_reference, load_receipt
from .artifacts import load_artifact, validate_artifact
from .bundles import build_execution_bundle
from .campaigns import assess_replication, load_replication_receipts
from .drift import assess_drift, load_replication_report
from .trends import assess_trend, load_trend_reports
from .calibration import load_snapshot, select_target
from .ingestion import load_vendor_export
from .language import (
    E7QError, backend_profile, compare, comparison_result, compilation_result,
    compile_topology, load, openqasm, proof_json, run, topology_edges, verify,
)
from .planning import plan, plan_result
from .results import build_execution_receipt, load_execution_bundle, load_execution_result


def _native_gates(value: str) -> frozenset[str]:
    return frozenset(item.strip().upper() for item in value.split(",") if item.strip())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="e7q")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("source")
        command.add_argument("--proof", type=Path)
    export = commands.add_parser("export")
    export.add_argument("source")
    export.add_argument(
        "--format", choices=["openqasm", "qiskit", "cirq"], default="openqasm"
    )
    export.add_argument("--proof", type=Path)
    export.add_argument("-o", "--output", type=Path)
    compare_command = commands.add_parser("compare")
    compare_command.add_argument("first")
    compare_command.add_argument("second")
    compare_command.add_argument(
        "--criterion",
        choices=[
            "exact", "global-phase", "measurement", "tolerance",
            "channel-exact", "channel-tolerance", "channel-measurement",
        ],
        default="global-phase",
    )
    compare_command.add_argument("--tolerance", type=float, default=1e-12)
    compare_command.add_argument("--proof", type=Path)
    capabilities = commands.add_parser("capabilities")
    capabilities.add_argument("source")
    ingest = commands.add_parser("ingest-calibration")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--provider", choices=["ibm", "google"], required=True)
    ingest.add_argument("--max-age-hours", type=float)
    ingest.add_argument("-o", "--output", required=True, type=Path)
    bundle = commands.add_parser("bundle")
    bundle.add_argument("source", type=Path)
    bundle.add_argument("--snapshot", required=True, type=Path)
    bundle.add_argument("--shots", type=int, default=1000)
    bundle.add_argument("-o", "--output", required=True, type=Path)
    receipt = commands.add_parser("receipt")
    receipt.add_argument("bundle", type=Path)
    receipt.add_argument("--result", required=True, type=Path)
    receipt.add_argument("-o", "--output", required=True, type=Path)
    assess = commands.add_parser("assess")
    assess.add_argument("receipt", type=Path)
    assess.add_argument("--reference", required=True, type=Path)
    assess.add_argument("-o", "--output", required=True, type=Path)
    replicate = commands.add_parser("replicate")
    replicate.add_argument("receipts", nargs="+", type=Path)
    replicate.add_argument("--max-pairwise-tvd", type=float, default=0.1)
    replicate.add_argument("--significance-level", type=float, default=0.05)
    replicate.add_argument("-o", "--output", required=True, type=Path)
    drift = commands.add_parser("drift")
    drift.add_argument("baseline", type=Path)
    drift.add_argument("candidate", type=Path)
    drift.add_argument("--max-total-variation", type=float, default=0.1)
    drift.add_argument("--significance-level", type=float, default=0.05)
    drift.add_argument("-o", "--output", required=True, type=Path)
    trend = commands.add_parser("trend")
    trend.add_argument("campaigns", nargs="+", type=Path)
    trend.add_argument("--max-total-variation", type=float, default=0.1)
    trend.add_argument("--significance-level", type=float, default=0.05)
    trend.add_argument("-o", "--output", required=True, type=Path)
    artifact = commands.add_parser("validate-artifact")
    artifact.add_argument("source", type=Path)
    artifact.add_argument("-o", "--output", type=Path)
    select = commands.add_parser("select")
    select.add_argument("source")
    select.add_argument("--snapshot", required=True, type=Path)
    select.add_argument("--proof", type=Path)
    for name in ("compile", "plan"):
        command = commands.add_parser(name)
        command.add_argument("source")
        command.add_argument(
            "--topology",
            choices=["linear", "ring", "all-to-all"],
            default="linear",
        )
        command.add_argument(
            "--native-gates",
            default="X,Y,Z,H,S,T,CX,CZ,SWAP",
            help="comma-separated native gate set",
        )
        command.add_argument("--proof", type=Path)
        if name == "compile":
            command.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "ingest-calibration":
            result = load_vendor_export(
                args.source, args.provider, max_age_hours=args.max_age_hours
            )
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Calibration snapshot: {args.output}")
            return 0
        if args.command == "bundle":
            source = args.source.read_bytes()
            result = build_execution_bundle(
                load(args.source), source, load_snapshot(args.snapshot), shots=args.shots
            )
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution bundle: {args.output}")
            return 0
        if args.command == "receipt":
            bundle_value, bundle_bytes = load_execution_bundle(args.bundle)
            result_value, result_bytes = load_execution_result(args.result)
            receipt = build_execution_receipt(
                bundle_value, bundle_bytes, result_value, result_bytes
            )
            args.output.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution receipt: {args.output}")
            return 0
        if args.command == "assess":
            assessment = assess_receipt(
                load_receipt(args.receipt), load_reference(args.reference)
            )
            args.output.write_text(
                json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution assessment: {args.output}")
            return 0 if assessment["status"] == "PASS" else 1
        if args.command == "replicate":
            report = assess_replication(
                load_replication_receipts(args.receipts),
                max_pairwise_tvd=args.max_pairwise_tvd,
                significance_level=args.significance_level,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Replication report: {args.output}")
            return 0 if report["status"] == "PASS" else 1
        if args.command == "drift":
            report = assess_drift(
                load_replication_report(args.baseline),
                load_replication_report(args.candidate),
                max_total_variation=args.max_total_variation,
                significance_level=args.significance_level,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Drift report: {args.output}")
            return 0 if report["status"] == "NO_DRIFT" else 1
        if args.command == "trend":
            report = assess_trend(
                load_trend_reports(args.campaigns),
                max_total_variation=args.max_total_variation,
                significance_level=args.significance_level,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Trend report: {args.output}")
            return 0 if report["status"] == "NO_TREND_DETECTED" else 1
        if args.command == "validate-artifact":
            report = validate_artifact(load_artifact(args.source))
            content = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                print(f"Conformance report: {args.output}")
            else:
                print(content, end="")
            return 0 if report["status"] == "PASS" else 1
        if args.command == "compare":
            comparison = compare(
                load(args.first), load(args.second), args.criterion, args.tolerance
            )
            result = comparison_result(comparison)
            print(
                f"{result['status']}  equivalent under "
                f"{result['criterion']} criterion"
            )
            print(f"Maximum error: {result['maximum_error']:.3e}")
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}")
            return 0 if comparison.equivalent else 1
        program = load(args.source)
        if args.command == "select":
            result = select_target(program, load_snapshot(args.snapshot))
            print(json.dumps({
                "status": result["status"],
                "selected": result["selected"],
                "score": result["score"],
                "captured_at": result["captured_at"],
            }, indent=2, sort_keys=True))
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "plan":
            result = plan_result(
                plan(program, args.topology, _native_gates(args.native_gates))
            )
            print(json.dumps({
                "status": result["status"],
                "source": result["source"],
                "compiled": result["compiled"],
                "overhead": result["overhead"],
            }, indent=2, sort_keys=True))
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "compile":
            compilation = compile_topology(
                program,
                topology_edges(program.qubits, args.topology),
                _native_gates(args.native_gates),
            )
            content = openqasm(compilation.program)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
            else:
                print(content, end="")
            if args.proof:
                args.proof.write_text(
                    proof_json(compilation_result(compilation)), encoding="utf-8"
                )
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "capabilities":
            print(json.dumps(backend_profile(program), indent=2, sort_keys=True))
            return 0
        if args.command == "export":
            if args.format == "openqasm":
                content = openqasm(program)
                result = None
            else:
                output = adapt(program, args.format)
                content = output.source
                result = adapter_result(output)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
            else:
                print(content, end="")
            if args.proof:
                if result is None:
                    raise E7QError("adapter proof requires qiskit or cirq format")
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
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
