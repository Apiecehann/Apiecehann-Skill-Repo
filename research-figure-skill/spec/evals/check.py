"""Check deterministic IR decisions against requests; no model calls are made."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compile import ROOT, compile_ir, distribution_rows, load_ir, load_recipes, read_rows


def read_cases(path):
    cases, seen = [], set()
    with Path(path).open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            case = json.loads(line)
            required = {"id", "request", "data", "recipe", "expect"}
            if not isinstance(case, dict) or set(case) != required:
                raise ValueError(f"Case line {line_number}: requires {sorted(required)}")
            if not isinstance(case["id"], str) or not case["id"] or case["id"] in seen:
                raise ValueError(f"Invalid or duplicate case id at line {line_number}")
            if not isinstance(case["expect"], dict) or not case["expect"]:
                raise ValueError(f"{case['id']}: expect must be a nonempty object")
            seen.add(case["id"])
            cases.append(case)
    if not cases:
        raise ValueError("No evaluation cases")
    return cases


def projection(ir):
    # Semantic defaults are included so omission and an explicit default agree.
    result = dict(ir)
    result["size"] = ir["size"]["preset"]
    result["layout"] = ir.get("layout", "grouped")
    result["emphasis"] = [c["card"] for c in ir.get("emphasis", [])]
    result["annotations"] = [c["card"] for c in ir.get("annotations", [])]
    result["encoding_cards"] = (["distribution"] if ir["chart"] == "distribution-overlap"
                                else [name for name, key in
                                      (("increment", "base"), ("capacity", "capacity"))
                                      if key in ir["encoding"]])
    result["theme"] = {"hatch": False, "type_scale": 1, **ir["theme"]}
    return result


def differences(actual, expected, path="IR"):
    errors = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {actual!r}"]
        for key, value in expected.items():
            if key not in actual:
                errors.append(f"{path}.{key}: missing expected field")
            else:
                errors.extend(differences(actual[key], value, f"{path}.{key}"))
    elif actual != expected:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")
    return errors


def check_case(case, ir_path):
    ir_path = Path(ir_path)
    ir = load_ir(ir_path)
    errors = differences(projection(ir), case["expect"])
    expected_data = (ROOT / case["data"]).resolve()
    if not expected_data.is_file():
        raise ValueError(f"{case['id']}: missing case data {case['data']}")
    # Compare parsed records, not machine-dependent paths or newline encodings.
    expected_ir = {**ir, "data": str(expected_data)}
    if ir["chart"] == "distribution-overlap":
        actual_rows = distribution_rows(ir, ir_path)
        expected_rows = distribution_rows(expected_ir, ir_path)
    else:
        actual_rows, _ = read_rows(ir, ir_path)
        expected_rows, _ = read_rows(expected_ir, ir_path)
    if actual_rows != expected_rows:
        errors.append("IR.data: rows do not match the case data")
    with tempfile.TemporaryDirectory(prefix="figure-eval-") as temp:
        compile_ir(ir_path, temp)
    if errors:
        raise ValueError(f"{case['id']}: " + "; ".join(errors))
    return case["id"]


def check_templates(cases):
    registry = {r["id"]: r for r in load_recipes()}
    checked = []
    for case in cases:
        if case["recipe"] not in registry:
            raise ValueError(f"{case['id']}: unknown recipe {case['recipe']!r}")
        checked.append(check_case(case, ROOT / registry[case["recipe"]]["ir"]))
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ir", type=Path)
    mode.add_argument("--check-templates", action="store_true")
    parser.add_argument("--case", help="Case id for --ir; optional when the case file has one row")
    args = parser.parse_args()
    try:
        cases = read_cases(args.cases)
        if args.check_templates:
            if args.case:
                raise ValueError("--case is only valid with --ir")
            checked = check_templates(cases)
        else:
            if args.case:
                selected = [c for c in cases if c["id"] == args.case]
                if len(selected) != 1:
                    raise ValueError(f"Unknown case {args.case!r}")
            elif len(cases) == 1:
                selected = cases
            else:
                ir = load_ir(args.ir)
                def records(path):
                    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
                        return list(csv.DictReader(stream))
                source = records(args.ir.parent / ir["data"])
                selected = [c for c in cases if records(ROOT / c["data"]) == source]
                if not selected:
                    raise ValueError("No case matches IR.data; use --case <id> to select explicitly")
            checked = [check_case(case, args.ir) for case in selected]
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"PASS {len(checked)} case(s): " + ", ".join(checked))


if __name__ == "__main__":
    main()
