from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PIPELINE_DIR = SKILL_DIR / "assets" / "frozen_pipeline"
REQUIRED_ASSET_DIRS = ["02_config", "03_scripts", "05_docs", "codex_prompt"]


def copytree_clean(src: Path, dst: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".git")
    shutil.copytree(src, dst, ignore=ignore)


def latest_run(results_dir: Path, smoke: bool | None = None) -> Path | None:
    runs = [p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith("run_")]
    if smoke is True:
        runs = [p for p in runs if p.name.endswith("_smoke")]
    elif smoke is False:
        runs = [p for p in runs if not p.name.endswith("_smoke")]
    if not runs:
        return None
    return max(runs, key=lambda p: p.stat().st_mtime)


def run_cmd(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def prepare_workspace(input_dir: Path, workspace: Path) -> int:
    for rel in REQUIRED_ASSET_DIRS:
        src = PIPELINE_DIR / rel
        if not src.exists():
            raise FileNotFoundError(f"Missing bundled pipeline asset: {src}")
        copytree_clean(src, workspace / rel)
    (workspace / "01_metadata").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PIPELINE_DIR / "01_metadata" / "group_definition.csv", workspace / "01_metadata" / "group_definition.csv")
    (workspace / "00_raw_csv").mkdir(parents=True, exist_ok=True)
    (workspace / "04_results").mkdir(parents=True, exist_ok=True)

    csv_files = sorted(p for p in input_dir.rglob("*.csv") if p.is_file())
    for src in csv_files:
        rel = src.relative_to(input_dir)
        dst = workspace / "00_raw_csv" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return len(csv_files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen ML01 breakdown waveform analysis on a folder of renamed CSV files.")
    parser.add_argument("input_dir", help="Folder containing renamed ML01 waveform CSV files.")
    parser.add_argument("--keep-workspace", action="store_true", help="Keep the temporary workspace for debugging.")
    parser.add_argument("--output-parent", default="", help="Optional parent directory for the date-prefixed results folder.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input folder does not exist or is not a directory: {input_dir}")

    output_parent = Path(args.output_parent).resolve() if args.output_parent else input_dir.parent
    date_prefix = dt.datetime.now().strftime("%Y%m%d")
    output_root = output_parent / f"{date_prefix}_{input_dir.name}_results"
    output_root.mkdir(parents=True, exist_ok=True)

    work_ctx = tempfile.TemporaryDirectory(prefix="ml01_pipeline_")
    workspace = Path(work_ctx.name)

    try:
        raw_count = prepare_workspace(input_dir, workspace)
        if raw_count == 0:
            raise SystemExit(f"No CSV files found under: {input_dir}")

        run_cmd([sys.executable, "03_scripts/run_all.py", "--smoke"], workspace)
        smoke_run = latest_run(workspace / "04_results", smoke=True)
        if smoke_run and smoke_run.exists():
            shutil.rmtree(smoke_run)

        run_cmd([sys.executable, "03_scripts/run_all.py"], workspace)
        final_run = latest_run(workspace / "04_results", smoke=False)
        if final_run is None:
            raise RuntimeError("Full pipeline completed but no final run folder was found.")

        dst_run = output_root / final_run.name
        if dst_run.exists():
            suffix = 1
            while (output_root / f"{final_run.name}_{suffix:02d}").exists():
                suffix += 1
            dst_run = output_root / f"{final_run.name}_{suffix:02d}"
        shutil.copytree(final_run, dst_run)

        summary = {
            "input_dir": str(input_dir),
            "output_root": str(output_root),
            "run_dir": str(dst_run),
            "raw_csv_files": raw_count,
            "excel_report": str(dst_run / "excel_report" / "waveform_analysis_summary.xlsx"),
            "run_log": str(dst_run / "logs" / "run.log"),
            "template_selection": str(dst_run / "template" / "template_selection.csv"),
        }
        (output_root / "latest_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        if args.keep_workspace:
            print(f"Workspace kept: {workspace}")
        else:
            work_ctx.cleanup()
            pass


if __name__ == "__main__":
    raise SystemExit(main())



