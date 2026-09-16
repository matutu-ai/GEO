#!/usr/bin/env python3
"""Run the GEO V4 fixed pipeline. Final exports are fail-closed."""

import argparse
import json
import shutil
from pathlib import Path

from core.fixed_pipeline import FixedPipeline, PipelineBlocked
from core.output_renderer import render_final, write_json


ROOT = Path(__file__).resolve().parent


def load_input(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineBlocked(f"INPUT-005: cannot read input JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineBlocked("INPUT-006: input JSON must be an object")
    return data


def prepare_output(path):
    resolved = path.resolve()
    if resolved in {ROOT, ROOT.parent}:
        raise PipelineBlocked("OUTPUT-001: output directory must not be the repository or its parent")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def main():
    parser = argparse.ArgumentParser(description="Run the non-overridable GEO V4 fixed pipeline.")
    parser.add_argument("--input", type=Path, default=ROOT / "input" / "company.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument("--mode", choices=("interactive", "fast_path"), default="interactive")
    args = parser.parse_args()

    try:
        data = load_input(args.input)
        prepare_output(args.output)
        pipeline = FixedPipeline(mode=args.mode)
        if args.mode == "interactive":
            state = pipeline.interactive_state(data)
            artifact = pipeline.store.get("fact_packet")
            write_json(args.output / "fact_packet.json", artifact["payload"])
            write_json(args.output / "interactive_state.json", state)
            write_json(args.output / "execution_trace.json", pipeline.trace)
            print("PAUSED: Interactive Mode created Fact_Packet and is awaiting required materials")
            return
        artifacts, trace = pipeline.run(data)
        render_final(args.output, artifacts, trace)
        print(f"PASS: generated validated GEO V4 assets for {data['company_name']}")
        for path in sorted(args.output.iterdir()):
            print(path.name)
    except PipelineBlocked as exc:
        print(f"BLOCKED: {exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
