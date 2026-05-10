---
name: ml01-breakdown-waveform-analysis
description: Run the frozen ML01-breakdown-waveform-analysis pipeline for renamed breakdown waveform CSV folders. Use when the user says ML01, ML01波形分析, breakdown waveform analysis, 击穿波形处理, or asks to process ML01 CSV waveform data into normalized tables, single/group figures, template outputs, Excel reports, logs, or extra comparison plots.
---

# ML01 Breakdown Waveform Analysis

Use this skill to run the frozen `breakdown_waveform_analysis` pipeline on a user-provided folder of renamed ML01 waveform CSV files.

## Default Workflow

1. Ask for a waveform folder only if the user did not provide one.
2. Run `scripts/run_ml01_breakdown_analysis.py <waveform_folder>`.
3. The script creates a sibling result folder named `<YYYYMMDD>_<waveform_folder_name>_results`.
4. The script copies the bundled frozen pipeline into an isolated temporary workspace, copies CSV inputs into `00_raw_csv/`, runs smoke test, deletes smoke results, runs the full pipeline, and copies the final `04_results/run_*` into the sibling result folder.
5. Report the final run folder, Excel report, run log, template status, errors, and excluded count.

Do not modify source CSV files. Do not edit bundled rules, docs, prompts, or scripts unless the user explicitly asks to update the skill itself.

## Input Requirements

CSV files must already follow the ML01 filename pattern used by the frozen pipeline, for example:

```text
20260506_ML01_G1_D0p3m_L1Mohm_Glong_B01_S001.csv
```

The skill uses its bundled fixed `group_definition.csv`. Do not require a project directory from the user.

## Output Layout

For input folder:

```text
D:\data\waveforms
```

write outputs to:

```text
D:\data\<YYYYMMDD>_waveforms_results\run_YYYYMMDD_HHMM\
```

## Extra Figures

When the user asks for extra comparison plots after a run, use:

```bash
python scripts/make_extra_comparison.py --run-dir <run_dir> --mode waveform-pair --file-id-a <file_id_a> --file-id-b <file_id_b>
python scripts/make_extra_comparison.py --run-dir <run_dir> --mode template-vs-waveform --file-id-a <file_id>
```

Outputs are written to:

```text
<run_dir>/extra_figures/
```

Use this for requests such as comparing A and B waveforms, comparing a selected waveform with the template, or drawing ad hoc comparison figures. If the template is missing, report that template-vs-waveform cannot be generated from the current run.

## Frozen Pipeline Notes

The bundled pipeline fixes the reference source group as:

```text
G3_D0p3m_L1Mohm_Gcoax
```

If this group is absent, `fsrc`, `alpha_src`, and template correlation remain empty and no fallback template is generated.
