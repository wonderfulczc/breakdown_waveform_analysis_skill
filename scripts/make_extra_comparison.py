from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = ["#0057B8", "#ED1C24", "#00A651", "#7B3294", "#F6A800", "#000000"]


def finite(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else np.nan
    except Exception:
        return np.nan


def spectrum(time_s: np.ndarray, voltage: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if len(time_s) < 4:
        return np.array([]), np.array([])
    dt = float(np.nanmedian(np.diff(time_s)))
    y = voltage - np.nanmean(voltage)
    y = y * np.hanning(len(y))
    nfft = max(4096, 1 << (len(y) - 1).bit_length())
    freq = np.fft.rfftfreq(nfft, dt) / 1e6
    amp = np.abs(np.fft.rfft(y, n=nfft))
    if np.nanmax(amp) > 0:
        amp = amp / np.nanmax(amp)
    return freq, amp


def read_waveform(run_dir: Path, file_id: str) -> pd.DataFrame:
    path = run_dir / "normalized_waveform" / "normalized_csv" / f"{file_id}_normalized.csv"
    if not path.exists():
        raise FileNotFoundError(f"Normalized waveform not found: {path}")
    return pd.read_csv(path)


def feature_map(run_dir: Path) -> dict[str, dict]:
    path = run_dir / "single_waveform" / "single_waveform_features.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {str(row["file_id"]): row.to_dict() for _, row in df.iterrows()}


def plot_pair(run_dir: Path, traces: list[tuple[str, pd.DataFrame]], output_name: str, fmap: dict[str, dict]) -> tuple[Path, Path]:
    out = run_dir / "extra_figures"
    out.mkdir(parents=True, exist_ok=True)
    time_path = out / f"{output_name}_time.png"
    freq_path = out / f"{output_name}_freq.png"

    fig, ax = plt.subplots(figsize=(7.1, 4.5))
    param_lines = []
    for idx, (label, df) in enumerate(traces):
        t = df["time_s"].to_numpy(float)
        y = df["voltage_V"].to_numpy(float)
        if len(t) and len(y):
            peak = int(np.nanargmax(np.abs(y)))
            x = (t - t[peak]) * 1e6
            ax.plot(x, y, lw=1.0, color=COLORS[idx % len(COLORS)], label=label)
            row = fmap.get(label, {})
            alpha = finite(row.get("alpha", np.nan))
            if math.isfinite(alpha):
                param_lines.append(f"{label}: alpha={alpha:.3e} s$^{{-1}}$")
    ax.set_xlabel("Aligned time (us)")
    ax.set_ylabel("Voltage (V)")
    ax.legend(loc="upper right", frameon=True, fontsize=7)
    if param_lines:
        ax.text(0.98, 0.72, "\n".join(param_lines[:8]), transform=ax.transAxes, ha="right", va="top", fontsize=7, bbox={"facecolor":"white", "edgecolor":"black", "linewidth":0.5})
    fig.savefig(time_path, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.1, 4.5))
    param_lines = []
    for idx, (label, df) in enumerate(traces):
        freq, amp = spectrum(df["time_s"].to_numpy(float), df["voltage_V"].to_numpy(float))
        ax.plot(freq, amp, lw=1.0, color=COLORS[idx % len(COLORS)], label=label)
        row = fmap.get(label, {})
        f1 = finite(row.get("f1_MHz", np.nan))
        if math.isfinite(f1):
            ax.axvline(f1, color=COLORS[idx % len(COLORS)], lw=0.75, ls="--")
            param_lines.append(f"{label}: f1={f1:.2f} MHz")
    ax.set_xlim(0, 200)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend(loc="upper right", frameon=True, fontsize=7)
    if param_lines:
        ax.text(0.98, 0.72, "\n".join(param_lines[:8]), transform=ax.transAxes, ha="right", va="top", fontsize=7, bbox={"facecolor":"white", "edgecolor":"black", "linewidth":0.5})
    fig.savefig(freq_path, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return time_path, freq_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create extra ML01 comparison figures from a completed run folder.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--mode", choices=["waveform-pair", "template-vs-waveform"], required=True)
    parser.add_argument("--file-id-a", required=True, help="First waveform file_id, or waveform compared with template.")
    parser.add_argument("--file-id-b", default="", help="Second waveform file_id for waveform-pair mode.")
    parser.add_argument("--output-name", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fmap = feature_map(run_dir)
    traces: list[tuple[str, pd.DataFrame]] = []
    if args.mode == "waveform-pair":
        if not args.file_id_b:
            raise SystemExit("--file-id-b is required for waveform-pair mode.")
        traces.append((args.file_id_a, read_waveform(run_dir, args.file_id_a)))
        traces.append((args.file_id_b, read_waveform(run_dir, args.file_id_b)))
        output_name = args.output_name or f"{args.file_id_a}_vs_{args.file_id_b}"
    else:
        template_path = run_dir / "template" / "selected_template_waveform.csv"
        if not template_path.exists() or template_path.stat().st_size <= 30:
            raise SystemExit("Template is missing or empty for this run.")
        template_df = pd.read_csv(template_path)
        traces.append(("T1_template", template_df))
        traces.append((args.file_id_a, read_waveform(run_dir, args.file_id_a)))
        output_name = args.output_name or f"T1_template_vs_{args.file_id_a}"
    time_path, freq_path = plot_pair(run_dir, traces, output_name, fmap)
    print(f"time_figure={time_path}")
    print(f"frequency_figure={freq_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
