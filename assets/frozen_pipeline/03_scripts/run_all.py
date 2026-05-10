from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import math
import re
import shutil
import sys
import textwrap
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnchoredOffsetbox, DrawingArea, HPacker, TextArea, VPacker
from matplotlib.patches import Rectangle
from matplotlib.text import Text
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, hilbert


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "00_raw_csv"
METADATA_DIR = PROJECT_ROOT / "01_metadata"
CONFIG_DIR = PROJECT_ROOT / "02_config"
RESULTS_DIR = PROJECT_ROOT / "04_results"
SCRIPTS_DIR = PROJECT_ROOT / "03_scripts"

REQUIRED_SCRIPTS = [
    "run_all.py",
    "detect_waveform_format.py",
    "load_waveform.py",
    "normalize_waveform.py",
    "read_waveform.py",
    "preprocess.py",
    "extract_features.py",
    "classify_waveform.py",
    "plot_waveform.py",
    "summarize_group.py",
    "export_report.py",
]

FIGURE_LEGEND_FONT_SIZE = 6.4
FIGURE_LEGEND_FRAME_WIDTH = 0.65
FIGURE_LEGEND_FRAME_ALPHA = 0.92
FIGURE_LEGEND_FRAME_EDGE = "black"
FIGURE_LEGEND_FRAME_FACE = "white"
SAMPLE_LEGEND_ANCHOR = (0.985, 0.985)
LEGEND_PARAMETER_GAP_PT = 1.0
COLOR_LEGEND_BOX_WIDTH_PT = 82.0
COLOR_LEGEND_LINE_WIDTH_PT = COLOR_LEGEND_BOX_WIDTH_PT * 0.5
GROUP_WAVEFORM_COLORS = [
    "#fbe6a0",
    "#f9d68e",
    "#f4b751",
    "#f19f3d",
    "#e56d3d",
    "#d72c3c",
    "#c71a5b",
    "#a82c8c",
    "#7b4b9e",
    "#4d4e9f",
]
COMPARISON_TRACE_COLORS = [
    "#0057B8",
    "#ED1C24",
    "#00A651",
    "#7B3294",
    "#F6A800",
    "#000000",
]
INSET_YTICK_FONT_SIZE = FIGURE_LEGEND_FONT_SIZE - 1.0
INSET_XTICK_FONT_SIZE = FIGURE_LEGEND_FONT_SIZE - 0.6
PARAMETER_BOX_ANCHOR = (SAMPLE_LEGEND_ANCHOR[0], 0.89)
DEFAULT_TIME_DISPLAY_START_US = 0.16
REFERENCE_SOURCE_GROUP = "G3_D0p3m_L1Mohm_Gcoax"

SAMPLE_INDEX_FIELDS = "file_name,file_path,date,experiment_id,group_id,config_group,distance_m,load_condition,ground_condition,block_id,sample_index,included,manual_note".split(",")
FORMAT_FIELDS = "run_id,file_id,file_name,file_path,file_extension,detected_format,loader_used,parse_status,time_column_mode,voltage_column_mode,start_time_s,time_increment_s,sampling_rate_Hz,record_length,error_message,suggested_action".split(",")
FEATURE_FIELDS = "run_id,file_id,file_name,file_path,normalized_file_path,detected_format,loader_used,experiment_id,date,input_data_domain,processing_direction,fft_performed,ifft_performed,time_domain_available,frequency_domain_available,time_domain_reconstructed,domain_detection_status,normalized_workbook_path,fdom_MHz,Adom,independent_peak_count,shoulder_peak_flag,DPR_dB,group_id,config_group,distance_m,load_condition,ground_condition,block_id,sample_index,time_unit,voltage_unit,start_time_s,time_increment_s,sampling_rate_Hz,record_length,baseline_V,nan_fraction,Apk,Amin,App,t_Apk_s,f1_MHz,A1,f2_MHz,A2,PSR_dB,narrowband_SNR_dB,alpha,rho,fit_R2,burst_start_s,burst_end_s,num_bursts,single_burst,envelope_monotonic,front_glitch_flag,tail_disturbance_flag,reignition_flag,multiburst_flag,overdamped_flag,nonoscillatory_flag,clipped,saturated,aliasing_flag,overdrive_recovery_flag,echo_flag,delayed_echo_detected,multi_peak_flag,beating_flag,period_drift_flag,f2_relation,fsrc_MHz,alpha_src,A_fsrc,f1_to_fsrc_diff_percent,fsrc_trackable,measurement_chain_sensitive,ground_sensitive,loading_sensitive,waveform_class,quality_label,pass_flag,reject_reason,main_warning_flag,classification_rule_version,figure_time_path,figure_freq_path,figure_fit_path,analysis_status,notes".split(",")
LABEL_FIELDS = "run_id,file_id,file_name,group_id,config_group,distance_m,load_condition,ground_condition,block_id,sample_index,waveform_class,quality_label,pass_flag,reject_reason,main_warning_flag,classification_rule_version,analysis_status,notes".split(",")
GROUP_STAT_FIELDS = "run_id,group_id,config_group,distance_m,load_condition,ground_condition,N_total,N_analyzed,N_excluded,f1_median_MHz,f1_IQR_MHz,f1_CV_percent,alpha_median,alpha_IQR,alpha_CV_percent,Apk_median,Apk_IQR,Apk_CV_percent,PSR_median_dB,PSR_IQR_dB,SNR_median_dB,SNR_IQR_dB,rho_median,rho_IQR,fit_R2_median,dominant_waveform_class,excellent_ratio_percent,usable_ratio_percent,suspicious_ratio_percent,unusable_ratio_percent,pass_ratio_percent,group_decision,overlay_time_figure_path,overlay_freq_figure_path,statistics_figure_path,notes".split(",")
GROUP_QUALITY_FIELDS = "run_id,group_id,N_total,N_excellent,N_usable,N_suspicious,N_unusable,excellent_ratio_percent,usable_ratio_percent,suspicious_ratio_percent,unusable_ratio_percent,A_count,B_count,C_count,D_count,E_count,F_count,G_count,H_count,main_failure_reason,recommendation".split(",")
ERROR_FIELDS = "run_id,file_name,file_path,error_type,error_message,processing_step,suggested_action,time_stamp".split(",")
EXCLUDED_FIELDS = "run_id,file_name,file_path,exclude_reason,excluded_by,exclude_time,original_quality_label,manual_note".split(",")
WRITE_AUDIT_FIELDS = "run_id,path,file_type,operation,allowed_by_rule,status,notes".split(",")
SCRIPT_AUDIT_FIELDS = "run_id,script_name,script_path,exists,reused,modified,modification_reason,backup_path,status".split(",")
TEMPLATE_SELECTION_FIELDS = "run_id,template_mode,manual_template_used,reference_group,fallback_level,template_confidence,template_method,candidate_N,selected_template_file_id,selected_template_file_name,selected_template_file_path,selected_template_normalized_path,fsrc_MHz,alpha_src,template_time_figure_path,template_frequency_figure_path,fallback_used,fallback_reason,warning_flag,status,notes".split(",")
TEMPLATE_CANDIDATE_FIELDS = "run_id,file_id,file_name,group_id,config_group,distance_m,load_condition,ground_condition,block_id,sample_index,candidate_pool,candidate_pass,ranking_score,PSR_dB,narrowband_SNR_dB,fit_R2,single_burst,envelope_monotonic,clipped,saturated,aliasing_flag,reignition_flag,multiburst_flag,selected_as_template,reject_reason,notes".split(",")
DISTANCE_S001_COMPARISON_FIELDS = "run_id,comparison_id,date,config_group,load_condition,ground_condition,N_distances,trace_labels,selected_file_ids,time_figure_path,frequency_figure_path,status,notes".split(",")
CONFIG_MIN_DISTANCE_COMPARISON_FIELDS = "run_id,comparison_id,date,load_condition,ground_condition,N_configs,trace_labels,selected_file_ids,time_figure_path,frequency_figure_path,status,notes".split(",")
CONFIG_SAME_DISTANCE_COMPARISON_FIELDS = "run_id,comparison_id,date,distance_m,N_configs,trace_labels,selected_file_ids,time_figure_path,frequency_figure_path,status,notes".split(",")

FILENAME_RE = re.compile(
    r"^(?P<date>\d{8})_(?P<experiment_id>ML01)_(?P<config_group>G[1-4])_"
    r"(?P<distance_token>D\d+p\d+m)_(?P<load_token>L(?:1Mohm|50ohm|100ohm|1kohm|open))_"
    r"(?P<ground_token>G(?:long|short|spring|coax|loop|none))_"
    r"(?P<block_id>B\d{2})_(?P<sample_index>S\d{3})\.csv$"
)


@dataclass
class Waveform:
    time_s: np.ndarray
    voltage_V: np.ndarray
    metadata: dict[str, Any]


def now_text() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def finite_or_nan(value: Any) -> float:
    try:
        value = float(value)
        return value if np.isfinite(value) else np.nan
    except Exception:
        return np.nan


def normalized_spectrum_amp(freq_mhz: np.ndarray, amp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    freq = np.asarray(freq_mhz, dtype=float)
    val = np.asarray(amp, dtype=float)
    keep = np.isfinite(freq) & np.isfinite(val)
    freq, val = freq[keep], np.abs(val[keep])
    if len(freq) == 0:
        return np.array([]), np.array([])
    order = np.argsort(freq)
    freq, val = freq[order], val[order]
    if np.nanmax(val) > 0:
        val = val / np.nanmax(val)
    return freq, val


def metadata_for_tables(metadata: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metadata.items() if not k.startswith("_") and not isinstance(v, np.ndarray)}


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def flatten_dict(dct: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    rows = []
    for key, value in dct.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            rows.extend(flatten_dict(value, name))
        else:
            rows.append((name, value))
    return rows


def create_run_dir(smoke: bool = False) -> tuple[str, Path]:
    run_id = dt.datetime.now().strftime("run_%Y%m%d_%H%M")
    if smoke:
        run_id = f"{run_id}_smoke"
    candidate = RESULTS_DIR / run_id
    counter = 1
    while candidate.exists():
        candidate = RESULTS_DIR / f"{run_id}_{counter:02d}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate.name, candidate


def ensure_run_dirs(run_dir: Path) -> None:
    for item in [
        "normalized_waveform/normalized_csv",
        "single_waveform/figures_time_domain",
        "single_waveform/figures_frequency_domain",
        "single_waveform/figures_fit",
        "group_summary/overlay_time_domain",
        "group_summary/overlay_frequency_domain",
        "group_summary/statistics_figures",
        "group_summary/distance_S001_comparison",
        "group_summary/config_min_distance_S001_comparison",
        "group_summary/config_same_distance_S001_comparison",
        "config_snapshot",
        "excel_report",
        "logs/script_backup",
        "template",
        "report",
    ]:
        (run_dir / item).mkdir(parents=True, exist_ok=True)


def audit_row(run_id: str, path: Path, operation: str, allowed: bool, status: str, notes: str = "") -> dict[str, Any]:
    return {
        "run_id": run_id,
        "path": relpath(path),
        "file_type": path.suffix.lower(),
        "operation": operation,
        "allowed_by_rule": int(bool(allowed)),
        "status": status,
        "notes": notes,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str], audit: list[dict[str, Any]], run_id: str, notes: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for field in fields:
        if field not in df.columns:
            df[field] = np.nan
    extra = [c for c in df.columns if c not in fields]
    df = df[fields + extra]
    existed = path.exists()
    df.to_csv(path, index=False, encoding="utf-8-sig")
    if audit is not None:
        audit.append(audit_row(run_id, path, "update" if existed else "create", True, "ok", notes))


def read_table_flexible(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    sig = path.read_bytes()[:8]
    if sig.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return pd.read_excel(path, engine="xlrd")
    if sig.startswith(b"PK\x03\x04"):
        return pd.read_excel(path, engine="openpyxl")
    for enc in ["utf-8-sig", "utf-8", "gbk", "latin1"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_excel(path)


def parse_filename(path: Path) -> dict[str, Any]:
    match = FILENAME_RE.match(path.name)
    if not match:
        raise ValueError("filename_parse_failed")
    data = match.groupdict()
    distance_token = data["distance_token"]
    load_token = data["load_token"]
    ground_token = data["ground_token"]
    distance_m = float(distance_token[1:-1].replace("p", "."))
    load_map = {
        "L1Mohm": ("1Mohm", 1000000.0),
        "L50ohm": ("50ohm", 50.0),
        "L100ohm": ("100ohm", 100.0),
        "L1kohm": ("1kohm", 1000.0),
        "Lopen": ("open", np.nan),
    }
    load_condition, load_ohm = load_map[load_token]
    ground_condition = ground_token[1:]
    group_id = f"{data['config_group']}_{distance_token}_{load_token}_{ground_token}"
    file_id = f"{group_id}_{data['block_id']}_{data['sample_index']}"
    return {
        "date": data["date"],
        "experiment_id": data["experiment_id"],
        "config_group": data["config_group"],
        "distance_token": distance_token,
        "distance_m": distance_m,
        "load_token": load_token,
        "load_condition": load_condition,
        "load_ohm": load_ohm,
        "ground_token": ground_token,
        "ground_condition": ground_condition,
        "block_id": data["block_id"],
        "sample_index": data["sample_index"],
        "group_id": group_id,
        "file_id": file_id,
    }


def folder_conflict(path: Path, meta: dict[str, Any]) -> bool:
    match = re.match(r"^(G[1-4])_(D\d+p\d+)$", path.parent.name)
    if not match:
        return False
    folder_group, folder_distance = match.groups()
    return folder_group != meta["config_group"] or not meta["distance_token"].startswith(folder_distance)


def scan_raw_files(max_files: int | None = None) -> list[Path]:
    files = sorted([
        p
        for p in RAW_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in [".csv", ".xlsx", ".xls"]
    ])
    return files[:max_files] if max_files else files


def detect_waveform_format(path: Path) -> dict[str, Any]:
    result = {"file_extension": path.suffix.lower(), "detected_format": "unknown_binary", "loader_used": "", "error_message": "", "suggested_action": ""}
    sig = path.read_bytes()[:8]
    if sig.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        result["detected_format"] = "mislabeled_excel_binary_with_csv_extension" if path.suffix.lower() == ".csv" else "excel_xls_or_ole_binary"
        result["loader_used"] = "try_read_excel_with_available_engine"
        return result
    if sig.startswith(b"PK\x03\x04"):
        result["detected_format"] = "excel_xlsx"
        result["loader_used"] = "pandas_read_excel"
        return result
    try:
        lines = []
        with path.open("r", encoding="utf-8-sig", errors="replace") as f:
            for _ in range(30):
                line = f.readline()
                if not line:
                    break
                lines.append(line.strip())
        lower = [ln.lower() for ln in lines]
        if len(lines) >= 2 and "sequence" in lower[1] and "volt" in lower[1] and "start" in lower[0] and "increment" in lower[0]:
            result["detected_format"] = "oscilloscope_sequence_volt_csv"
            result["loader_used"] = "parse_sequence_volt_start_increment"
        elif any(ln.startswith("fft length") for ln in lower) and any(ln.startswith("frequency,") and "real part" in ln and "imaginary part" in ln for ln in lower):
            result["detected_format"] = "fft_spectrum_csv"
            result["loader_used"] = "parse_fft_complex_spectrum_and_irfft"
        elif any(ln.startswith("frequency,") and "magnitude" in ln for ln in lower):
            result["detected_format"] = "frequency_magnitude_csv"
            result["loader_used"] = "parse_frequency_magnitude_direct"
        elif any("," in ln for ln in lines[:5]) and any(token in ",".join(lower[:5]) for token in ["time", "volt", "ch1", "sequence"]):
            result["detected_format"] = "true_text_csv"
            result["loader_used"] = "pandas_read_csv_auto"
        elif any(re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", ln) for ln in lines):
            result["detected_format"] = "csv_with_preamble"
            result["loader_used"] = "auto_detect_numeric_table_start"
        else:
            result["suggested_action"] = "Check whether file is a supported text CSV or Excel waveform export."
    except Exception as exc:
        result["error_message"] = str(exc)
        result["suggested_action"] = "Check file encoding or binary format."
    return result


def load_waveform(path: Path, detection: dict[str, Any], config: dict[str, Any]) -> Waveform:
    fmt = detection["detected_format"]
    if fmt == "oscilloscope_sequence_volt_csv":
        df = pd.read_csv(path, header=None, engine="python")
        start_s = finite_or_nan(df.iloc[1, 2]) if df.shape[1] > 2 else np.nan
        dt_s = finite_or_nan(df.iloc[1, 3]) if df.shape[1] > 3 else np.nan
        sequence = pd.to_numeric(df.iloc[2:, 0], errors="coerce").to_numpy(dtype=float)
        voltage = pd.to_numeric(df.iloc[2:, 1], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("invalid_time_increment")
        return clean_waveform(start_s + sequence * dt_s, voltage, "reconstructed_from_sequence", "Volt_column", start_s, dt_s)
    if fmt == "fft_spectrum_csv":
        return load_fft_spectrum_csv(path)
    if fmt == "frequency_magnitude_csv":
        return load_frequency_magnitude_csv(path)
    if fmt in {"excel_xlsx", "excel_xls_or_ole_binary", "mislabeled_excel_binary_with_csv_extension"}:
        engine = "xlrd" if fmt in {"excel_xls_or_ole_binary", "mislabeled_excel_binary_with_csv_extension"} else "openpyxl"
        return load_from_dataframe(pd.read_excel(path, header=None, engine=engine), config)
    if fmt in {"true_text_csv", "csv_with_preamble"}:
        if fmt == "true_text_csv":
            try:
                return load_from_dataframe(pd.read_csv(path, engine="python"), config)
            except Exception:
                return load_from_dataframe(pd.read_csv(path, header=None, engine="python"), config)
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        start = 0
        for i, line in enumerate(lines):
            parts = [p.strip() for p in re.split(r"[,;\t]", line)]
            numeric = sum(1 for p in parts if p and pd.notna(pd.to_numeric(p, errors="coerce")))
            if numeric >= 2:
                start = i
                break
        return load_from_dataframe(pd.read_csv(path, header=None, skiprows=start, engine="python"), config)
    raise ValueError(f"unsupported waveform format: {fmt}")


def load_fft_spectrum_csv(path: Path) -> Waveform:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_idx = None
    meta: dict[str, float] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        low = stripped.lower()
        if low.startswith("frequency,") and "real part" in low and "imaginary part" in low:
            header_idx = i
            break
        parts = [p.strip() for p in stripped.split(",")]
        if len(parts) >= 2:
            val = finite_or_nan(parts[1])
            if np.isfinite(val):
                meta[parts[0].strip().lower()] = val
    if header_idx is None:
        raise ValueError("fft_spectrum_header_not_found")
    df = pd.read_csv(path, skiprows=header_idx, engine="python")
    columns = {str(c).strip().lower(): c for c in df.columns}
    required = ["frequency", "real part", "imaginary part"]
    if any(c not in columns for c in required):
        raise ValueError("fft_spectrum_required_columns_missing")
    freq_hz = pd.to_numeric(df[columns["frequency"]], errors="coerce").to_numpy(dtype=float)
    real = pd.to_numeric(df[columns["real part"]], errors="coerce").to_numpy(dtype=float)
    imag = pd.to_numeric(df[columns["imaginary part"]], errors="coerce").to_numpy(dtype=float)
    keep = np.isfinite(freq_hz) & np.isfinite(real) & np.isfinite(imag)
    freq_hz, spec = freq_hz[keep], real[keep] + 1j * imag[keep]
    if len(freq_hz) < 4:
        raise ValueError("fft_spectrum_too_short")
    order = np.argsort(freq_hz)
    freq_hz, spec = freq_hz[order], spec[order]
    sample_rate_hz = meta.get("fft sample rate", np.nan)
    if not np.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        delta_hz = meta.get("delta frequency", np.nan)
        sample_rate_hz = float(2.0 * np.nanmax(freq_hz)) if np.isfinite(delta_hz) else np.nan
    nfft = int(meta.get("fft length", 0))
    if nfft <= 0:
        nfft = max(2 * (len(freq_hz) - 1), 2)
    rfft_len = nfft // 2 + 1
    if len(spec) < rfft_len:
        spec_for_irfft = np.pad(spec, (0, rfft_len - len(spec)), constant_values=0)
    else:
        spec_for_irfft = spec[:rfft_len]
    dt_s = 1.0 / sample_rate_hz if np.isfinite(sample_rate_hz) and sample_rate_hz > 0 else np.nan
    if not np.isfinite(dt_s):
        raise ValueError("invalid_fft_sample_rate")
    time_s = np.arange(nfft, dtype=float) * dt_s
    voltage_v = np.fft.irfft(spec_for_irfft, n=nfft) * nfft
    amp = np.abs(spec)
    freq_mhz, amp_norm = normalized_spectrum_amp(freq_hz / 1e6, amp)
    waveform = clean_waveform(time_s, voltage_v, "reconstructed_from_fft_spectrum", "irfft_from_real_imaginary_spectrum", 0.0, dt_s)
    waveform.metadata.update({
        "domain": "fft_spectrum_reconstructed_time",
        "input_data_domain": "frequency_domain_complex",
        "processing_direction": "ifft_complex_frequency_to_time",
        "fft_performed": 0,
        "ifft_performed": 1,
        "time_domain_available": 1,
        "frequency_domain_available": 1,
        "time_domain_reconstructed": 1,
        "domain_detection_status": "success",
        "frequency_MHz": freq_mhz,
        "spectrum_amp": amp_norm,
        "fft_length": nfft,
        "fft_sample_rate_Hz": sample_rate_hz,
        "spectrum_source_note": "frequency features computed from exported complex FFT; time waveform reconstructed by irfft",
    })
    return waveform


def load_frequency_magnitude_csv(path: Path) -> Waveform:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low.startswith("frequency,") and "magnitude" in low:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("frequency_magnitude_header_not_found")
    df = pd.read_csv(path, skiprows=header_idx, engine="python")
    columns = {str(c).strip().lower(): c for c in df.columns}
    freq_col = next((columns[k] for k in columns if k.startswith("frequency")), None)
    mag_col = next((columns[k] for k in columns if "magnitude" in k or "amplitude" in k), None)
    if freq_col is None or mag_col is None:
        raise ValueError("frequency_magnitude_required_columns_missing")
    freq_hz = pd.to_numeric(df[freq_col], errors="coerce").to_numpy(dtype=float)
    mag = pd.to_numeric(df[mag_col], errors="coerce").to_numpy(dtype=float)
    if "db" in str(mag_col).lower() or np.nanmedian(mag) < 0:
        amp = np.power(10.0, mag / 20.0)
    else:
        amp = np.abs(mag)
    freq_mhz, amp_norm = normalized_spectrum_amp(freq_hz / 1e6, amp)
    waveform = Waveform(np.array([], dtype=float), np.array([], dtype=float), {
        "time_column_mode": "unavailable_frequency_magnitude_only",
        "voltage_column_mode": "unavailable_frequency_magnitude_only",
        "start_time_s": np.nan,
        "time_increment_s": np.nan,
        "sampling_rate_Hz": np.nan,
        "record_length": len(freq_mhz),
        "domain": "frequency_magnitude_only",
        "input_data_domain": "frequency_domain_magnitude",
        "processing_direction": "use_frequency_data_directly",
        "fft_performed": 0,
        "ifft_performed": 0,
        "time_domain_available": 0,
        "frequency_domain_available": 1,
        "time_domain_reconstructed": 0,
        "domain_detection_status": "success",
        "frequency_MHz": freq_mhz,
        "spectrum_amp": amp_norm,
        "spectrum_source_note": "frequency features computed directly from magnitude spectrum; IFFT not performed",
    })
    return waveform


def load_from_dataframe(df: pd.DataFrame, config: dict[str, Any]) -> Waveform:
    if df.empty:
        raise ValueError("empty waveform table")
    first_rows = df.head(3).astype(str).apply(lambda row: ",".join(row), axis=1).str.lower().tolist()
    if len(first_rows) >= 2 and "sequence" in first_rows[1] and "volt" in first_rows[1] and "start" in first_rows[0]:
        start_s = finite_or_nan(df.iloc[1, 2]) if df.shape[1] > 2 else np.nan
        dt_s = finite_or_nan(df.iloc[1, 3]) if df.shape[1] > 3 else np.nan
        sequence = pd.to_numeric(df.iloc[2:, 0], errors="coerce").to_numpy(dtype=float)
        voltage = pd.to_numeric(df.iloc[2:, 1], errors="coerce").to_numpy(dtype=float)
        return clean_waveform(start_s + sequence * dt_s, voltage, "reconstructed_from_sequence", "Volt_column", start_s, dt_s)
    if not all(isinstance(c, str) for c in df.columns):
        header = [str(x) for x in df.iloc[0].tolist()]
        body = df.iloc[1:].copy()
        body.columns = header
        if any(h.lower() in ["time", "t", "ch1", "volt", "voltage"] for h in header):
            df = body
    cols = list(df.columns)
    cdet = config.get("csv_reading", {}).get("column_detection", {})
    time_col = next((c for c in cols if str(c) in cdet.get("time_column_candidates", [])), None)
    voltage_col = next((c for c in cols if str(c) in cdet.get("voltage_column_candidates", [])), None)
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    if time_col is None or voltage_col is None:
        numeric_counts = numeric_df.notna().sum().sort_values(ascending=False)
        if len(numeric_counts) < 2:
            raise ValueError("less than two numeric columns")
        time_col = numeric_counts.index[0]
        voltage_col = numeric_counts.index[1]
    return clean_waveform(
        pd.to_numeric(df[time_col], errors="coerce").to_numpy(dtype=float),
        pd.to_numeric(df[voltage_col], errors="coerce").to_numpy(dtype=float),
        "direct_time_column",
        "direct_voltage_column",
        np.nan,
        np.nan,
    )


def clean_waveform(time_s: np.ndarray, voltage: np.ndarray, time_mode: str, voltage_mode: str, start_s: float, dt_s: float) -> Waveform:
    data = pd.DataFrame({"time_s": time_s, "voltage_V": voltage}).replace([np.inf, -np.inf], np.nan).dropna()
    data = data.drop_duplicates(subset=["time_s"]).sort_values("time_s")
    if len(data) < 2:
        raise ValueError("not enough valid waveform points")
    time = data["time_s"].to_numpy(dtype=float)
    volt = data["voltage_V"].to_numpy(dtype=float)
    if np.any(np.diff(time) <= 0):
        raise ValueError("time axis is not strictly increasing")
    if not np.isfinite(dt_s):
        dt_s = float(np.median(np.diff(time)))
    if not np.isfinite(start_s):
        start_s = float(time[0])
    fs = 1.0 / dt_s if dt_s > 0 else np.nan
    return Waveform(time, volt, {
        "time_column_mode": time_mode,
        "voltage_column_mode": voltage_mode,
        "start_time_s": start_s,
        "time_increment_s": dt_s,
        "sampling_rate_Hz": fs,
        "record_length": len(time),
        "input_data_domain": "time_domain",
        "processing_direction": "forward_fft_time_to_frequency",
        "fft_performed": 1,
        "ifft_performed": 0,
        "time_domain_available": 1,
        "frequency_domain_available": 1,
        "time_domain_reconstructed": 0,
        "domain_detection_status": "success",
    })


def save_normalized(waveform: Waveform, file_id: str, run_dir: Path, audit: list[dict[str, Any]], run_id: str) -> Path:
    path = run_dir / "normalized_waveform" / "normalized_csv" / f"{file_id}_normalized.csv"
    time_df = pd.DataFrame({"time_s": waveform.time_s, "voltage_V": waveform.voltage_V})
    time_df.to_csv(path, index=False, encoding="utf-8-sig")
    audit.append(audit_row(run_id, path, "create", True, "ok", "normalized waveform"))
    workbook = path.with_suffix(".xlsx")
    freq_mhz = np.asarray(waveform.metadata.get("frequency_MHz", []), dtype=float)
    amp = np.asarray(waveform.metadata.get("spectrum_amp", []), dtype=float)
    freq_df = pd.DataFrame({"frequency_MHz": freq_mhz, "amplitude_au": amp}) if len(freq_mhz) and len(amp) else pd.DataFrame({"frequency_MHz": [], "amplitude_au": []})
    info = metadata_for_tables({"run_id": run_id, "file_id": file_id, **waveform.metadata})
    info_df = pd.DataFrame([info])
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        time_df.to_excel(writer, index=False, sheet_name="time_domain")
        freq_df.to_excel(writer, index=False, sheet_name="frequency_domain")
        info_df.to_excel(writer, index=False, sheet_name="processing_info")
    waveform.metadata["normalized_workbook_path"] = relpath(workbook)
    audit.append(audit_row(run_id, workbook, "create", True, "ok", "normalized domain workbook"))
    return path


def load_normalized(path: Path) -> Waveform:
    df = pd.read_csv(path)
    return clean_waveform(df["time_s"].to_numpy(dtype=float), df["voltage_V"].to_numpy(dtype=float), "normalized_csv", "normalized_csv", np.nan, np.nan)


def preprocess_waveform(waveform: Waveform, config: dict[str, Any]) -> dict[str, Any]:
    time = waveform.time_s
    voltage = waveform.voltage_V
    n = len(voltage)
    pre_frac = config.get("preprocessing", {}).get("baseline_correction", {}).get("pretrigger_fraction", 0.10)
    pre_n = max(1, int(n * pre_frac))
    baseline = float(np.nanmedian(voltage[:pre_n]))
    corrected = voltage - baseline
    pre = corrected[:pre_n]
    noise_med = float(np.nanmedian(pre))
    mad = float(np.nanmedian(np.abs(pre - noise_med)))
    sigma = 1.4826 * mad if mad > 0 else float(np.nanstd(pre))
    sigma = sigma if np.isfinite(sigma) and sigma > 0 else float(np.nanstd(corrected))
    sigma = sigma if np.isfinite(sigma) and sigma > 0 else 1e-12
    threshold = config.get("analysis_window", {}).get("main_burst_detection", {}).get("threshold_sigma", 6.0) * sigma
    idx = np.flatnonzero(np.abs(corrected) >= threshold)
    warning = "none"
    if len(idx) == 0:
        start_i, end_i, num_bursts = 0, n - 1, 0
        warning = config.get("analysis_window", {}).get("warning_flag_if_burst_not_found", "burst_not_found")
    else:
        dt_s = waveform.metadata.get("time_increment_s", np.nan)
        gap_s = config.get("analysis_window", {}).get("main_burst_detection", {}).get("merge_gap_s", 5e-8)
        gap_points = max(1, int(round(gap_s / dt_s))) if np.isfinite(dt_s) and dt_s > 0 else 1
        breaks = np.where(np.diff(idx) > gap_points)[0]
        starts = np.r_[idx[0], idx[breaks + 1]]
        ends = np.r_[idx[breaks], idx[-1]]
        amps = [np.max(np.abs(corrected[s : e + 1])) for s, e in zip(starts, ends)]
        main = int(np.argmax(amps))
        pre_s = config.get("analysis_window", {}).get("window_padding", {}).get("pre_burst_s", 2e-8)
        post_s = config.get("analysis_window", {}).get("window_padding", {}).get("post_burst_s", 2e-7)
        pre_pts = max(0, int(round(pre_s / dt_s))) if np.isfinite(dt_s) and dt_s > 0 else 0
        post_pts = max(0, int(round(post_s / dt_s))) if np.isfinite(dt_s) and dt_s > 0 else 0
        start_i = max(0, int(starts[main]) - pre_pts)
        end_i = min(n - 1, int(ends[main]) + post_pts)
        num_bursts = len(starts)
    return {"time_s": time, "voltage_raw_V": voltage, "voltage_V": corrected, "baseline_V": baseline, "start_i": start_i, "end_i": end_i, "burst_start_s": float(time[start_i]), "burst_end_s": float(time[end_i]), "num_bursts": int(num_bursts), "single_burst": bool(num_bursts == 1), "warning": warning}


def spectrum_from_window(time: np.ndarray, voltage: np.ndarray, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    if len(time) < 4:
        return np.array([]), np.array([])
    dt_s = float(np.median(np.diff(time)))
    y = voltage - np.nanmean(voltage)
    if config.get("fft", {}).get("window", {}).get("enabled", True):
        y = y * np.hanning(len(y))
    nfft_min = int(config.get("fft", {}).get("zero_padding", {}).get("minimum_nfft", 4096))
    nfft = max(nfft_min, 1 << (len(y) - 1).bit_length())
    freq = np.fft.rfftfreq(nfft, dt_s) / 1e6
    amp = np.abs(np.fft.rfft(y, n=nfft))
    if np.max(amp) > 0:
        amp = amp / np.max(amp)
    return freq, amp


def fit_damped_sine(time: np.ndarray, voltage: np.ndarray, f1_mhz: float, apk: float, config: dict[str, Any]) -> tuple[float, float, np.ndarray]:
    min_points = config.get("damping_fit", {}).get("fit_window", {}).get("min_points", 20)
    if len(time) < min_points or not np.isfinite(f1_mhz):
        return np.nan, np.nan, np.full_like(voltage, np.nan)
    t = time - time[0]
    keep = t <= config.get("damping_fit", {}).get("fit_window", {}).get("max_duration_s", 2e-6)
    t = t[keep]
    y = voltage[keep]

    def model(x, amp, alpha, freq_hz, phi, offset):
        return offset + amp * np.exp(-alpha * x) * np.sin(2 * np.pi * freq_hz * x + phi)

    bounds = ([0.0, 0.0, 1e6, -2 * np.pi, -np.inf], [np.inf, 1e10, 3e8, 2 * np.pi, np.inf])
    p0 = [max(abs(apk), 1e-9), 1e7, f1_mhz * 1e6, 0.0, 0.0]
    try:
        popt, _ = curve_fit(model, t, y, p0=p0, bounds=bounds, maxfev=int(config.get("damping_fit", {}).get("max_iterations", 20000)))
        yfit = model(t, *popt)
        ss_res = float(np.sum((y - yfit) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        full_fit = np.full_like(voltage, np.nan)
        full_fit[keep] = yfit
        return float(popt[1]), float(r2), full_fit
    except Exception:
        return np.nan, np.nan, np.full_like(voltage, np.nan)


def independent_peak_features(freq: np.ndarray, amp: np.ndarray, config: dict[str, Any]) -> dict[str, Any]:
    freq = np.asarray(freq, dtype=float)
    amp = np.asarray(amp, dtype=float)
    search_cfg = config.get("peak_detection", {}).get("independent_peak_detection", {}).get("frequency_range_MHz", {})
    fmin = float(search_cfg.get("min", config.get("fft", {}).get("search_band_MHz", {}).get("min", 1.0)))
    fmax = float(search_cfg.get("max", config.get("fft", {}).get("search_band_MHz", {}).get("max", 300.0)))
    keep = np.isfinite(freq) & np.isfinite(amp) & (freq >= fmin) & (freq <= fmax)
    if not np.any(keep):
        return {"f1_MHz": np.nan, "A1": np.nan, "f2_MHz": np.nan, "A2": np.nan, "fdom_MHz": np.nan, "Adom": np.nan, "independent_peak_count": 0, "shoulder_peak_flag": False, "DPR_dB": np.nan, "PSR_dB": np.nan}
    f = freq[keep]
    a = np.abs(amp[keep])
    order = np.argsort(f)
    f, a = f[order], a[order]
    if np.nanmax(a) > 0:
        a = a / np.nanmax(a)
    smooth_cfg = config.get("peak_detection", {}).get("independent_peak_detection", {}).get("smoothing_before_peak_detection", {})
    y = a.copy()
    if smooth_cfg.get("enabled", True) and len(y) >= 9:
        try:
            from scipy.signal import savgol_filter

            win = int(smooth_cfg.get("window_length_points", 9))
            win = min(win if win % 2 else win + 1, len(y) - (1 - len(y) % 2))
            if win >= 5:
                y = savgol_filter(y, win, int(smooth_cfg.get("polyorder", 2)))
        except Exception:
            y = a
    local_cfg = config.get("peak_detection", {}).get("independent_peak_detection", {}).get("local_maxima", {})
    min_height = float(local_cfg.get("min_relative_height_to_global_max", 0.08))
    df = float(np.nanmedian(np.diff(f))) if len(f) > 1 else 1.0
    distance_pts = max(1, int(round(float(local_cfg.get("min_distance_MHz", 1.0)) / df))) if df > 0 else 1
    prominence = max(1e-9, min_height * 0.20)
    peaks, props = find_peaks(y, height=min_height, prominence=prominence, distance=distance_pts)
    raw_peaks, _ = find_peaks(a, height=min_height, prominence=max(prominence * 0.25, 1e-9), distance=distance_pts)
    peaks = np.union1d(peaks, raw_peaks)
    if len(peaks) == 0:
        idx = int(np.nanargmax(a))
        peaks = np.array([idx], dtype=int)
    peaks = peaks[np.argsort(f[peaks])]
    min_sep = float(config.get("peak_detection", {}).get("f2", {}).get("candidate_requirements", {}).get("min_frequency_separation_from_f1_MHz", 5.0))
    min_valley_db = float(config.get("peak_detection", {}).get("independent_peak_detection", {}).get("peak_cluster", {}).get("min_valley_depth_for_independent_peaks_dB", 6.0))
    clusters: list[list[int]] = []
    shoulder = False
    for p in peaks:
        if not clusters:
            clusters.append([int(p)])
            continue
        prev = clusters[-1][-1]
        lo, hi = sorted((prev, int(p)))
        valley = float(np.nanmin(y[lo : hi + 1])) if hi > lo else min(float(y[prev]), float(y[p]))
        valley = max(valley, 1e-12)
        depth_db = 20.0 * math.log10(max(min(float(y[prev]), float(y[p])), 1e-12) / valley)
        same_cluster = (abs(float(f[p] - f[prev])) < min_sep) or (depth_db < min_valley_db)
        if same_cluster:
            clusters[-1].append(int(p))
            shoulder = True
        else:
            clusters.append([int(p)])
    reps = []
    for cluster in clusters:
        rep = max(cluster, key=lambda idx: a[idx])
        reps.append(int(rep))
    reps = sorted(reps, key=lambda idx: f[idx])
    ranked_reps = sorted(reps, key=lambda idx: (-float(a[idx]), float(f[idx])))
    fdom_idx = ranked_reps[0]
    # Current ML01 review convention: f1 is the strongest independent peak.
    # f2 is the next strongest independent peak from a different cluster.
    f1_idx = fdom_idx
    f2_candidates = [idx for idx in ranked_reps[1:] if abs(float(f[idx] - f[f1_idx])) >= min_sep]
    f2_idx = f2_candidates[0] if f2_candidates else None
    a1 = float(a[f1_idx])
    a2 = float(a[f2_idx]) if f2_idx is not None else np.nan
    adom = float(a[fdom_idx])
    next_for_dom = max([float(a[idx]) for idx in reps if idx != fdom_idx], default=np.nan)
    return {
        "f1_MHz": float(f[f1_idx]),
        "A1": a1,
        "f2_MHz": float(f[f2_idx]) if f2_idx is not None else np.nan,
        "A2": a2,
        "fdom_MHz": float(f[fdom_idx]),
        "Adom": adom,
        "independent_peak_count": int(len(reps)),
        "shoulder_peak_flag": bool(shoulder),
        "DPR_dB": 20.0 * math.log10(adom / next_for_dom) if np.isfinite(next_for_dom) and next_for_dom > 0 else np.nan,
        "PSR_dB": 20.0 * math.log10(a1 / a2) if np.isfinite(a2) and a2 > 0 else np.nan,
    }


def extract_features(waveform: Waveform, base: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    proc = preprocess_waveform(waveform, config)
    time = proc["time_s"]
    voltage = proc["voltage_V"]
    win = slice(proc["start_i"], proc["end_i"] + 1)
    tw = time[win]
    vw = voltage[win]
    apk_idx = int(np.nanargmax(np.abs(vw)))
    apk = float(np.abs(vw[apk_idx]))
    amin = float(np.nanmin(vw))
    app = float(np.nanmax(vw) - np.nanmin(vw))
    t_apk = float(tw[apk_idx])
    if waveform.metadata.get("domain") == "fft_spectrum_reconstructed_time":
        freq, amp = normalized_spectrum_amp(waveform.metadata.get("frequency_MHz", np.array([])), waveform.metadata.get("spectrum_amp", np.array([])))
    else:
        freq, amp = spectrum_from_window(tw, vw, config)
    search = config.get("fft", {}).get("search_band_MHz", {})
    fmin = float(search.get("min", 1.0))
    fmax = float(search.get("max", 300.0))
    nyq_mhz = waveform.metadata.get("sampling_rate_Hz", np.nan) / 2e6
    if np.isfinite(nyq_mhz):
        fmax = min(fmax, 0.9 * nyq_mhz)
    peak_info = independent_peak_features(freq, amp, config)
    f1, a1 = peak_info["f1_MHz"], peak_info["A1"]
    f2, a2 = peak_info["f2_MHz"], peak_info["A2"]
    psr = peak_info["PSR_dB"]
    snr = compute_snr(freq, amp, f1, config)
    alpha, fit_r2, fit_curve = fit_damped_sine(tw, vw, f1, apk, config)
    flags = morphology_flags(time, voltage, proc, freq, amp, f1, psr, waveform.metadata.get("sampling_rate_Hz", np.nan))
    f2_relation = classify_f2_relation(f1, f2, psr, config)
    main_warning = choose_warning(proc["warning"], flags, psr, snr, alpha, fit_r2)
    status = "success"
    if not np.isfinite(f1):
        status = "feature_extract_failed"
    elif not np.isfinite(alpha) or not np.isfinite(fit_r2):
        status = "fit_failed"
        if main_warning == "none":
            main_warning = "fit_failed"
    feature = {
        **base,
        "time_unit": "s",
        "voltage_unit": "V",
        "baseline_V": proc["baseline_V"],
        "nan_fraction": float(np.mean(~np.isfinite(waveform.voltage_V))),
        "Apk": apk,
        "Amin": amin,
        "App": app,
        "t_Apk_s": t_apk,
        "fdom_MHz": peak_info["fdom_MHz"],
        "Adom": peak_info["Adom"],
        "independent_peak_count": peak_info["independent_peak_count"],
        "shoulder_peak_flag": peak_info["shoulder_peak_flag"],
        "DPR_dB": peak_info["DPR_dB"],
        "f1_MHz": f1,
        "A1": a1,
        "f2_MHz": f2,
        "A2": a2,
        "PSR_dB": psr,
        "narrowband_SNR_dB": snr,
        "alpha": alpha,
        "rho": np.nan,
        "fit_R2": fit_r2,
        "burst_start_s": proc["burst_start_s"],
        "burst_end_s": proc["burst_end_s"],
        "num_bursts": proc["num_bursts"],
        "single_burst": proc["single_burst"],
        "f2_relation": f2_relation,
        "fsrc_MHz": np.nan,
        "alpha_src": np.nan,
        "A_fsrc": np.nan,
        "f1_to_fsrc_diff_percent": np.nan,
        "fsrc_trackable": False,
        "measurement_chain_sensitive": False,
        "ground_sensitive": False,
        "loading_sensitive": False,
        "main_warning_flag": main_warning,
        "analysis_status": status,
        "notes": "",
        **flags,
    }
    arrays = {"time": time, "voltage": voltage, "tw": tw, "vw": vw, "freq": freq, "amp": amp, "fit_time": tw, "fit_curve": fit_curve}
    return feature, arrays


def compute_snr(freq: np.ndarray, amp: np.ndarray, f1: float, config: dict[str, Any]) -> float:
    if len(freq) == 0 or not np.isfinite(f1):
        return np.nan
    half = config.get("narrowband_SNR", {}).get("signal_band", {}).get("half_width_MHz", 2.0)
    sig_mask = np.abs(freq - f1) <= half
    nb = config.get("narrowband_SNR", {}).get("noise_band", {}).get("fallback_absolute_band_MHz", {})
    noise_mask = (freq >= nb.get("min", 150.0)) & (freq <= nb.get("max", 300.0)) & ~sig_mask
    if not np.any(noise_mask):
        noise_mask = ~sig_mask
    ps = float(np.nanmean(amp[sig_mask] ** 2)) if np.any(sig_mask) else np.nan
    pn = float(np.nanmean(amp[noise_mask] ** 2)) if np.any(noise_mask) else np.nan
    return 10.0 * math.log10(ps / pn) if ps > 0 and pn > 0 else np.nan


def morphology_flags(time: np.ndarray, voltage: np.ndarray, proc: dict[str, Any], freq: np.ndarray, amp: np.ndarray, f1: float, psr: float, fs_hz: float) -> dict[str, Any]:
    vw = voltage[proc["start_i"] : proc["end_i"] + 1]
    tw = time[proc["start_i"] : proc["end_i"] + 1]
    apk = float(np.nanmax(np.abs(vw))) if len(vw) else np.nan
    env = np.abs(hilbert(vw)) if len(vw) >= 4 else np.abs(vw)
    if len(env) > 5 and np.nanmax(env) > 0:
        after_peak = env[int(np.nanargmax(env)) :]
        rises = np.sum(np.diff(after_peak) > 0.15 * np.nanmax(env))
        envelope_monotonic = bool(rises <= max(1, int(0.15 * len(after_peak))))
    else:
        envelope_monotonic = None
    zero_crossings = int(np.sum(np.diff(np.signbit(vw - np.nanmean(vw))) != 0)) if len(vw) else 0
    range_v = float(np.nanmax(voltage) - np.nanmin(voltage)) if len(voltage) else np.nan
    clipped = False
    if np.isfinite(range_v) and range_v > 0:
        tol = 0.005 * range_v
        clipped = has_consecutive(np.abs(voltage - np.nanmax(voltage)) <= tol, 3) or has_consecutive(np.abs(voltage - np.nanmin(voltage)) <= tol, 3)
    aliasing = bool(np.isfinite(f1) and np.isfinite(fs_hz) and f1 * 1e6 > 0.85 * fs_hz / 2)
    peaks, _ = find_peaks(amp, height=0.1) if len(amp) else (np.array([]), {})
    multi_peak = bool(len(peaks) >= 2 and (not np.isfinite(psr) or psr < 6.0))
    tail_start = np.searchsorted(tw, proc["burst_start_s"] + 1.0e-7) if len(tw) else 0
    tail_disturbance = bool(len(vw[tail_start:]) and np.nanmax(np.abs(vw[tail_start:])) > 0.15 * apk) if np.isfinite(apk) else False
    front_end = np.searchsorted(tw, proc["burst_start_s"] + 5.0e-8) if len(tw) else 0
    front_glitch = bool(front_end > 0 and np.nanmax(np.abs(vw[:front_end])) > 0.15 * apk) if np.isfinite(apk) else False
    overdamped = bool(zero_crossings < 3)
    nonosc = bool((not np.isfinite(f1)) or (np.isfinite(psr) and psr < 3.0))
    echo = tail_disturbance and proc["num_bursts"] <= 1
    return {
        "envelope_monotonic": envelope_monotonic,
        "front_glitch_flag": front_glitch,
        "tail_disturbance_flag": tail_disturbance,
        "reignition_flag": bool(proc["num_bursts"] >= 2),
        "multiburst_flag": bool(proc["num_bursts"] >= 2),
        "overdamped_flag": overdamped,
        "nonoscillatory_flag": nonosc,
        "clipped": clipped,
        "saturated": clipped,
        "aliasing_flag": aliasing,
        "overdrive_recovery_flag": False,
        "echo_flag": echo,
        "delayed_echo_detected": echo,
        "multi_peak_flag": multi_peak,
        "beating_flag": multi_peak,
        "period_drift_flag": False,
    }


def has_consecutive(mask: np.ndarray, count: int) -> bool:
    run = 0
    for val in mask:
        run = run + 1 if val else 0
        if run >= count:
            return True
    return False


def classify_f2_relation(f1: float, f2: float, psr: float, config: dict[str, Any]) -> str:
    if not np.isfinite(f1) or not np.isfinite(f2):
        return "unknown"
    tol = config.get("peak_detection", {}).get("f2_relation", {}).get("harmonic_tolerance_percent", 5.0) / 100.0
    if abs(f2 / f1 - 2.0) <= tol:
        return "harmonic"
    if np.isfinite(psr) and psr < config.get("peak_detection", {}).get("f2_relation", {}).get("independent_peak_min_PSR_dB", 6.0):
        return "independent_peak"
    return "noise"


def choose_warning(current: str, flags: dict[str, Any], psr: float, snr: float, alpha: float, fit_r2: float) -> str:
    if current not in {"none", "burst_not_found"}:
        return current
    for name, cond in [
        ("clipped", flags.get("clipped")),
        ("saturated", flags.get("saturated")),
        ("aliasing", flags.get("aliasing_flag")),
        ("reignition_or_multiburst", flags.get("reignition_flag") or flags.get("multiburst_flag")),
        ("echo_or_multipath", flags.get("echo_flag")),
        ("multi_peak", flags.get("multi_peak_flag")),
        ("beating", flags.get("beating_flag")),
        ("period_drift", flags.get("period_drift_flag")),
        ("overdamped_or_nonoscillatory", flags.get("overdamped_flag") or flags.get("nonoscillatory_flag")),
        ("low_snr", np.isfinite(snr) and snr < 6.0),
        ("weak_main_peak", np.isfinite(psr) and psr < 6.0),
        ("fit_failed", not np.isfinite(alpha) or not np.isfinite(fit_r2)),
        ("template_missing", True),
    ]:
        if cond:
            return name
    return "none"


def classify_waveform(feature: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    thresholds = rules.get("thresholds", {})
    version = rules.get("project", {}).get("rule_version", "")
    status = feature.get("analysis_status", "success")
    if status in {"filename_parse_failed", "csv_read_failed", "invalid_time_column", "invalid_voltage_column", "invalid_experiment_id", "feature_extract_failed"} or finite_or_nan(feature.get("record_length")) < thresholds.get("min_record_length_points", 100):
        return label("unknown", "unusable", 0, "read_or_parse_failure", "read_or_parse_failed", version)
    if feature.get("clipped") is True or feature.get("saturated") is True or feature.get("aliasing_flag") is True:
        return label("G", "unusable", 0, "clipped_saturated_or_aliased", "clipped", version)
    if feature.get("reignition_flag") is True or feature.get("multiburst_flag") is True or finite_or_nan(feature.get("num_bursts")) >= 2:
        return label("D", "unusable", 0, "multiple_pulse_or_reignition", "reignition_or_multiburst", version)
    if feature.get("echo_flag") is True or feature.get("delayed_echo_detected") is True:
        return label("H", "suspicious", 0, "echo_or_multipath_tail", "echo_or_multipath", version)
    if feature.get("measurement_chain_sensitive") is True or feature.get("ground_sensitive") is True or feature.get("loading_sensitive") is True:
        return label("E", "suspicious", 0, "pseudo_ringing_measurement_chain_artifact", "pseudo_artifact_suspected", version)
    if feature.get("overdamped_flag") is True or feature.get("nonoscillatory_flag") is True:
        return label("F", "unusable", 0, "overdamped_or_nonoscillatory", "overdamped_or_nonoscillatory", version)
    if feature.get("multi_peak_flag") is True or feature.get("beating_flag") is True or feature.get("period_drift_flag") is True or feature.get("f2_relation") == "independent_peak":
        return label("C", "suspicious", 0, "dual_mode_or_beating_competition", "multi_peak", version)
    excellent = thresholds.get("excellent", {})
    usable = thresholds.get("usable", {})
    f1, psr, snr, rho, fit_r2, alpha = [finite_or_nan(feature.get(k)) for k in ["f1_MHz", "PSR_dB", "narrowband_SNR_dB", "rho", "fit_R2", "alpha"]]
    f_ok = thresholds.get("f1_min_MHz", 1.0) <= f1 <= thresholds.get("f1_max_MHz", 200.0)
    if status == "success" and f_ok and feature.get("single_burst") is True and np.isfinite(alpha) and alpha > 0 and psr >= excellent.get("min_PSR_dB", 10.0) and snr >= excellent.get("min_SNRf_dB", 10.0) and rho >= excellent.get("min_rho", 0.85) and fit_r2 >= excellent.get("min_fit_R2", 0.9):
        return label("A", "excellent", 1, "", "none", version)
    if f_ok and feature.get("single_burst") is True and psr >= usable.get("min_PSR_dB", 10.0) and snr >= usable.get("min_SNRf_dB", 10.0):
        if feature.get("front_glitch_flag") is True or feature.get("tail_disturbance_flag") is True or rho >= usable.get("min_rho", 0.7) or fit_r2 >= usable.get("min_fit_R2", 0.7):
            return label("B", "usable", 1, "", "slight_front_glitch" if feature.get("front_glitch_flag") else "tail_disturbance" if feature.get("tail_disturbance_flag") else "none", version)
    return label("unknown", "unknown", np.nan, "unclassified", "unclassified", version, "classification_failed" if status == "success" else status)


def label(cls: str, quality: str, pass_flag: Any, reason: str, warning: str, version: str, status: str | None = None) -> dict[str, Any]:
    return {"waveform_class": cls, "quality_label": quality, "pass_flag": pass_flag, "reject_reason": reason, "main_warning_flag": warning, "classification_rule_version": version, "analysis_status": status}


def apply_fsrc(features: list[dict[str, Any]], config: dict[str, Any]) -> None:
    ref_group = REFERENCE_SOURCE_GROUP
    ref_rows = [r for r in features if r.get("group_id") == ref_group and r.get("analysis_status") in {"success", "fit_failed"}]
    f_vals = [finite_or_nan(r.get("f1_MHz")) for r in ref_rows]
    f_vals = [v for v in f_vals if np.isfinite(v)]
    alpha_vals = [finite_or_nan(r.get("alpha")) for r in ref_rows]
    alpha_vals = [v for v in alpha_vals if np.isfinite(v) and v > 0]
    fsrc = float(np.median(f_vals)) if f_vals else np.nan
    alpha_src = float(np.median(alpha_vals)) if alpha_vals else np.nan
    tol = config.get("fsrc_tracking", {}).get("loose_tolerance_percent", 10.0)
    for row in features:
        row["fsrc_MHz"] = fsrc
        row["alpha_src"] = alpha_src
        f1 = finite_or_nan(row.get("f1_MHz"))
        if np.isfinite(fsrc) and np.isfinite(f1) and fsrc > 0:
            diff = abs(f1 - fsrc) / fsrc * 100.0
            row["f1_to_fsrc_diff_percent"] = diff
            row["fsrc_trackable"] = bool(diff <= tol and finite_or_nan(row.get("narrowband_SNR_dB")) >= config.get("fsrc_tracking", {}).get("minimum_trackable_SNR_dB", 6.0))
        else:
            row["f1_to_fsrc_diff_percent"] = np.nan
            row["fsrc_trackable"] = False


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def template_signal(arrays: dict[str, np.ndarray]) -> np.ndarray:
    y = np.asarray(arrays.get("vw", []), dtype=float)
    y = y[np.isfinite(y)]
    if len(y) == 0:
        return y
    scale = float(np.nanmax(np.abs(y)))
    return y / scale if scale > 0 and np.isfinite(scale) else y


def aligned_candidate_matrix(candidate_ids: list[str], arrays_by_file: dict[str, dict[str, np.ndarray]]) -> tuple[np.ndarray, list[str]]:
    vectors, valid_ids, peaks = [], [], []
    for file_id in candidate_ids:
        vec = template_signal(arrays_by_file.get(file_id, {}))
        if len(vec) < 20:
            continue
        peak = int(np.nanargmax(np.abs(vec)))
        vectors.append(vec)
        valid_ids.append(file_id)
        peaks.append(peak)
    if not vectors:
        return np.empty((0, 0)), []
    left = min(peaks)
    right = min(len(v) - p for v, p in zip(vectors, peaks))
    if left + right < 20:
        min_len = min(len(v) for v in vectors)
        return np.vstack([v[:min_len] for v in vectors]), valid_ids
    return np.vstack([v[p - left : p + right] for v, p in zip(vectors, peaks)]), valid_ids


def choose_medoid_template(candidate_ids: list[str], arrays_by_file: dict[str, dict[str, np.ndarray]]) -> str:
    matrix, valid_ids = aligned_candidate_matrix(candidate_ids, arrays_by_file)
    if len(valid_ids) == 0:
        return ""
    if len(valid_ids) == 1:
        return valid_ids[0]
    diffs = matrix[:, None, :] - matrix[None, :, :]
    dist_sum = np.sqrt(np.sum(diffs * diffs, axis=2)).sum(axis=1)
    return valid_ids[int(np.argmin(dist_sum))]


def rho_against_template(arrays: dict[str, np.ndarray], template_arrays: dict[str, np.ndarray], config: dict[str, Any]) -> float:
    y = template_signal(arrays)
    tmpl = template_signal(template_arrays)
    if len(y) < 4 or len(tmpl) < 4:
        return np.nan
    dt_s = np.nan
    t = np.asarray(arrays.get("tw", []), dtype=float)
    if len(t) > 1:
        dt_s = float(np.nanmedian(np.diff(t)))
    max_lag_s = config.get("template_correlation", {}).get("correlation", {}).get("max_lag_s", 5.0e-8)
    max_lag = max(0, int(round(max_lag_s / dt_s))) if np.isfinite(dt_s) and dt_s > 0 else 0
    best = np.nan
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            a, b = y[-lag:], tmpl[: len(y) + lag]
        elif lag > 0:
            a, b = y[: len(y) - lag], tmpl[lag : lag + len(y) - lag]
        else:
            n = min(len(y), len(tmpl))
            a, b = y[:n], tmpl[:n]
        n = min(len(a), len(b))
        if n < 4:
            continue
        a, b = a[:n], b[:n]
        if np.nanstd(a) <= 0 or np.nanstd(b) <= 0:
            continue
        rho = float(np.corrcoef(a, b)[0, 1])
        if np.isfinite(rho) and (not np.isfinite(best) or abs(rho) > abs(best)):
            best = rho
    return best


def template_candidate_score(feature: dict[str, Any]) -> float:
    score = 0.0
    score += min(max(finite_or_nan(feature.get("PSR_dB")), 0.0), 30.0) / 30.0 * 0.25
    score += min(max(finite_or_nan(feature.get("narrowband_SNR_dB")), 0.0), 30.0) / 30.0 * 0.25
    score += min(max(finite_or_nan(feature.get("fit_R2")), 0.0), 1.0) * 0.20
    score += (0.10 if truthy(feature.get("single_burst")) else 0.0)
    score += (0.10 if truthy(feature.get("envelope_monotonic")) else 0.0)
    no_distortion = not any(truthy(feature.get(k)) for k in ["clipped", "saturated", "aliasing_flag", "reignition_flag", "multiburst_flag"])
    score += (0.10 if no_distortion else 0.0)
    return float(score)


def candidate_passes(feature: dict[str, Any], relaxed: bool, included_map: dict[str, Any], config: dict[str, Any]) -> tuple[bool, str]:
    if str(included_map.get(str(feature.get("file_name")), "1")).strip() in {"0", "False", "false"}:
        return False, "included_not_1"
    if feature.get("analysis_status") not in {"success", "fit_failed", "undefined_group", "metadata_conflict"}:
        return False, "analysis_status_not_allowed"
    if not Path(PROJECT_ROOT / str(feature.get("normalized_file_path", ""))).exists():
        return False, "normalized_file_missing"
    if not np.isfinite(finite_or_nan(feature.get("f1_MHz"))) or not np.isfinite(finite_or_nan(feature.get("Apk"))):
        return False, "invalid_f1_or_Apk"
    if any(truthy(feature.get(k)) for k in ["clipped", "saturated", "aliasing_flag", "reignition_flag", "multiburst_flag"]):
        return False, "distortion_or_multiburst"
    filt = config.get("template_correlation", {}).get("candidate_filter", {})
    thresholds = filt.get("relaxed_numeric_thresholds" if relaxed else "numeric_thresholds", {})
    min_psr = float(thresholds.get("min_PSR_dB", 6.0 if relaxed else 10.0))
    min_snr = float(thresholds.get("min_narrowband_SNR_dB", 6.0 if relaxed else 10.0))
    min_r2 = float(thresholds.get("min_fit_R2_preferred", 0.50 if relaxed else 0.70))
    if finite_or_nan(feature.get("PSR_dB")) < min_psr:
        return False, "PSR_below_threshold"
    if finite_or_nan(feature.get("narrowband_SNR_dB")) < min_snr:
        return False, "SNR_below_threshold"
    if finite_or_nan(feature.get("fit_R2")) < min_r2:
        return False, "fit_R2_below_threshold"
    return True, ""


def build_reference_template(candidate_ids: list[str], arrays_by_file: dict[str, dict[str, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    vectors: list[np.ndarray] = []
    peaks: list[int] = []
    dts: list[float] = []
    for file_id in candidate_ids:
        arrays = arrays_by_file.get(file_id, {})
        vec = template_signal(arrays)
        if len(vec) < 20:
            continue
        t = np.asarray(arrays.get("tw", []), dtype=float)
        if len(t) > 1:
            dt_s = float(np.nanmedian(np.diff(t)))
            if np.isfinite(dt_s) and dt_s > 0:
                dts.append(dt_s)
        vectors.append(vec)
        peaks.append(int(np.nanargmax(np.abs(vec))))
    if not vectors:
        return np.array([]), np.array([])
    dt_s = float(np.nanmedian(dts)) if dts else 1.0
    left = min(peaks)
    right = min(len(v) - p for v, p in zip(vectors, peaks))
    if left + right < 20:
        min_len = min(len(v) for v in vectors)
        matrix = np.vstack([v[:min_len] for v in vectors])
        time_s = np.arange(min_len, dtype=float) * dt_s
    else:
        matrix = np.vstack([v[p - left : p + right] for v, p in zip(vectors, peaks)])
        time_s = np.arange(-left, right, dtype=float) * dt_s
    voltage = np.nanmedian(matrix, axis=0)
    scale = float(np.nanmax(np.abs(voltage))) if len(voltage) else np.nan
    if np.isfinite(scale) and scale > 0:
        voltage = voltage / scale
    return time_s, voltage


def write_template_reference_figures(
    run_dir: Path,
    run_id: str,
    template_time_s: np.ndarray,
    template_voltage: np.ndarray,
    fsrc_mhz: float,
    alpha_src: float,
    config: dict[str, Any],
    audit: list[dict[str, Any]],
) -> tuple[str, str]:
    if len(template_time_s) == 0 or len(template_voltage) == 0:
        return "", ""
    template_dir = run_dir / "template"
    template_dir.mkdir(parents=True, exist_ok=True)

    time_path = template_dir / "T1_reference_template_time.png"
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(template_time_s * 1e6, template_voltage, color="#000000", lw=1.1, label=rf"$\alpha_{{src}}$ = {alpha_src:.3e} s$^{{-1}}$" if np.isfinite(alpha_src) else r"$\alpha_{src}$ = NaN")
    ax.set_xlabel("Aligned time (us)")
    ax.set_ylabel("Normalized voltage")
    ax.legend(loc="upper right", frameon=True, fontsize=7)
    fig.savefig(time_path, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    audit.append(audit_row(run_id, time_path, "create", True, "ok", "reference template time figure"))

    freq_path = template_dir / "T1_reference_template_frequency.png"
    freq, amp = spectrum_from_window(template_time_s, template_voltage, config)
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(freq, amp, color="#000000", lw=1.1)
    if np.isfinite(fsrc_mhz):
        ax.axvline(fsrc_mhz, color="#0057B8", lw=0.9, ls="--", label=rf"$f_{{src}}$ = {fsrc_mhz:.2f} MHz")
    else:
        ax.plot([], [], color="#0057B8", lw=0.9, ls="--", label=r"$f_{src}$ = NaN")
    ax.set_xlim(0, 200)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend(loc="upper right", frameon=True, fontsize=7)
    fig.savefig(freq_path, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    audit.append(audit_row(run_id, freq_path, "create", True, "ok", "reference template frequency figure"))
    return relpath(time_path), relpath(freq_path)


def write_template_outputs(
    features: list[dict[str, Any]],
    arrays_by_file: dict[str, dict[str, np.ndarray]],
    sample_index: pd.DataFrame,
    run_dir: Path,
    run_id: str,
    config: dict[str, Any],
    audit: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ref_group = REFERENCE_SOURCE_GROUP
    ref_features = [f for f in features if f.get("group_id") == ref_group]
    candidate_ids = [
        str(f.get("file_id"))
        for f in ref_features
        if f.get("analysis_status") in {"success", "fit_failed", "undefined_group", "metadata_conflict"}
        and str(f.get("file_id")) in arrays_by_file
        and len(np.asarray(arrays_by_file.get(str(f.get("file_id")), {}).get("vw", []), dtype=float)) >= 20
    ]
    f_vals = [finite_or_nan(f.get("f1_MHz")) for f in ref_features]
    f_vals = [v for v in f_vals if np.isfinite(v)]
    alpha_vals = [finite_or_nan(f.get("alpha")) for f in ref_features]
    alpha_vals = [v for v in alpha_vals if np.isfinite(v) and v > 0]
    fsrc_mhz = float(np.median(f_vals)) if f_vals else np.nan
    alpha_src = float(np.median(alpha_vals)) if alpha_vals else np.nan
    candidate_rows = []
    for feature in features:
        file_id = str(feature.get("file_id"))
        is_ref = feature.get("group_id") == ref_group
        has_arrays = file_id in candidate_ids
        reason = "" if has_arrays else ("not_reference_group" if not is_ref else "reference_waveform_unavailable")
        candidate_rows.append({
            "run_id": run_id,
            "file_id": file_id,
            "file_name": feature.get("file_name", ""),
            "group_id": feature.get("group_id", ""),
            "config_group": feature.get("config_group", ""),
            "distance_m": feature.get("distance_m", np.nan),
            "load_condition": feature.get("load_condition", ""),
            "ground_condition": feature.get("ground_condition", ""),
            "block_id": feature.get("block_id", ""),
            "sample_index": feature.get("sample_index", ""),
            "candidate_pool": "fixed_reference_group" if has_arrays else "rejected",
            "candidate_pass": int(has_arrays),
            "ranking_score": np.nan,
            "PSR_dB": feature.get("PSR_dB", np.nan),
            "narrowband_SNR_dB": feature.get("narrowband_SNR_dB", np.nan),
            "fit_R2": feature.get("fit_R2", np.nan),
            "single_burst": feature.get("single_burst", np.nan),
            "envelope_monotonic": feature.get("envelope_monotonic", np.nan),
            "clipped": feature.get("clipped", np.nan),
            "saturated": feature.get("saturated", np.nan),
            "aliasing_flag": feature.get("aliasing_flag", np.nan),
            "reignition_flag": feature.get("reignition_flag", np.nan),
            "multiburst_flag": feature.get("multiburst_flag", np.nan),
            "selected_as_template": int(has_arrays),
            "reject_reason": reason,
            "notes": "",
        })
    if not candidate_ids:
        selection = {"run_id": run_id, "template_mode": "template_missing", "manual_template_used": 0, "reference_group": ref_group, "fallback_level": "none", "template_confidence": "none", "template_method": "fixed_reference_group_only", "candidate_N": 0, "selected_template_file_id": "", "selected_template_file_name": "", "selected_template_file_path": "", "selected_template_normalized_path": "", "fsrc_MHz": fsrc_mhz, "alpha_src": alpha_src, "template_time_figure_path": "", "template_frequency_figure_path": "", "fallback_used": 0, "fallback_reason": "fixed_reference_group_missing", "warning_flag": "template_missing", "status": "reference_group_missing", "notes": "No fallback template generated."}
        write_csv(run_dir / "template" / "selected_template_waveform.csv", [], ["time_s", "voltage_V"], audit, run_id, "empty template waveform")
        write_template_overlay(run_dir, run_id, [], "", arrays_by_file, audit, config, selection)
        return [selection], candidate_rows
    template_time_s, template_voltage = build_reference_template(candidate_ids, arrays_by_file)
    template_arrays = {"tw": template_time_s, "vw": template_voltage}
    for feature in features:
        feature["rho"] = rho_against_template(arrays_by_file.get(str(feature.get("file_id")), {}), template_arrays, config)
    template_df = pd.DataFrame({"time_s": template_time_s, "voltage_V": template_voltage})
    template_path = run_dir / "template" / "selected_template_waveform.csv"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_df.to_csv(template_path, index=False, encoding="utf-8-sig")
    audit.append(audit_row(run_id, template_path, "create", True, "ok", "fixed reference template waveform"))
    time_fig, freq_fig = write_template_reference_figures(run_dir, run_id, template_time_s, template_voltage, fsrc_mhz, alpha_src, config, audit)
    selection = {
        "run_id": run_id,
        "template_mode": "fixed_reference_group_median",
        "manual_template_used": 0,
        "reference_group": ref_group,
        "fallback_level": "none",
        "template_confidence": "reference_group_defined",
        "template_method": "peak_aligned_median_of_all_reference_waveforms",
        "candidate_N": len(candidate_ids),
        "selected_template_file_id": "T1_reference_median",
        "selected_template_file_name": "selected_template_waveform.csv",
        "selected_template_file_path": relpath(template_path),
        "selected_template_normalized_path": relpath(template_path),
        "fsrc_MHz": fsrc_mhz,
        "alpha_src": alpha_src,
        "template_time_figure_path": time_fig,
        "template_frequency_figure_path": freq_fig,
        "fallback_used": 0,
        "fallback_reason": "",
        "warning_flag": "none",
        "status": "success",
        "notes": "Template, fsrc, and alpha_src are derived only from the fixed reference group.",
    }
    write_template_overlay(run_dir, run_id, candidate_ids, "T1_reference_median", arrays_by_file, audit, config, selection)
    return [selection], candidate_rows


def write_template_overlay(run_dir: Path, run_id: str, candidate_ids: list[str], selected_id: str, arrays_by_file: dict[str, dict[str, np.ndarray]], audit: list[dict[str, Any]], config: dict[str, Any], selection: dict[str, Any]) -> None:
    path = run_dir / "template" / "template_overlay_check.png"
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for file_id in candidate_ids:
        arrays = arrays_by_file.get(file_id, {})
        t = np.asarray(arrays.get("tw", []), dtype=float)
        y = template_signal(arrays)
        if len(t) and len(y):
            n = min(len(t), len(y))
            ax.plot((t[:n] - t[0]) * 1e6, y[:n], lw=1.2 if file_id == selected_id else 0.6, alpha=1.0 if file_id == selected_id else 0.35, color="#D7263D" if file_id == selected_id else "#7F7F7F", label=file_id if file_id == selected_id else None)
    if selected_id:
        ax.legend(frameon=False, fontsize=7)
    ax.set_xlabel("Aligned time (us)")
    ax.set_ylabel("Normalized voltage")
    ax.set_title(f"{selection.get('reference_group', '')}, N={selection.get('candidate_N', 0)}", fontsize=8)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    audit.append(audit_row(run_id, path, "create", True, "ok", "template overlay check"))


def style_axes(plot_cfg: dict[str, Any]) -> None:
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": plot_cfg.get("font", {}).get("fallback", ["DejaVu Sans"]), "axes.grid": False, "axes.facecolor": "white", "figure.facecolor": "white"})


def mm_fig(plot_cfg: dict[str, Any], preset: str) -> tuple[float, float]:
    p = plot_cfg.get("figure_size", {}).get("presets", {}).get(preset, {"width_mm": 72, "height_mm": 52})
    return p.get("width_mm", 72) / 25.4, p.get("height_mm", 52) / 25.4


def save_figure(fig: plt.Figure, base: Path, formats: list[str], dpi: int, audit: list[dict[str, Any]], run_id: str) -> None:
    for fmt in ["png"]:
        path = base.with_suffix(f".{fmt}")
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.08, facecolor="white")
        audit.append(audit_row(run_id, path, "create", True, "ok", "figure export"))
    plt.close(fig)


def plot_single(feature: dict[str, Any], arrays: dict[str, np.ndarray], run_dir: Path, audit: list[dict[str, Any]], run_id: str, plot_cfg: dict[str, Any], time_display_start_us: float = DEFAULT_TIME_DISPLAY_START_US) -> dict[str, str]:
    file_id = feature["file_id"]
    formats = plot_cfg.get("export", {}).get("formats", ["png"])
    dpi = int(plot_cfg.get("export", {}).get("dpi", 600))
    style_axes(plot_cfg)
    paths = {}
    base_time = run_dir / "single_waveform" / "figures_time_domain" / f"{file_id}_time"
    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "single_standard"))
    ax.plot(arrays["time"] * 1e6, arrays["voltage"], lw=0.8, color="black")
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Voltage (V)")
    apply_time_display_window(ax, [(arrays["time"] * 1e6, arrays["voltage"])], time_display_start_us)
    add_single_annotation(
        ax,
        feature,
        [
            latex_param("alpha", feature.get("alpha"), "s^-1"),
            latex_param("Apk", feature.get("Apk"), "V"),
        ],
    )
    save_figure(fig, base_time, formats, dpi, audit, run_id)
    paths["figure_time_path"] = relpath(base_time.with_suffix(".png"))

    base_freq = run_dir / "single_waveform" / "figures_frequency_domain" / f"{file_id}_freq"
    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "single_standard"))
    ax.plot(arrays["freq"], arrays["amp"], lw=0.8, color="black")
    for key, color, ls, label in [
        ("f1_MHz", "#ED1C24", "--", r"$f_1$"),
        ("f2_MHz", "#7F7F7F", ":", r"$f_2$"),
        ("fsrc_MHz", "#0057B8", "-.", r"$f_{src}$"),
    ]:
        value = finite_or_nan(feature.get(key))
        if np.isfinite(value):
            ax.axvline(value, color=color, ls=ls, lw=0.75)
            mark_frequency_peak(ax, arrays["freq"], arrays["amp"], value, label, color)
    ax.set_xlim(0, min(200, np.nanmax(arrays["freq"]) if len(arrays["freq"]) else 200))
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Amplitude (a.u.)")
    freq_params = [
        latex_param("f1", feature.get("f1_MHz"), "MHz"),
        latex_param("f2", feature.get("f2_MHz"), "MHz"),
        latex_param("PSR_dB", feature.get("PSR_dB"), "dB"),
        latex_param("narrowband_SNR_dB", feature.get("narrowband_SNR_dB"), "dB"),
    ]
    if np.isfinite(finite_or_nan(feature.get("fsrc_MHz"))):
        freq_params.append(latex_param("fsrc", feature.get("fsrc_MHz"), "MHz"))
    add_single_annotation(ax, feature, freq_params)
    save_figure(fig, base_freq, formats, dpi, audit, run_id)
    paths["figure_freq_path"] = relpath(base_freq.with_suffix(".png"))

    base_fit = run_dir / "single_waveform" / "figures_fit" / f"{file_id}_fit"
    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "single_standard"))
    ax.plot(arrays["fit_time"] * 1e6, arrays["vw"], lw=0.75, color="black")
    if np.any(np.isfinite(arrays["fit_curve"])):
        ax.plot(arrays["fit_time"] * 1e6, arrays["fit_curve"], lw=0.9, color="#ED1C24", ls="--")
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Voltage (V)")
    add_single_annotation(
        ax,
        feature,
        [
            latex_param("alpha", feature.get("alpha"), "s^-1"),
            latex_param("fit_R2", feature.get("fit_R2"), ""),
            latex_param("rho", feature.get("rho"), ""),
        ],
    )
    save_figure(fig, base_fit, formats, dpi, audit, run_id)
    paths["figure_fit_path"] = relpath(base_fit.with_suffix(".png"))
    return paths


def waveform_full_label(feature: dict[str, Any]) -> str:
    label = str(feature.get("file_id") or Path(str(feature.get("file_name", "waveform"))).stem)
    return "\n".join(textwrap.wrap(label, width=30, break_long_words=False, break_on_hyphens=False)) or "waveform"


def add_single_annotation(ax: plt.Axes, feature: dict[str, Any], param_lines: list[str]) -> None:
    lines = [waveform_full_label(feature)] + [line for line in param_lines if line]
    ax.text(
        0.98,
        0.96,
        "\n".join(lines),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=5.6,
        color="black",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.15},
    )


def mark_frequency_peak(ax: plt.Axes, freq: np.ndarray, amp: np.ndarray, target_mhz: float, label: str, color: str) -> None:
    if len(freq) == 0 or len(amp) == 0 or not np.isfinite(target_mhz):
        return
    idx = int(np.nanargmin(np.abs(freq - target_mhz)))
    if idx < 0 or idx >= len(freq) or not np.isfinite(amp[idx]):
        return
    ax.plot(freq[idx], amp[idx], marker="o", ms=2.8, mfc="white", mec=color, mew=0.7, linestyle="none", zorder=5)
    ax.annotate(
        label,
        xy=(freq[idx], amp[idx]),
        xytext=(5, 7),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=6.2,
        color=color,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.05},
        arrowprops={"arrowstyle": "-", "color": color, "lw": 0.45, "shrinkA": 0, "shrinkB": 2},
    )


def plot_group_figures(group_id: str, gf: pd.DataFrame, arrays_by_file: dict[str, dict[str, np.ndarray]], run_dir: Path, audit: list[dict[str, Any]], run_id: str, plot_cfg: dict[str, Any], time_display_start_us: float = DEFAULT_TIME_DISPLAY_START_US) -> tuple[str, str, str]:
    formats = plot_cfg.get("export", {}).get("formats", ["png"])
    dpi = int(plot_cfg.get("export", {}).get("dpi", 600))
    style_axes(plot_cfg)
    time_path = run_dir / "group_summary" / "overlay_time_domain" / f"{group_id}_overlay_time"
    freq_path = run_dir / "group_summary" / "overlay_frequency_domain" / f"{group_id}_overlay_freq"
    stat_path = run_dir / "group_summary" / "statistics_figures" / f"{group_id}_statistics"
    color_by_label = group_sample_color_map(gf, plot_cfg)
    waveform_rows = load_group_waveform_rows(gf, color_by_label, arrays_by_file)

    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "full_width_multipanel"))
    fig.subplots_adjust(left=0.13, bottom=0.17, right=0.985, top=0.965)
    time_annotations = []
    time_series_for_limits = []
    for item in waveform_rows:
        x_us = item["waveform"].time_s * 1e6
        y_v = item["waveform"].voltage_V
        ax.plot(x_us, y_v, lw=0.75, alpha=0.85, label=item["label"], color=item["color"])
        time_series_for_limits.append((x_us, y_v))
        time_annotations.append((item["label"], "alpha", finite_or_nan(item["row"].get("alpha")), item["color"], "s^-1", False))
        time_annotations.append((item["label"], "Apk", finite_or_nan(item["row"].get("Apk")), item["color"], "V", True))
    if not waveform_rows:
        plt.close(fig)
        time_figure = ""
    else:
        ax.set_xlabel("Time (us)")
        ax.set_ylabel("Voltage (V)")
        ax.yaxis.set_label_coords(-0.06, 0.5)
        apply_time_display_window(ax, time_series_for_limits, time_display_start_us)
        legend = add_framed_legend(ax, title="Sample")
        draw_parameter_stack(ax, time_annotations, "s^-1", anchor=parameter_anchor_below_artist(ax, legend), top_artist=legend)
        save_figure(fig, time_path, formats, dpi, audit, run_id)
        time_figure = relpath(time_path.with_suffix(".png"))

    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "full_width_multipanel"))
    fig.subplots_adjust(left=0.13, bottom=0.17, right=0.985, top=0.965)
    freq_annotations = []
    for item in waveform_rows:
        f, a = spectrum_for_overlay_item(item)
        ax.plot(f, a, lw=0.75, alpha=0.85, label=item["label"], color=item["color"])
        freq_annotations.append((item["label"], "f1", finite_or_nan(item["row"].get("f1_MHz")), item["color"]))
    if not waveform_rows:
        plt.close(fig)
        freq_figure = ""
    else:
        ax.set_xlim(0, 200)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Amplitude (a.u.)")
        ax.yaxis.set_label_coords(-0.06, 0.5)
        legend = add_framed_legend(ax, title="Sample")
        draw_parameter_stack(ax, freq_annotations, "MHz", anchor=parameter_anchor_below_artist(ax, legend), top_artist=legend)
        save_figure(fig, freq_path, formats, dpi, audit, run_id)
        freq_figure = relpath(freq_path.with_suffix(".png"))

    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "full_width_multipanel"))
    fig.subplots_adjust(left=0.13, bottom=0.17, right=0.985, top=0.965)
    stat_figure = ""
    if not gf.empty:
        labels, vals = collect_stat_plot_values(gf, ["f1_MHz", "Apk", "PSR_dB"])
        if vals:
            display_labels = [parameter_display_name(label) for label in labels]
            ax.boxplot(vals, tick_labels=display_labels, showfliers=True)
            for x_pos, col in enumerate(labels, start=1):
                series = pd.to_numeric(gf[col], errors="coerce")
                valid_rows = gf[series.notna()]
                for offset, (_, row) in enumerate(valid_rows.iterrows()):
                    y_val = finite_or_nan(row.get(col))
                    if np.isfinite(y_val):
                        sample_label = short_waveform_label(row)
                        color = color_by_label.get(sample_label, trace_color(len(color_by_label), plot_cfg))
                        ax.plot(x_pos, y_val, "o", ms=3.8, mfc=color, mec="black", mew=0.35, label=sample_label if col == labels[0] else None)
            ax.set_ylabel("Value")
            ax.yaxis.set_label_coords(-0.06, 0.5)
            add_zoom_insets_for_small_ranges(ax, gf, labels, color_by_label)
            legend = add_sample_color_legend(ax, color_by_label)
            draw_group_statistics_box(ax, gf, labels, anchor=parameter_anchor_below_artist(ax, legend), top_artist=legend)
            save_figure(fig, stat_path, formats, dpi, audit, run_id)
            stat_figure = relpath(stat_path.with_suffix(".png"))
        else:
            plt.close(fig)
    else:
        plt.close(fig)
    return time_figure, freq_figure, stat_figure


def sanitize_id(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def select_comparison_row(group: pd.DataFrame) -> pd.Series:
    work = group.copy()
    work["_block_num"] = work["block_id"].astype(str).str.extract(r"B(\d+)")[0].astype(float)
    work = work.sort_values(["_block_num", "file_name"])
    preferred = work[work["block_id"].astype(str) == "B01"]
    return (preferred if not preferred.empty else work).iloc[0]


def distance_sort_key(distance: float) -> tuple[int, float]:
    priority = [0.1, 0.3, 0.6, 0.8]
    for idx, value in enumerate(priority):
        if np.isclose(distance, value):
            return (idx, distance)
    return (len(priority), distance)


def distance_token_from_m(distance: float) -> str:
    if not np.isfinite(distance):
        return ""
    return "D" + f"{distance:.1f}".replace(".", "p") + "m"


def aligned_trace_from_arrays(row: pd.Series, arrays_by_file: dict[str, dict[str, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    arrays = arrays_by_file.get(str(row.get("file_id")), {})
    time = np.asarray(arrays.get("time", []), dtype=float)
    voltage = np.asarray(arrays.get("voltage", []), dtype=float)
    if len(time) == 0 or len(voltage) == 0:
        return np.array([]), np.array([])
    peak_t = finite_or_nan(row.get("t_Apk_s"))
    if not np.isfinite(peak_t):
        peak_t = float(time[int(np.nanargmax(np.abs(voltage)))])
    return (time - peak_t) * 1e6, voltage


def full_waveform_legend_label(row: pd.Series) -> str:
    file_id = str(row.get("file_id", "")).strip()
    if file_id:
        return file_id
    parts = [
        str(row.get("config_group", "")).strip(),
        distance_token_from_m(finite_or_nan(row.get("distance_m"))),
        str(row.get("load_condition", "")).strip(),
        str(row.get("ground_condition", "")).strip(),
        str(row.get("block_id", "")).strip(),
        str(row.get("sample_index", "")).strip(),
    ]
    return "_".join(p for p in parts if p)


def comparison_trace_from_row(
    row: pd.Series,
    idx: int,
    arrays_by_file: dict[str, dict[str, np.ndarray]],
    plot_cfg: dict[str, Any],
) -> dict[str, Any]:
    x_us, y_v = aligned_trace_from_arrays(row, arrays_by_file)
    arrays = arrays_by_file.get(str(row.get("file_id")), {})
    return {
        "x_us": x_us,
        "y_v": y_v,
        "freq": np.asarray(arrays.get("freq", []), dtype=float),
        "amp": np.asarray(arrays.get("amp", []), dtype=float),
        "label": full_waveform_legend_label(row),
        "color": comparison_trace_color(idx),
        "row": row,
    }


def save_aligned_time_comparison(
    traces: list[dict[str, Any]],
    base: Path,
    title_label: str,
    run_id: str,
    audit: list[dict[str, Any]],
    plot_cfg: dict[str, Any],
) -> str:
    formats = plot_cfg.get("export", {}).get("formats", ["png"])
    dpi = int(plot_cfg.get("export", {}).get("dpi", 600))
    style_axes(plot_cfg)
    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "full_width_multipanel"))
    fig.subplots_adjust(left=0.13, bottom=0.17, right=0.985, top=0.965)
    visible = []
    time_annotations = []
    for trace in traces:
        x_us, y_v = trace["x_us"], trace["y_v"]
        keep = np.isfinite(x_us) & np.isfinite(y_v) & (x_us >= 0)
        if not np.any(keep):
            continue
        ax.plot(x_us[keep], y_v[keep], lw=0.9, alpha=0.88, color=trace["color"], label=trace["label"])
        visible.append((x_us[keep], y_v[keep]))
        row = trace["row"]
        time_annotations.append((trace["label"], "alpha", finite_or_nan(row.get("alpha")), trace["color"], "s^-1", False))
        time_annotations.append((trace["label"], "Apk", finite_or_nan(row.get("Apk")), trace["color"], "V", True))
    ax.set_xlabel("Aligned time (us)")
    ax.set_ylabel("Voltage (V)")
    ax.yaxis.set_label_coords(-0.06, 0.5)
    apply_time_display_window(ax, visible, 0.0)
    legend = add_framed_legend(ax, title="Trace")
    draw_parameter_stack(ax, time_annotations, "s^-1", anchor=parameter_anchor_below_artist(ax, legend), top_artist=legend)
    save_figure(fig, base, formats, dpi, audit, run_id)
    return relpath(base.with_suffix(".png"))


def save_frequency_comparison(
    traces: list[dict[str, Any]],
    base: Path,
    title_label: str,
    run_id: str,
    audit: list[dict[str, Any]],
    plot_cfg: dict[str, Any],
) -> str:
    formats = plot_cfg.get("export", {}).get("formats", ["png"])
    dpi = int(plot_cfg.get("export", {}).get("dpi", 600))
    style_axes(plot_cfg)
    fig, ax = plt.subplots(figsize=mm_fig(plot_cfg, "full_width_multipanel"))
    fig.subplots_adjust(left=0.13, bottom=0.17, right=0.985, top=0.965)
    freq_annotations = []
    plotted = 0
    for trace in traces:
        freq = np.asarray(trace.get("freq", []), dtype=float)
        amp = np.asarray(trace.get("amp", []), dtype=float)
        keep = np.isfinite(freq) & np.isfinite(amp)
        if not np.any(keep):
            continue
        ax.plot(freq[keep], amp[keep], lw=0.9, alpha=0.88, color=trace["color"], label=trace["label"])
        row = trace["row"]
        freq_annotations.append((trace["label"], "f1", finite_or_nan(row.get("f1_MHz")), trace["color"], "MHz", False))
        freq_annotations.append((trace["label"], "f2", finite_or_nan(row.get("f2_MHz")), trace["color"], "MHz", True))
        freq_annotations.append((trace["label"], "PSR_dB", finite_or_nan(row.get("PSR_dB")), trace["color"], "dB", True))
        plotted += 1
    if plotted < 2:
        plt.close(fig)
        return ""
    ax.set_xlim(0, 200)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.yaxis.set_label_coords(-0.06, 0.5)
    legend = add_framed_legend(ax, title="Trace")
    draw_parameter_stack(ax, freq_annotations, "MHz", anchor=parameter_anchor_below_artist(ax, legend), top_artist=legend)
    save_figure(fig, base, formats, dpi, audit, run_id)
    return relpath(base.with_suffix(".png"))


def generate_distance_s001_comparisons(
    features: list[dict[str, Any]],
    arrays_by_file: dict[str, dict[str, np.ndarray]],
    run_dir: Path,
    audit: list[dict[str, Any]],
    run_id: str,
    plot_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    df = pd.DataFrame(features)
    if df.empty:
        return []
    rows = []
    s001 = df[df["sample_index"].astype(str) == "S001"].copy()
    for keys, group in s001.groupby(["date", "config_group", "load_condition", "ground_condition"], dropna=False):
        selected = []
        for distance, dgroup in group.groupby(pd.to_numeric(group["distance_m"], errors="coerce")):
            if not np.isfinite(distance):
                continue
            selected.append((float(distance), select_comparison_row(dgroup)))
        selected = sorted(selected, key=lambda item: distance_sort_key(item[0]))
        if len(selected) < 2:
            continue
        traces = []
        for idx, (distance, row) in enumerate(selected):
            trace = comparison_trace_from_row(row, idx, arrays_by_file, plot_cfg)
            if len(trace["x_us"]) == 0:
                continue
            traces.append(trace)
        if len(traces) < 2:
            continue
        date, config_group, load_condition, ground_condition = keys
        stem = sanitize_id(f"{date}_{config_group}_{load_condition}_{ground_condition}_S001_distance_compare")
        base = run_dir / "group_summary" / "distance_S001_comparison" / stem
        time_figure_path = save_aligned_time_comparison(traces, Path(str(base) + "_time"), stem, run_id, audit, plot_cfg)
        frequency_figure_path = save_frequency_comparison(traces, Path(str(base) + "_freq"), stem, run_id, audit, plot_cfg)
        rows.append({
            "run_id": run_id,
            "comparison_id": stem,
            "date": date,
            "config_group": config_group,
            "load_condition": load_condition,
            "ground_condition": ground_condition,
            "N_distances": len(traces),
            "trace_labels": "; ".join(t["label"] for t in traces),
            "selected_file_ids": "; ".join(str(t["row"].get("file_id")) for t in traces),
            "time_figure_path": time_figure_path,
            "frequency_figure_path": frequency_figure_path,
            "status": "success",
            "notes": "",
        })
    return rows


def generate_config_min_distance_s001_comparisons(
    features: list[dict[str, Any]],
    arrays_by_file: dict[str, dict[str, np.ndarray]],
    run_dir: Path,
    audit: list[dict[str, Any]],
    run_id: str,
    plot_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    df = pd.DataFrame(features)
    if df.empty:
        return []
    rows = []
    s001 = df[df["sample_index"].astype(str) == "S001"].copy()
    config_order = ["G1", "G2", "G3", "G4"]
    for keys, group in s001.groupby(["date", "load_condition", "ground_condition"], dropna=False):
        selected = []
        for config_group in config_order:
            cgroup = group[group["config_group"].astype(str) == config_group].copy()
            if cgroup.empty:
                continue
            cgroup["_distance_num"] = pd.to_numeric(cgroup["distance_m"], errors="coerce")
            available = sorted([float(v) for v in cgroup["_distance_num"].dropna().unique()], key=distance_sort_key)
            if not available:
                continue
            distance = available[0]
            selected.append((config_group, distance, select_comparison_row(cgroup[np.isclose(cgroup["_distance_num"], distance)])))
        if len(selected) < 2:
            continue
        traces = []
        for idx, (config_group, distance, row) in enumerate(selected):
            trace = comparison_trace_from_row(row, idx, arrays_by_file, plot_cfg)
            if len(trace["x_us"]) == 0:
                continue
            traces.append(trace)
        if len(traces) < 2:
            continue
        date, load_condition, ground_condition = keys
        stem = sanitize_id(f"{date}_{load_condition}_{ground_condition}_config_min_distance_S001_compare")
        base = run_dir / "group_summary" / "config_min_distance_S001_comparison" / stem
        time_figure_path = save_aligned_time_comparison(traces, Path(str(base) + "_time"), stem, run_id, audit, plot_cfg)
        frequency_figure_path = save_frequency_comparison(traces, Path(str(base) + "_freq"), stem, run_id, audit, plot_cfg)
        rows.append({
            "run_id": run_id,
            "comparison_id": stem,
            "date": date,
            "load_condition": load_condition,
            "ground_condition": ground_condition,
            "N_configs": len(traces),
            "trace_labels": "; ".join(t["label"] for t in traces),
            "selected_file_ids": "; ".join(str(t["row"].get("file_id")) for t in traces),
            "time_figure_path": time_figure_path,
            "frequency_figure_path": frequency_figure_path,
            "status": "success",
            "notes": "",
        })
    return rows


def generate_config_same_distance_s001_comparisons(
    features: list[dict[str, Any]],
    arrays_by_file: dict[str, dict[str, np.ndarray]],
    run_dir: Path,
    audit: list[dict[str, Any]],
    run_id: str,
    plot_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    df = pd.DataFrame(features)
    if df.empty:
        return []
    rows = []
    s001 = df[df["sample_index"].astype(str) == "S001"].copy()
    s001["_distance_num"] = pd.to_numeric(s001["distance_m"], errors="coerce")
    s001 = s001[np.isfinite(s001["_distance_num"])]
    config_order = ["G1", "G2", "G3", "G4"]
    for keys, group in s001.groupby(["date", "_distance_num"], dropna=False):
        selected = []
        for config_group in config_order:
            cgroup = group[group["config_group"].astype(str) == config_group].copy()
            if cgroup.empty:
                continue
            selected.append((config_group, select_comparison_row(cgroup)))
        if len(selected) < 2:
            continue
        traces = []
        for idx, (_config_group, row) in enumerate(selected):
            trace = comparison_trace_from_row(row, idx, arrays_by_file, plot_cfg)
            if len(trace["x_us"]) == 0:
                continue
            traces.append(trace)
        if len(traces) < 2:
            continue
        date, distance = keys
        distance = float(distance)
        stem = sanitize_id(f"{date}_{distance_token_from_m(distance)}_config_same_distance_S001_compare")
        base = run_dir / "group_summary" / "config_same_distance_S001_comparison" / stem
        time_figure_path = save_aligned_time_comparison(traces, Path(str(base) + "_time"), stem, run_id, audit, plot_cfg)
        frequency_figure_path = save_frequency_comparison(traces, Path(str(base) + "_freq"), stem, run_id, audit, plot_cfg)
        rows.append({
            "run_id": run_id,
            "comparison_id": stem,
            "date": date,
            "distance_m": distance,
            "N_configs": len(traces),
            "trace_labels": "; ".join(t["label"] for t in traces),
            "selected_file_ids": "; ".join(str(t["row"].get("file_id")) for t in traces),
            "time_figure_path": time_figure_path,
            "frequency_figure_path": frequency_figure_path,
            "status": "success",
            "notes": "",
        })
    return rows


def group_sample_color_map(gf: pd.DataFrame, plot_cfg: dict[str, Any]) -> dict[str, str]:
    color_by_label: dict[str, str] = {}
    if gf.empty:
        return color_by_label
    for _, row in gf.iterrows():
        sample_label = short_waveform_label(row)
        if sample_label not in color_by_label:
            color_by_label[sample_label] = trace_color(len(color_by_label), plot_cfg)
    return color_by_label


def load_group_waveform_rows(gf: pd.DataFrame, color_by_label: dict[str, str], arrays_by_file: dict[str, dict[str, np.ndarray]] | None = None) -> list[dict[str, Any]]:
    rows = []
    if gf.empty:
        return rows
    arrays_by_file = arrays_by_file or {}
    for _, row in gf.iterrows():
        normalized_path = PROJECT_ROOT / str(row.get("normalized_file_path", ""))
        if not normalized_path.exists():
            continue
        sample_label = short_waveform_label(row)
        rows.append(
            {
                "row": row,
                "waveform": load_normalized(normalized_path),
                "arrays": arrays_by_file.get(str(row.get("file_id")), {}),
                "label": sample_label,
                "color": color_by_label.get(sample_label, "black"),
            }
        )
    return rows


def spectrum_for_overlay_item(item: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    arrays = item.get("arrays", {})
    freq = np.asarray(arrays.get("freq", []), dtype=float)
    amp = np.asarray(arrays.get("amp", []), dtype=float)
    if len(freq) and len(amp):
        return freq, amp
    return spectrum_for_overlay(item["waveform"])


def spectrum_for_overlay(waveform: Waveform) -> tuple[np.ndarray, np.ndarray]:
    overlay_cfg = {"analysis_window": {}, "preprocessing": {"baseline_correction": {"pretrigger_fraction": 0.1}}, "fft": {"window": {"enabled": True}, "zero_padding": {"minimum_nfft": 4096}}}
    proc = preprocess_waveform(waveform, overlay_cfg)
    return spectrum_from_window(proc["time_s"][proc["start_i"] : proc["end_i"] + 1], proc["voltage_V"][proc["start_i"] : proc["end_i"] + 1], overlay_cfg)


def collect_stat_plot_values(gf: pd.DataFrame, candidate_columns: list[str]) -> tuple[list[str], list[np.ndarray]]:
    labels = []
    values_by_label = []
    for col in candidate_columns:
        if col not in gf:
            continue
        values = pd.to_numeric(gf[col], errors="coerce").dropna().to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        if len(values):
            labels.append(col)
            values_by_label.append(values)
    return labels, values_by_label


def short_waveform_label(row: pd.Series) -> str:
    file_name = str(row.get("file_name", ""))
    match = re.search(r"_S(\d{3})(?:\.csv)?$", file_name)
    if match:
        return f"S{match.group(1)}"
    sample_index = str(row.get("sample_index", ""))
    if sample_index:
        return sample_index
    return str(row.get("file_id", "waveform"))


def trace_color(index: int, plot_cfg: dict[str, Any]) -> str:
    palette = plot_cfg.get("color_palette", {}).get("cycle_hex") or GROUP_WAVEFORM_COLORS
    return str(palette[index % len(palette)])


def comparison_trace_color(index: int) -> str:
    return COMPARISON_TRACE_COLORS[index % len(COMPARISON_TRACE_COLORS)]


def add_framed_legend(ax: plt.Axes, title: str = "Sample"):
    handles, labels = ax.get_legend_handles_labels()
    colors = []
    kept_labels = []
    for handle, label in zip(handles, labels):
        if not label or label.startswith("_"):
            continue
        color = "black"
        if hasattr(handle, "get_color"):
            color = handle.get_color()
        colors.append(color)
        kept_labels.append(label)
    return add_color_legend_box(ax, kept_labels, colors, title=title, anchor=SAMPLE_LEGEND_ANCHOR)


def add_sample_color_legend(ax: plt.Axes, color_by_label: dict[str, str]):
    return add_color_legend_box(
        ax,
        list(color_by_label.keys()),
        list(color_by_label.values()),
        title="Sample",
        anchor=SAMPLE_LEGEND_ANCHOR,
    )


def add_color_legend_box(
    ax: plt.Axes,
    labels: list[str],
    colors: list[str],
    title: str,
    anchor: tuple[float, float],
) -> AnchoredOffsetbox:
    row_left = 0.0
    row_height = FIGURE_LEGEND_FONT_SIZE + 3.0
    title_height = FIGURE_LEGEND_FONT_SIZE + 4.0
    row_gap = 1.5
    box_width = COLOR_LEGEND_BOX_WIDTH_PT
    line_width = COLOR_LEGEND_LINE_WIDTH_PT
    box_height = title_height + max(len(labels), 1) * row_height + max(len(labels) - 1, 0) * row_gap
    canvas = DrawingArea(box_width, box_height, 0, 0)
    canvas.add_artist(
        Text(
            x=0.5 * box_width,
            y=box_height - 0.65 * title_height,
            text=title,
            fontsize=FIGURE_LEGEND_FONT_SIZE,
            color="black",
            va="center",
            ha="center",
        )
    )
    for row_i, (label, color) in enumerate(zip(labels, colors)):
        y_mid = box_height - title_height - 0.5 * row_height - row_i * (row_height + row_gap)
        canvas.add_artist(Line2D([row_left, row_left + line_width], [y_mid, y_mid], color=color, linewidth=1.2))
        canvas.add_artist(
            Text(
                x=row_left + line_width + 3.0,
                y=y_mid,
                text=str(label),
                fontsize=FIGURE_LEGEND_FONT_SIZE,
                color="black",
                va="center",
                ha="left",
            )
        )
    box = AnchoredOffsetbox(
        loc="upper right",
        child=canvas,
        pad=0.25,
        borderpad=0.0,
        frameon=True,
        bbox_to_anchor=anchor,
        bbox_transform=ax.transAxes,
    )
    ax.add_artist(box)
    frame = box.patch
    frame.set_edgecolor(FIGURE_LEGEND_FRAME_EDGE)
    frame.set_linewidth(FIGURE_LEGEND_FRAME_WIDTH)
    frame.set_facecolor(FIGURE_LEGEND_FRAME_FACE)
    frame.set_alpha(FIGURE_LEGEND_FRAME_ALPHA)
    return box


def draw_parameter_stack(
    ax: plt.Axes,
    annotations: list[tuple[Any, ...]],
    unit: str,
    anchor: tuple[float, float] = PARAMETER_BOX_ANCHOR,
    top_artist: Any | None = None,
) -> None:
    if not annotations:
        return
    rows = []
    for entry in annotations:
        sample_label, name, value, color = entry[:4]
        unit_for_row = entry[4] if len(entry) > 4 else unit
        continuation = bool(entry[5]) if len(entry) > 5 else False
        value_text = f"{value:.3g}" if np.isfinite(value) else "NaN"
        name_text = parameter_math_name(name)
        unit_text = unit_math_text(unit_for_row)
        prefix_text = f"{sample_label}: "
        prefix_props = {"fontsize": FIGURE_LEGEND_FONT_SIZE, "color": color}
        if continuation:
            prefix_props = {"fontsize": FIGURE_LEGEND_FONT_SIZE, "color": color, "alpha": 0.0}
        prefix_area = TextArea(prefix_text, textprops=prefix_props)
        parameter_area = TextArea(
            f"{name_text}={value_text} {unit_text}",
            textprops={"fontsize": FIGURE_LEGEND_FONT_SIZE, "color": color},
        )
        rows.append(HPacker(children=[prefix_area, parameter_area], align="baseline", pad=0, sep=0.0))
    add_parameter_offset_box(ax, rows, anchor=anchor, top_artist=top_artist)


def draw_group_statistics_box(
    ax: plt.Axes,
    gf: pd.DataFrame,
    labels: list[str],
    anchor: tuple[float, float] = PARAMETER_BOX_ANCHOR,
    top_artist: Any | None = None,
) -> None:
    labels_out = []
    for col in labels:
        series = pd.to_numeric(gf[col], errors="coerce").dropna()
        if len(series):
            med = float(series.median())
            q75 = float(series.quantile(0.75))
            q25 = float(series.quantile(0.25))
            labels_out.append(f"{parameter_math_name(col)}: median={med:.3g}, IQR={q75 - q25:.3g}")
    if not labels_out:
        return
    add_parameter_legend_box(ax, labels_out, ["black"] * len(labels_out), anchor=anchor, top_artist=top_artist)


def add_parameter_offset_box(
    ax: plt.Axes,
    rows: list[HPacker],
    anchor: tuple[float, float],
    top_artist: Any | None = None,
) -> None:
    title = TextArea(
        "Parameters",
        textprops={"fontsize": FIGURE_LEGEND_FONT_SIZE, "color": "black", "ha": "center"},
    )
    detail_block = VPacker(children=rows, align="left", pad=0, sep=2.0)
    packed = VPacker(children=[title, detail_block], align="center", pad=0, sep=2.0)
    box = AnchoredOffsetbox(
        loc="upper right",
        child=packed,
        pad=0.25,
        borderpad=0.0,
        frameon=True,
        bbox_to_anchor=anchor,
        bbox_transform=ax.transAxes,
    )
    ax.add_artist(box)
    frame = box.patch
    frame.set_edgecolor(FIGURE_LEGEND_FRAME_EDGE)
    frame.set_linewidth(FIGURE_LEGEND_FRAME_WIDTH)
    frame.set_facecolor(FIGURE_LEGEND_FRAME_FACE)
    frame.set_alpha(FIGURE_LEGEND_FRAME_ALPHA)
    if top_artist is not None:
        align_box_to_top_artist(ax, box, top_artist)


def add_zoom_insets_for_small_ranges(ax: plt.Axes, gf: pd.DataFrame, labels: list[str], color_by_label: dict[str, str]) -> None:
    global_values = []
    for col in labels:
        global_values.extend(pd.to_numeric(gf[col], errors="coerce").dropna().tolist())
    global_values = np.asarray(global_values, dtype=float)
    global_values = global_values[np.isfinite(global_values)]
    if len(global_values) < 2:
        return
    global_span = float(np.max(global_values) - np.min(global_values))
    if global_span <= 0:
        return
    n_labels = max(len(labels), 1)
    for x_pos, col in enumerate(labels, start=1):
        values = pd.to_numeric(gf[col], errors="coerce").dropna().to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        if len(values) < 2:
            continue
        local_span = float(np.max(values) - np.min(values))
        if local_span / global_span > 0.03:
            continue
        width = min(0.22, 0.72 / n_labels)
        height = 0.34
        center = (x_pos - 0.5) / n_labels
        left = min(max(center - width / 2, 0.05), 0.95 - width)
        bottom = 0.53
        inset = ax.inset_axes([left, bottom, width, height])
        inset.boxplot([values], tick_labels=[parameter_display_name(col)], showfliers=True)
        series = pd.to_numeric(gf[col], errors="coerce")
        for _, row in gf[series.notna()].iterrows():
            sample_label = short_waveform_label(row)
            y_val = finite_or_nan(row.get(col))
            if np.isfinite(y_val):
                color = color_by_label.get(sample_label, "black")
                inset.plot(1, y_val, "o", ms=3.2, mfc=color, mec="black", mew=0.35)
        set_adaptive_metric_ylim(inset, values)
        inset.tick_params(axis="x", labelsize=INSET_XTICK_FONT_SIZE, direction="out", length=2.0, width=0.55)
        inset.tick_params(axis="y", labelsize=INSET_YTICK_FONT_SIZE, direction="out", length=2.0, width=0.55)
        for spine in inset.spines.values():
            spine.set_edgecolor("black")
            spine.set_linewidth(FIGURE_LEGEND_FRAME_WIDTH)


def parameter_anchor_below_artist(ax: plt.Axes, artist: Any | None) -> tuple[float, float]:
    if artist is None:
        return PARAMETER_BOX_ANCHOR
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = artist.get_window_extent(renderer=renderer)
    gap_px = LEGEND_PARAMETER_GAP_PT * fig.dpi / 72.0
    right, top = ax.transAxes.inverted().transform((bbox.x1, bbox.y0 - gap_px))
    return (float(right), float(min(max(top, 0.05), 0.98)))


def add_parameter_legend_box(
    ax: plt.Axes,
    labels: list[str],
    colors: list[str],
    anchor: tuple[float, float],
    top_artist: Any | None = None,
):
    handles = [Line2D([0], [0], linestyle="none", linewidth=0.0, color="none") for _ in labels]
    legend = Legend(
        ax,
        handles=handles,
        labels=labels,
        loc="upper right",
        bbox_to_anchor=anchor,
        bbox_transform=ax.transAxes,
        fontsize=FIGURE_LEGEND_FONT_SIZE,
        title="Parameters",
        title_fontsize=FIGURE_LEGEND_FONT_SIZE,
        frameon=True,
        borderpad=0.35,
        borderaxespad=0.0,
        handlelength=0.0,
        handletextpad=0.0,
        labelspacing=0.35,
    )
    legend._legend_box.align = "center"
    legend.get_title().set_ha("center")
    for text, color in zip(legend.get_texts(), colors):
        text.set_color(color)
        text.set_ha("left")
    ax.add_artist(legend)
    frame = legend.get_frame()
    frame.set_edgecolor(FIGURE_LEGEND_FRAME_EDGE)
    frame.set_linewidth(FIGURE_LEGEND_FRAME_WIDTH)
    frame.set_facecolor(FIGURE_LEGEND_FRAME_FACE)
    frame.set_alpha(FIGURE_LEGEND_FRAME_ALPHA)
    if top_artist is not None:
        align_parameter_legend_to_top_artist(ax, legend, top_artist)
    return legend


def align_parameter_legend_to_top_artist(ax: plt.Axes, parameter_legend: Legend, top_artist: Any) -> None:
    align_box_to_top_artist(ax, parameter_legend, top_artist)


def align_box_to_top_artist(ax: plt.Axes, parameter_artist: Any, top_artist: Any) -> None:
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    top_bbox = top_artist.get_window_extent(renderer=renderer)
    param_bbox = parameter_artist.get_window_extent(renderer=renderer)
    gap_px = LEGEND_PARAMETER_GAP_PT * fig.dpi / 72.0
    dx = top_bbox.x1 - param_bbox.x1
    dy = (top_bbox.y0 - gap_px) - param_bbox.y1
    current_anchor = parameter_artist.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
    current_disp = ax.transAxes.transform((current_anchor.x1, current_anchor.y1))
    adjusted_anchor = ax.transAxes.inverted().transform((current_disp[0] + dx, current_disp[1] + dy))
    parameter_artist.set_bbox_to_anchor(tuple(adjusted_anchor), transform=ax.transAxes)
    fig.canvas.draw()
    target_width = parameter_artist.get_window_extent(renderer=renderer).width
    resizable_box = None
    if hasattr(top_artist, "_legend_box"):
        resizable_box = top_artist._legend_box
    elif hasattr(top_artist, "get_child"):
        resizable_box = top_artist.get_child()
    elif hasattr(top_artist, "child"):
        resizable_box = top_artist.child
    if resizable_box is not None and hasattr(resizable_box, "set_width"):
        low = 1.0
        high = max(2.0, target_width * 1.5)
        for _ in range(24):
            mid = 0.5 * (low + high)
            resizable_box.set_width(mid)
            fig.canvas.draw()
            top_width = top_artist.get_window_extent(renderer=renderer).width
            if top_width < target_width:
                low = mid
            else:
                high = mid
            if abs(top_width - target_width) < 0.05:
                break
    draw_matched_color_frame(ax, top_artist, parameter_artist)


def draw_matched_color_frame(ax: plt.Axes, top_artist: Any, parameter_artist: Any) -> None:
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    top_bbox = top_artist.get_window_extent(renderer=renderer)
    parameter_bbox = parameter_artist.get_window_extent(renderer=renderer)
    if hasattr(top_artist, "patch"):
        top_artist.patch.set_visible(False)
    x0, y0 = ax.transAxes.inverted().transform((parameter_bbox.x0, top_bbox.y0))
    x1, y1 = ax.transAxes.inverted().transform((parameter_bbox.x1, top_bbox.y1))
    frame = Rectangle(
        (x0, y0),
        x1 - x0,
        y1 - y0,
        transform=ax.transAxes,
        facecolor=FIGURE_LEGEND_FRAME_FACE,
        edgecolor=FIGURE_LEGEND_FRAME_EDGE,
        linewidth=FIGURE_LEGEND_FRAME_WIDTH,
        alpha=FIGURE_LEGEND_FRAME_ALPHA,
        zorder=top_artist.get_zorder() - 0.1,
        clip_on=False,
    )
    ax.add_patch(frame)


def add_framed_text_box(ax: plt.Axes, children: list[TextArea], anchor: tuple[float, float]) -> None:
    packed = VPacker(children=children, align="right", pad=0, sep=2.0)
    box = AnchoredOffsetbox(
        loc="upper right",
        child=packed,
        pad=0.25,
        borderpad=0.0,
        frameon=True,
        bbox_to_anchor=anchor,
        bbox_transform=ax.transAxes,
    )
    ax.add_artist(box)
    frame = box.patch
    frame.set_edgecolor(FIGURE_LEGEND_FRAME_EDGE)
    frame.set_linewidth(FIGURE_LEGEND_FRAME_WIDTH)
    frame.set_facecolor(FIGURE_LEGEND_FRAME_FACE)
    frame.set_alpha(FIGURE_LEGEND_FRAME_ALPHA)


def parameter_math_name(name: str) -> str:
    mapping = {
        "alpha": r"$\alpha$",
        "f1": r"$f_1$",
        "f1_MHz": r"$f_1$",
        "f2": r"$f_2$",
        "fsrc": r"$f_{src}$",
        "Apk": r"$A_{pk}$",
        "PSR_dB": r"$\mathrm{PSR}$",
        "narrowband_SNR_dB": r"$\mathrm{SNR}_f$",
        "fit_R2": r"$R^2$",
        "rho": r"$\rho$",
    }
    return mapping.get(name, name)


def latex_param(name: str, value: Any, unit: str = "") -> str:
    value_num = finite_or_nan(value)
    value_text = latex_number(value_num)
    unit_text = unit_math_text(unit)
    if unit_text:
        return f"{parameter_math_name(name)}={value_text} {unit_text}"
    return f"{parameter_math_name(name)}={value_text}"


def latex_number(value: float) -> str:
    if not np.isfinite(value):
        return r"$\mathrm{NaN}$"
    if value == 0:
        return "0"
    abs_value = abs(value)
    if abs_value >= 1e4 or abs_value < 1e-2:
        exponent = int(math.floor(math.log10(abs_value)))
        mantissa = value / (10**exponent)
        return rf"${mantissa:.3g}\times10^{{{exponent}}}$"
    return f"{value:.3g}"


def parameter_display_name(name: str) -> str:
    mapping = {
        "f1_MHz": r"$f_1$ (MHz)",
        "Apk": r"$A_{pk}$ (V)",
        "PSR_dB": r"$\mathrm{PSR}$ (dB)",
    }
    return mapping.get(name, name)


def parameter_axis_label(name: str) -> str:
    mapping = {
        "f1_MHz": r"$f_1$ (MHz)",
        "Apk": r"$A_{pk}$ (V)",
        "PSR_dB": r"$\mathrm{PSR}$ (dB)",
    }
    return mapping.get(name, name)


def unit_math_text(unit: str) -> str:
    if unit == "s^-1":
        return r"$\mathrm{s}^{-1}$"
    if unit == "MHz":
        return r"$\mathrm{MHz}$"
    if unit == "V":
        return r"$\mathrm{V}$"
    if unit == "dB":
        return r"$\mathrm{dB}$"
    return unit


def set_adaptive_metric_ylim(ax: plt.Axes, values: np.ndarray) -> None:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    center = 0.5 * (vmin + vmax)
    span = vmax - vmin
    baseline = max(abs(center), abs(vmin), abs(vmax), 1.0)
    min_span = baseline * 0.006
    span = max(span, min_span)
    pad = span * 0.65
    ax.set_ylim(vmin - pad, vmax + pad)


def apply_time_display_window(ax: plt.Axes, series: list[tuple[np.ndarray, np.ndarray]], start_us: float) -> None:
    finite_start = finite_or_nan(start_us)
    if not np.isfinite(finite_start):
        finite_start = DEFAULT_TIME_DISPLAY_START_US
    right_values = []
    visible_y = []
    for x_raw, y_raw in series:
        x = np.asarray(x_raw, dtype=float)
        y = np.asarray(y_raw, dtype=float)
        keep = np.isfinite(x) & np.isfinite(y)
        if not np.any(keep):
            continue
        x, y = x[keep], y[keep]
        right_values.append(float(np.nanmax(x)))
        visible = x >= finite_start
        if np.any(visible):
            visible_y.extend(y[visible].tolist())
    if right_values:
        right = max(right_values)
        if right > finite_start:
            ax.set_xlim(finite_start, right)
    values = np.asarray(visible_y, dtype=float)
    values = values[np.isfinite(values)]
    if len(values):
        ymin, ymax = float(np.nanmin(values)), float(np.nanmax(values))
        if ymax > ymin:
            pad = 0.08 * (ymax - ymin)
            ax.set_ylim(ymin - pad, ymax + pad)


def estimate_time_display_start_us(features: list[dict[str, Any]], arrays_by_file: dict[str, dict[str, np.ndarray]]) -> float:
    markers = []
    for feature in features:
        if str(feature.get("config_group")) == "G2":
            continue
        arrays = arrays_by_file.get(str(feature.get("file_id")), {})
        time = np.asarray(arrays.get("time", []), dtype=float) * 1e6
        voltage = np.asarray(arrays.get("voltage", []), dtype=float)
        keep = np.isfinite(time) & np.isfinite(voltage)
        if np.sum(keep) < 20:
            continue
        time, voltage = time[keep], voltage[keep]
        voltage = voltage - np.nanmedian(voltage)
        max_abs = float(np.nanmax(np.abs(voltage)))
        if not np.isfinite(max_abs) or max_abs <= 0:
            continue
        env = np.abs(hilbert(voltage)) / max_abs
        for i, t_us in enumerate(time):
            if t_us < 0.08:
                continue
            j = np.searchsorted(time, t_us + 0.03)
            if j > i and np.nanpercentile(env[i:j], 75) < 0.55:
                markers.append(float(t_us))
                break
    if not markers:
        return DEFAULT_TIME_DISPLAY_START_US
    return float(round(max(DEFAULT_TIME_DISPLAY_START_US, np.nanquantile(markers, 0.90)), 2))


def update_sample_index(raw_files: list[Path], run_id: str, audit: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    path = METADATA_DIR / "sample_index.csv"
    old = read_table_flexible(path)
    manual = {}
    if not old.empty:
        for _, row in old.iterrows():
            manual[str(row.get("file_name", ""))] = {col: row.get(col, "") for col in ["included", "manual_note", "notes"] if col in old.columns}
    rows, errors, seen = [], [], set()
    for raw in raw_files:
        try:
            meta = parse_filename(raw)
            row = {"file_name": raw.name, "file_path": relpath(raw), "date": meta["date"], "experiment_id": meta["experiment_id"], "group_id": meta["group_id"], "config_group": meta["config_group"], "distance_m": meta["distance_m"], "load_condition": meta["load_condition"], "ground_condition": meta["ground_condition"], "block_id": meta["block_id"], "sample_index": meta["sample_index"], "included": 1, "manual_note": ""}
            for col, val in manual.get(raw.name, {}).items():
                if col in row and pd.notna(val) and str(val) != "":
                    row[col] = val
            if row["file_name"] in seen:
                errors.append(error_row(run_id, raw, "duplicate_file_name", "duplicate file_name in sample index", "metadata", "Check duplicated raw files."))
            seen.add(row["file_name"])
            rows.append(row)
        except Exception as exc:
            errors.append(error_row(run_id, raw, "filename_parse_failed", str(exc), "metadata", "Rename file according to file_naming_rule.md or add metadata to sample_index.csv."))
    df = pd.DataFrame(rows)
    for f in SAMPLE_INDEX_FIELDS:
        if f not in df.columns:
            df[f] = ""
    existed = path.exists()
    df[SAMPLE_INDEX_FIELDS].to_csv(path, index=False, encoding="utf-8-sig")
    audit.append(audit_row(run_id, path, "update" if existed else "create", True, "ok", "sample index regenerated while preserving included/manual_note"))
    xlsx = METADATA_DIR / "sample_index.xlsx"
    existed_xlsx = xlsx.exists()
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        df[SAMPLE_INDEX_FIELDS].to_excel(writer, index=False, sheet_name="sample_index")
    audit.append(audit_row(run_id, xlsx, "update" if existed_xlsx else "create", True, "ok", "Excel view regenerated from sample_index.csv"))
    return df[SAMPLE_INDEX_FIELDS], errors


def error_row(run_id: str, raw: Path, error_type: str, message: str, step: str, action: str) -> dict[str, Any]:
    return {"run_id": run_id, "file_name": raw.name, "file_path": relpath(raw), "error_type": error_type, "error_message": message, "processing_step": step, "suggested_action": action, "time_stamp": now_text()}


def copy_config_snapshot(run_dir: Path, run_id: str, configs: dict[str, dict[str, Any]], audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for source, target in {"analysis_config.yaml": "analysis_config_used.yaml", "classification_rules.yaml": "classification_rules_used.yaml", "plot_style_origin.yaml": "plot_style_origin_used.yaml"}.items():
        dst = run_dir / "config_snapshot" / target
        shutil.copy2(CONFIG_DIR / source, dst)
        audit.append(audit_row(run_id, dst, "create", True, "ok", "config snapshot copy"))
    rows = []
    for source, cfg in configs.items():
        for key, value in flatten_dict(cfg):
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            rows.append({"run_id": run_id, "config_item": key, "config_value": value, "source_file": source, "description": ""})
    return rows


def script_reuse_audit(run_dir: Path, run_id: str, audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name in REQUIRED_SCRIPTS:
        path = SCRIPTS_DIR / name
        exists = path.exists()
        backup_path = ""
        if exists:
            dst = run_dir / "logs" / "script_backup" / name
            shutil.copy2(path, dst)
            backup_path = relpath(dst)
            audit.append(audit_row(run_id, dst, "create", True, "ok", "script backup"))
        rows.append({"run_id": run_id, "script_name": name, "script_path": relpath(path), "exists": int(exists), "reused": int(exists and path.stat().st_size > 0), "modified": 0, "modification_reason": "", "backup_path": backup_path, "status": "ok" if exists and path.stat().st_size > 0 else "missing_or_empty"})
    return rows


def summarize_groups(features: list[dict[str, Any]], labels: list[dict[str, Any]], group_def: pd.DataFrame, arrays_by_file: dict[str, dict[str, np.ndarray]], run_dir: Path, audit: list[dict[str, Any]], run_id: str, plot_cfg: dict[str, Any], time_display_start_us: float = DEFAULT_TIME_DISPLAY_START_US) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fdf, ldf = pd.DataFrame(features), pd.DataFrame(labels)
    group_ids = set(fdf.get("group_id", pd.Series(dtype=str)).dropna().astype(str).tolist())
    if not group_def.empty and "group_id" in group_def.columns:
        group_ids.update(group_def["group_id"].dropna().astype(str).tolist())
    stats_rows, quality_rows = [], []
    for group_id in sorted(group_ids):
        gf = fdf[fdf["group_id"] == group_id] if not fdf.empty else pd.DataFrame()
        gl = ldf[ldf["group_id"] == group_id] if not ldf.empty else pd.DataFrame()
        first = gf.iloc[0].to_dict() if not gf.empty else group_definition_row(group_def, group_id)
        n_total = int(len(gl))
        n_excluded = int((gl["pass_flag"].fillna(0).astype(str) == "0").sum()) if not gl.empty else 0
        formal = gf[gf["quality_label"].isin(["excellent", "usable"])] if not gf.empty and "quality_label" in gf else pd.DataFrame()
        qcounts = {q: int((gl["quality_label"] == q).sum()) if not gl.empty else 0 for q in ["excellent", "usable", "suspicious", "unusable"]}
        ccounts = {c: int((gl["waveform_class"] == c).sum()) if not gl.empty else 0 for c in list("ABCDEFGH")}
        ratios = {q: (qcounts[q] / n_total * 100.0 if n_total else 0.0) for q in qcounts}
        pass_ratio = float((pd.to_numeric(gl["pass_flag"], errors="coerce").fillna(0) == 1).sum() / n_total * 100.0) if n_total else 0.0
        overlay_time, overlay_freq, stat_fig = plot_group_figures(group_id, gf, arrays_by_file, run_dir, audit, run_id, plot_cfg, time_display_start_us)
        stats_rows.append({"run_id": run_id, "group_id": group_id, "config_group": first.get("config_group", ""), "distance_m": first.get("distance_m", np.nan), "load_condition": first.get("load_condition", ""), "ground_condition": first.get("ground_condition", ""), "N_total": n_total, "N_analyzed": int(len(gf)), "N_excluded": n_excluded, "f1_median_MHz": median(formal, "f1_MHz"), "f1_IQR_MHz": iqr(formal, "f1_MHz"), "f1_CV_percent": cv(formal, "f1_MHz"), "alpha_median": median(formal[formal["waveform_class"] == "A"] if not formal.empty else formal, "alpha"), "alpha_IQR": iqr(formal[formal["waveform_class"] == "A"] if not formal.empty else formal, "alpha"), "alpha_CV_percent": cv(formal[formal["waveform_class"] == "A"] if not formal.empty else formal, "alpha"), "Apk_median": median(formal, "Apk"), "Apk_IQR": iqr(formal, "Apk"), "Apk_CV_percent": cv(formal, "Apk"), "PSR_median_dB": median(formal, "PSR_dB"), "PSR_IQR_dB": iqr(formal, "PSR_dB"), "SNR_median_dB": median(formal, "narrowband_SNR_dB"), "SNR_IQR_dB": iqr(formal, "narrowband_SNR_dB"), "rho_median": median(formal, "rho"), "rho_IQR": iqr(formal, "rho"), "fit_R2_median": median(formal, "fit_R2"), "dominant_waveform_class": dominant(gl, "waveform_class"), "excellent_ratio_percent": ratios["excellent"], "usable_ratio_percent": ratios["usable"], "suspicious_ratio_percent": ratios["suspicious"], "unusable_ratio_percent": ratios["unusable"], "pass_ratio_percent": pass_ratio, "group_decision": group_decision(pass_ratio, ratios, len(gf)), "overlay_time_figure_path": overlay_time, "overlay_freq_figure_path": overlay_freq, "statistics_figure_path": stat_fig, "notes": "" if n_total else "insufficient_valid_data"})
        quality_rows.append({"run_id": run_id, "group_id": group_id, "N_total": n_total, "N_excellent": qcounts["excellent"], "N_usable": qcounts["usable"], "N_suspicious": qcounts["suspicious"], "N_unusable": qcounts["unusable"], "excellent_ratio_percent": ratios["excellent"], "usable_ratio_percent": ratios["usable"], "suspicious_ratio_percent": ratios["suspicious"], "unusable_ratio_percent": ratios["unusable"], **{f"{c}_count": ccounts[c] for c in list("ABCDEFGH")}, "main_failure_reason": dominant(gl[gl["pass_flag"].fillna(0).astype(str) != "1"] if not gl.empty else gl, "reject_reason"), "recommendation": "manual_review_required" if n_total else "insufficient_valid_data"})
    return stats_rows, quality_rows


def group_definition_row(group_def: pd.DataFrame, group_id: str) -> dict[str, Any]:
    if not group_def.empty and "group_id" in group_def.columns:
        row = group_def[group_def["group_id"].astype(str) == group_id]
        if not row.empty:
            return row.iloc[0].to_dict()
    return {"group_id": group_id}


def median(df: pd.DataFrame, col: str) -> float:
    return float(pd.to_numeric(df[col], errors="coerce").median()) if not df.empty and col in df else np.nan


def iqr(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df:
        return np.nan
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    return float(s.quantile(0.75) - s.quantile(0.25)) if len(s) else np.nan


def cv(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df:
        return np.nan
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    mean = float(s.mean()) if len(s) else np.nan
    return float(s.std(ddof=1) / mean * 100.0) if len(s) > 1 and abs(mean) > 1e-12 else np.nan


def dominant(df: pd.DataFrame, col: str) -> str:
    if df.empty or col not in df:
        return ""
    vals = df[col].dropna().astype(str)
    return vals.value_counts().idxmax() if len(vals) else ""


def group_decision(pass_ratio: float, ratios: dict[str, float], n_analyzed: int) -> str:
    if n_analyzed < 5:
        return "not_recommended"
    if pass_ratio >= 80 and ratios.get("unusable", 0) <= 10 and ratios.get("suspicious", 0) <= 20 and n_analyzed >= 10:
        return "recommended"
    if pass_ratio >= 60 and ratios.get("unusable", 0) <= 25 and n_analyzed >= 10:
        return "usable_with_caution"
    if ratios.get("suspicious", 0) > 30:
        return "suspicious_group"
    if pass_ratio < 60 or ratios.get("unusable", 0) > 25:
        return "not_recommended"
    return "manual_review_required"


def export_excel(run_dir: Path, run_id: str, sample_index: pd.DataFrame, audit: list[dict[str, Any]]) -> str:
    xlsx = run_dir / "excel_report" / "waveform_analysis_summary.xlsx"
    sheets = {
        "sample_index": sample_index,
        "format_detection_summary": pd.read_csv(run_dir / "normalized_waveform" / "format_detection_summary.csv"),
        "single_waveform_features": pd.read_csv(run_dir / "single_waveform" / "single_waveform_features.csv"),
        "single_waveform_labels": pd.read_csv(run_dir / "single_waveform" / "single_waveform_labels.csv"),
        "group_statistics": pd.read_csv(run_dir / "group_summary" / "group_statistics.csv"),
        "group_quality_summary": pd.read_csv(run_dir / "group_summary" / "group_quality_summary.csv"),
        "error_files": pd.read_csv(run_dir / "logs" / "error_files.csv"),
        "excluded_files": pd.read_csv(run_dir / "logs" / "excluded_files.csv"),
        "config_snapshot": pd.read_csv(run_dir / "config_snapshot" / "config_snapshot.csv"),
        "template_selection": pd.read_csv(run_dir / "template" / "template_selection.csv"),
        "template_candidates": pd.read_csv(run_dir / "template" / "template_candidates.csv"),
    }
    distance_comparison_csv = run_dir / "group_summary" / "distance_S001_comparison" / "distance_S001_comparison_index.csv"
    if distance_comparison_csv.exists():
        sheets["distance_S001_comparison"] = pd.read_csv(distance_comparison_csv)
    config_comparison_csv = run_dir / "group_summary" / "config_min_distance_S001_comparison" / "config_min_distance_S001_comparison_index.csv"
    if config_comparison_csv.exists():
        sheets["config_min_distance_S001"] = pd.read_csv(config_comparison_csv)
    config_same_distance_csv = run_dir / "group_summary" / "config_same_distance_S001_comparison" / "config_same_distance_S001_comparison_index.csv"
    if config_same_distance_csv.exists():
        sheets["config_same_distance_S001"] = pd.read_csv(config_same_distance_csv)
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        pd.DataFrame({"item": ["run_id", "created_by"], "value": [run_id, "03_scripts/run_all.py"]}).to_excel(writer, index=False, sheet_name="README")
        for sheet, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=sheet[:31])
    audit.append(audit_row(run_id, xlsx, "create", True, "ok", "Excel generated from CSV tables"))
    return relpath(xlsx)


def export_report(run_dir: Path, run_id: str, counts: dict[str, Any], audit: list[dict[str, Any]]) -> tuple[str, str]:
    md = run_dir / "report" / "quick_report.md"
    lines = ["# ML01 Waveform Analysis Quick Report", "", f"run_id: {run_id}", f"raw_files_found: {counts.get('raw_files_found', 0)}", f"files_normalized: {counts.get('files_normalized', 0)}", f"files_analyzed: {counts.get('files_analyzed', 0)}", f"errors: {counts.get('errors', 0)}", f"excluded: {counts.get('excluded', 0)}", "", "This report is an execution summary only. Physical interpretation requires manual inspection."]
    md.write_text("\n".join(lines), encoding="utf-8")
    audit.append(audit_row(run_id, md, "create", True, "ok", "quick markdown report"))
    pdf = run_dir / "report" / "quick_report.pdf"
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    ax.axis("off")
    ax.text(0.02, 0.95, "\n".join(lines), va="top", family="monospace", fontsize=9)
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    audit.append(audit_row(run_id, pdf, "create", True, "ok", "quick PDF report via matplotlib"))
    return relpath(md), relpath(pdf)


def write_run_log(run_dir: Path, run_id: str, start_time: str, end_time: str, counts: dict[str, Any], warnings: list[str], errors: list[dict[str, Any]], audit: list[dict[str, Any]], smoke: bool) -> None:
    path = run_dir / "logs" / "run.log"
    packages = {}
    for mod in ["numpy", "pandas", "scipy", "matplotlib", "yaml", "openpyxl", "xlrd"]:
        try:
            m = importlib.import_module(mod)
            packages[mod] = getattr(m, "__version__", "unknown")
        except Exception:
            packages[mod] = "not_available"
    text = {"run_id": run_id, "mode": "smoke_test" if smoke else "full_analysis", "start_time": start_time, "end_time": end_time, "python_version": sys.version, "package_versions": packages, "command_line": " ".join(sys.argv), "number_of_input_raw_files": counts.get("raw_files_found", 0), "number_of_parsed_files": counts.get("files_normalized", 0), "number_of_normalized_files": counts.get("files_normalized", 0), "number_of_success_files": counts.get("files_analyzed", 0), "number_of_error_files": counts.get("errors", 0), "number_of_excluded_files": counts.get("excluded", 0), "configuration_files_used": ["analysis_config.yaml", "classification_rules.yaml", "plot_style_origin.yaml"], "warnings": warnings, "errors": errors, "excel_export_status": counts.get("excel_status", ""), "report_export_status": counts.get("report_status", ""), "figure_export_status": counts.get("figure_status", "")}
    path.write_text(json.dumps(text, ensure_ascii=False, indent=2), encoding="utf-8")
    audit.append(audit_row(run_id, path, "create", True, "ok", "run log"))


def validate_outputs(run_dir: Path) -> list[str]:
    required = ["normalized_waveform/format_detection_summary.csv", "single_waveform/single_waveform_features.csv", "single_waveform/single_waveform_labels.csv", "group_summary/group_statistics.csv", "group_summary/group_quality_summary.csv", "template/template_selection.csv", "template/template_candidates.csv", "template/selected_template_waveform.csv", "template/template_overlay_check.png", "excel_report/waveform_analysis_summary.xlsx", "logs/run.log", "logs/error_files.csv", "logs/excluded_files.csv", "logs/write_audit.csv", "logs/script_reuse_audit.csv"]
    return [p for p in required if not (run_dir / p).exists()]


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    start_time = now_text()
    run_id, run_dir = create_run_dir(smoke=args.smoke)
    ensure_run_dirs(run_dir)
    audit, warnings, error_rows, excluded_rows = [], [], [], []
    configs = {name: read_yaml(CONFIG_DIR / name) for name in ["analysis_config.yaml", "classification_rules.yaml", "plot_style_origin.yaml"]}
    raw_files = scan_raw_files(args.max_files)
    sample_index, metadata_errors = update_sample_index(raw_files, run_id, audit)
    error_rows.extend(metadata_errors)
    group_def = read_table_flexible(METADATA_DIR / "group_definition.csv")
    config_rows = copy_config_snapshot(run_dir, run_id, configs, audit)
    write_csv(run_dir / "config_snapshot" / "config_snapshot.csv", config_rows, ["run_id", "config_item", "config_value", "source_file", "description"], audit, run_id, "config snapshot table")
    script_rows = script_reuse_audit(run_dir, run_id, audit)
    write_csv(run_dir / "logs" / "script_reuse_audit.csv", script_rows, SCRIPT_AUDIT_FIELDS, audit, run_id, "script reuse audit")
    group_ids_defined = set(group_def["group_id"].astype(str)) if not group_def.empty and "group_id" in group_def.columns else set()
    format_rows, features, labels, arrays_by_file, seen_file_ids = [], [], [], {}, set()
    for raw in raw_files:
        try:
            meta = parse_filename(raw)
            if meta["file_id"] in seen_file_ids:
                suffix = 1
                base_id = meta["file_id"]
                while f"{base_id}_dup{suffix:02d}" in seen_file_ids:
                    suffix += 1
                meta["file_id"] = f"{base_id}_dup{suffix:02d}"
            seen_file_ids.add(meta["file_id"])
            main_warning = "none"
            if folder_conflict(raw, meta):
                main_warning = "metadata_conflict"
                warnings.append(f"metadata_conflict: folder and filename mismatch for {raw.name}")
            if group_ids_defined and meta["group_id"] not in group_ids_defined:
                main_warning = "undefined_group"
                warnings.append(f"undefined_group: {meta['group_id']}")
            detection = detect_waveform_format(raw)
            waveform = load_waveform(raw, detection, configs["analysis_config.yaml"])
            normalized = save_normalized(waveform, meta["file_id"], run_dir, audit, run_id)
            public_metadata = metadata_for_tables(waveform.metadata)
            format_rows.append({"run_id": run_id, "file_id": meta["file_id"], "file_name": raw.name, "file_path": relpath(raw), **detection, "parse_status": "success", **public_metadata, "error_message": "", "suggested_action": ""})
            base = {"run_id": run_id, "file_id": meta["file_id"], "file_name": raw.name, "file_path": relpath(raw), "normalized_file_path": relpath(normalized), "detected_format": detection["detected_format"], "loader_used": detection["loader_used"], "experiment_id": meta["experiment_id"], "date": meta["date"], "group_id": meta["group_id"], "config_group": meta["config_group"], "distance_m": meta["distance_m"], "load_condition": meta["load_condition"], "ground_condition": meta["ground_condition"], "block_id": meta["block_id"], "sample_index": meta["sample_index"], **public_metadata}
            feature, arrays = extract_features(waveform, base, configs["analysis_config.yaml"])
            if main_warning != "none":
                feature["main_warning_flag"] = main_warning
                if feature["analysis_status"] == "success":
                    feature["analysis_status"] = main_warning
            features.append(feature)
            arrays_by_file[meta["file_id"]] = arrays
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            error_rows.append(error_row(run_id, raw, "waveform_format_parse_failed", msg, "load_or_feature", "Check file format and filename metadata."))
            try:
                meta = parse_filename(raw)
                file_id = meta["file_id"]
            except Exception:
                file_id = raw.stem
            detection = detect_waveform_format(raw)
            format_rows.append({"run_id": run_id, "file_id": file_id, "file_name": raw.name, "file_path": relpath(raw), **detection, "parse_status": "error", "time_column_mode": "unknown", "voltage_column_mode": "unknown", "start_time_s": np.nan, "time_increment_s": np.nan, "sampling_rate_Hz": np.nan, "record_length": 0, "error_message": msg, "suggested_action": "Check file format and parser support."})
    apply_fsrc(features, configs["analysis_config.yaml"])
    template_selection, template_candidates = write_template_outputs(features, arrays_by_file, sample_index, run_dir, run_id, configs["analysis_config.yaml"], audit)
    write_csv(run_dir / "template" / "template_selection.csv", template_selection, TEMPLATE_SELECTION_FIELDS, audit, run_id, "template selection table")
    write_csv(run_dir / "template" / "template_candidates.csv", template_candidates, TEMPLATE_CANDIDATE_FIELDS, audit, run_id, "template candidate table")
    if template_selection:
        selection = template_selection[0]
        warnings.append(f"template_selected: {selection.get('selected_template_file_id', '')}; status={selection.get('status', '')}; warning={selection.get('warning_flag', '')}")
        for key in ["template_mode", "reference_group", "fallback_level", "template_confidence", "template_method", "candidate_N", "selected_template_file_id", "fsrc_MHz", "alpha_src", "template_time_figure_path", "template_frequency_figure_path", "fallback_used", "fallback_reason", "warning_flag", "status"]:
            config_rows.append({"run_id": run_id, "config_item": f"template_selection.{key}", "config_value": selection.get(key, ""), "source_file": "template_selection.csv", "description": "template selection result"})
        write_csv(run_dir / "config_snapshot" / "config_snapshot.csv", config_rows, ["run_id", "config_item", "config_value", "source_file", "description"], audit, run_id, "config snapshot table with template selection")
    time_display_start_us = estimate_time_display_start_us(features, arrays_by_file)
    warnings.append(f"time_display_start_us: {time_display_start_us:g} (estimated from non-G2 decay-entry markers)")
    config_rows.append({"run_id": run_id, "config_item": "plot.time_display_start_us", "config_value": time_display_start_us, "source_file": "03_scripts/run_all.py", "description": "time-domain figure x-axis start estimated from non-G2 data"})
    write_csv(run_dir / "config_snapshot" / "config_snapshot.csv", config_rows, ["run_id", "config_item", "config_value", "source_file", "description"], audit, run_id, "config snapshot table with time display start")
    for feature in features:
        cls = classify_waveform(feature, configs["classification_rules.yaml"])
        for k, v in cls.items():
            if v is not None:
                feature[k] = v
        feature.update(plot_single(feature, arrays_by_file[feature["file_id"]], run_dir, audit, run_id, configs["plot_style_origin.yaml"], time_display_start_us))
        labels.append({field: feature.get(field, np.nan) for field in LABEL_FIELDS})
        if feature.get("pass_flag") != 1:
            excluded_rows.append({"run_id": run_id, "file_name": feature["file_name"], "file_path": feature["file_path"], "exclude_reason": feature.get("reject_reason", ""), "excluded_by": "algorithm", "exclude_time": now_text(), "original_quality_label": feature.get("quality_label", ""), "manual_note": ""})
    distance_comparison_rows = generate_distance_s001_comparisons(features, arrays_by_file, run_dir, audit, run_id, configs["plot_style_origin.yaml"])
    config_comparison_rows = generate_config_min_distance_s001_comparisons(features, arrays_by_file, run_dir, audit, run_id, configs["plot_style_origin.yaml"])
    config_same_distance_rows = generate_config_same_distance_s001_comparisons(features, arrays_by_file, run_dir, audit, run_id, configs["plot_style_origin.yaml"])
    write_csv(run_dir / "group_summary" / "distance_S001_comparison" / "distance_S001_comparison_index.csv", distance_comparison_rows, DISTANCE_S001_COMPARISON_FIELDS, audit, run_id, "distance S001 comparison index")
    write_csv(run_dir / "group_summary" / "config_min_distance_S001_comparison" / "config_min_distance_S001_comparison_index.csv", config_comparison_rows, CONFIG_MIN_DISTANCE_COMPARISON_FIELDS, audit, run_id, "config min distance S001 comparison index")
    write_csv(run_dir / "group_summary" / "config_same_distance_S001_comparison" / "config_same_distance_S001_comparison_index.csv", config_same_distance_rows, CONFIG_SAME_DISTANCE_COMPARISON_FIELDS, audit, run_id, "config same distance S001 comparison index")
    group_stats, group_quality = summarize_groups(features, labels, group_def, arrays_by_file, run_dir, audit, run_id, configs["plot_style_origin.yaml"], time_display_start_us)
    write_csv(run_dir / "normalized_waveform" / "format_detection_summary.csv", format_rows, FORMAT_FIELDS, audit, run_id)
    write_csv(run_dir / "single_waveform" / "single_waveform_features.csv", features, FEATURE_FIELDS, audit, run_id)
    write_csv(run_dir / "single_waveform" / "single_waveform_labels.csv", labels, LABEL_FIELDS, audit, run_id)
    write_csv(run_dir / "group_summary" / "group_statistics.csv", group_stats, GROUP_STAT_FIELDS, audit, run_id)
    write_csv(run_dir / "group_summary" / "group_quality_summary.csv", group_quality, GROUP_QUALITY_FIELDS, audit, run_id)
    write_csv(run_dir / "logs" / "error_files.csv", error_rows, ERROR_FIELDS, audit, run_id)
    write_csv(run_dir / "logs" / "excluded_files.csv", excluded_rows, EXCLUDED_FIELDS, audit, run_id)
    counts = {"raw_files_found": len(raw_files), "files_normalized": int(sum(1 for r in format_rows if r.get("parse_status") == "success")), "files_analyzed": int(len(features)), "errors": int(len(error_rows)), "excluded": int(len(excluded_rows)), "figure_status": "ok"}
    try:
        excel_path = export_excel(run_dir, run_id, sample_index, audit)
        counts["excel_status"] = "ok"
    except Exception as exc:
        excel_path = ""
        counts["excel_status"] = f"failed: {exc}"
        error_rows.append(error_row(run_id, run_dir, "excel_export_failed", str(exc), "excel_export", "Inspect CSV tables and openpyxl availability."))
    try:
        report_md, report_pdf = export_report(run_dir, run_id, counts, audit)
        counts["report_status"] = "ok"
    except Exception as exc:
        report_md, report_pdf = "", ""
        counts["report_status"] = f"failed: {exc}"
    write_run_log(run_dir, run_id, start_time, now_text(), counts, warnings, error_rows, audit, args.smoke)
    write_csv(run_dir / "logs" / "write_audit.csv", audit, WRITE_AUDIT_FIELDS, None, run_id, "write audit")
    missing = validate_outputs(run_dir)
    return {"run_id": run_id, "run_dir": str(run_dir), "counts": counts, "excel_report": excel_path, "run_log": relpath(run_dir / "logs" / "run.log"), "blocking_issues": missing, "report_md": report_md, "report_pdf": report_pdf}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ML01 waveform analysis pipeline.")
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--quicklook", action="store_true")
    parser.add_argument("--no-pdf-report", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test on a small subset.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.smoke and args.max_files is None:
        args.max_files = 1
    try:
        result = run_pipeline(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result["blocking_issues"] else 2
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
