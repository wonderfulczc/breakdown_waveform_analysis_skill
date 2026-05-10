from __future__ import annotations

from pathlib import Path

from run_all import CONFIG_DIR, detect_waveform_format, load_waveform, read_yaml


def load(path: str | Path):
    cfg = read_yaml(CONFIG_DIR / "analysis_config.yaml")
    detection = detect_waveform_format(Path(path))
    return load_waveform(Path(path), detection, cfg)
