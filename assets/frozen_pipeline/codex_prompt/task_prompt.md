# Task Prompt for Codex

You are inside the local project:

```text
breakdown_waveform_analysis/
```

Your task is to implement the ML01 waveform analysis pipeline according to the project rules and documentation.

Before doing anything, read:

```text
05_docs/README.md
05_docs/file_naming_rule.md
05_docs/parameter_definition.md
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
codex_prompt/project_rules.md
```

Follow those files strictly.

Do not modify raw waveform files.

---

## Execution Mode for This Task

Use the following execution mode unless the user explicitly says otherwise:

```text
run_mode
```

This means:

1. First check whether `03_scripts/` already contains all required scripts.
2. If all required scripts exist, run smoke test using the existing scripts.
3. If smoke test passes, do not modify scripts.
4. Directly process the current waveform files in `00_raw_csv/`.
5. Write all outputs to a new `04_results/run_YYYYMMDD_HHMM/` folder.
6. Generate `logs/script_reuse_audit.csv`.

Only switch to `build_mode` if:

```text
a required script is missing
or smoke test fails
or required outputs cannot be generated
or the user explicitly asks you to modify scripts
```

In `run_mode`, do not rewrite, refactor, rename, delete, or regenerate scripts.

---

## Permission Check Before Work

Before writing any file, read and obey the permission matrix in:

```text
codex_prompt/project_rules.md
```

You may write only to:

```text
03_scripts/
01_metadata/sample_index.csv
01_metadata/sample_index.xlsx
04_results/run_YYYYMMDD_HHMM/
```

You must treat these as read-only:

```text
00_raw_csv/
01_metadata/group_definition.csv
02_config/
05_docs/
codex_prompt/
```

Before each write operation, verify that the target path and file type are allowed.

At the end of the run, generate:

```text
04_results/run_YYYYMMDD_HHMM/logs/write_audit.csv
```

listing every created or updated file.

---

## 1. Immediate Goal

Create a complete, runnable Python pipeline that:

1. Detects real waveform file formats.
2. Loads raw waveform files from `00_raw_csv/`.
3. Converts each valid waveform to normalized CSV with `time_s, voltage_V`.
4. Extracts single-waveform features.
5. Classifies waveforms into A/B/C/D/E/F/G/H/unknown.
6. Generates Science Robotics style figures.
7. Computes group statistics.
8. Exports CSV tables.
9. Exports one Excel summary workbook.
10. Writes logs and error tables.
11. Generates a quick Markdown report.

---

## 2. Required Implementation Files

Create or update these scripts in:

```text
03_scripts/
```

Required scripts:

```text
run_all.py
detect_waveform_format.py
load_waveform.py
normalize_waveform.py
read_waveform.py
preprocess.py
extract_features.py
classify_waveform.py
plot_waveform.py
summarize_group.py
export_report.py
```

Also create:

```text
requirements.txt
```

with the required Python dependencies.

Use only common Python packages unless necessary:

```text
numpy
pandas
scipy
matplotlib
openpyxl
pyyaml
```

If `.xls` or OLE binary files need support, attempt available engines safely. If the required package is unavailable, record the failure in `error_files.csv` and continue.

---

## 3. Pipeline Entry Point

The main entry point must be:

```text
03_scripts/run_all.py
```

It should be runnable from the project root:

```bash
python 03_scripts/run_all.py
```

Optional arguments are allowed:

```bash
python 03_scripts/run_all.py --max-files 10
python 03_scripts/run_all.py --quicklook
python 03_scripts/run_all.py --no-pdf-report
```

But default execution must run the full available pipeline.

---

## 4. Required Data Flow

Use this fixed data flow:

```text
00_raw_csv/
01_metadata/
02_config/
05_docs/
        ↓
format detection
        ↓
normalized waveform generation
        ↓
feature extraction
        ↓
classification
        ↓
group statistics
        ↓
figures
        ↓
CSV tables
        ↓
Excel workbook
        ↓
quick report
```

Downstream analysis must use:

```text
04_results/run_*/normalized_waveform/normalized_csv/
```

not raw waveform files.

---

## 5. Run Folder

Create a new run folder:

```text
04_results/run_YYYYMMDD_HHMM/
```

If it already exists, append a counter:

```text
run_YYYYMMDD_HHMM_01
run_YYYYMMDD_HHMM_02
```

Do not overwrite old run folders.

---

## 6. Waveform Format Detection

Implement `detect_waveform_format.py`.

It must detect at least:

```text
true_text_csv
oscilloscope_sequence_volt_csv
csv_with_preamble
excel_xlsx
excel_xls_or_ole_binary
mislabeled_excel_binary_with_csv_extension
unknown_binary
```

Detection methods should include:

```text
file signature
file extension
first 20 lines
delimiter pattern
header keywords
sheet structure
```

For OLE binary files, detect signatures such as:

```text
D0 CF 11 E0 A1 B1 1A E1
```

Do not treat file extension alone as truth.

---

## 7. Waveform Loading

Implement `load_waveform.py`.

It must load and return a standard in-memory representation:

```text
time_s
voltage_V
metadata
```

Supported cases:

### Case 1: True text CSV with time and voltage columns

Detect time and voltage columns using config candidates.

Convert time to seconds.

Convert voltage to volts.

### Case 2: Oscilloscope Sequence-Volt-Start-Increment format

Expected structure:

```text
Row 0: X, CH1, Start, Increment
Row 1: Sequence, Volt, start_s, increment_s
Row 2+: sequence_index, voltage
```

Use:

```text
time_s = start_s + sequence_index × increment_s
voltage_V = voltage
sampling_rate_Hz = 1 / increment_s
```

### Case 3: CSV with preamble

Find the first numerical table.

Detect or infer time and voltage columns.

If time cannot be safely determined, write error.

### Case 4: Excel `.xlsx`

Read the first sheet unless config says otherwise.

Detect the same structures as above.

### Case 5: Excel/OLE binary or mislabeled `.csv`

Try safe Excel reading.

If unavailable or unreadable, write error and continue.

---

## 8. Normalized Waveform Output

Implement `normalize_waveform.py`.

For every successfully parsed file, write:

```text
04_results/run_*/normalized_waveform/normalized_csv/{file_id}_normalized.csv
```

Required columns:

```text
time_s,voltage_V
```

Optional metadata columns are allowed only if they do not disrupt downstream reading.

Also write:

```text
04_results/run_*/normalized_waveform/format_detection_summary.csv
```

Required fields:

```text
run_id,file_id,file_name,file_path,file_extension,detected_format,loader_used,parse_status,time_column_mode,voltage_column_mode,start_time_s,time_increment_s,sampling_rate_Hz,record_length,error_message,suggested_action
```

---

## 9. Metadata Handling

Create or update:

```text
01_metadata/sample_index.csv
01_metadata/sample_index.xlsx
```

Use fields defined in:

```text
05_docs/parameter_definition.md
```

Do not overwrite user notes.

If `manual_note` exists, preserve it.

If `included` exists, preserve it.

If absent, default:

```text
included = 1
```

Read group definitions from:

```text
01_metadata/group_definition.csv
```

If a parsed `group_id` is absent from `group_definition.csv`, mark:

```text
main_warning_flag = undefined_group
```

---

## 10. Feature Extraction

Implement `extract_features.py`.

Extract at minimum:

```text
Apk
Amin
App
t_Apk_s
f1_MHz
A1
f2_MHz
A2
PSR_dB
narrowband_SNR_dB
alpha
rho
fit_R2
burst_start_s
burst_end_s
fsrc_MHz
A_fsrc
f1_to_fsrc_diff_percent
fsrc_trackable
num_bursts
envelope_monotonic
overdrive_recovery_flag
aliasing_flag
echo_flag
```

Use:

```text
02_config/analysis_config.yaml
```

for all processing parameters.

Key requirements:

1. Apply baseline correction if enabled.
2. Detect main burst.
3. Compute FFT from analysis window.
4. Extract f1 and f2 using configured bands.
5. Compute PSR.
6. Compute narrowband SNR.
7. Fit damped sine if enabled.
8. Build or load template for rho.
9. Track fsrc if enabled.
10. Do not fail entire batch if one feature fails.

If fitting fails, set:

```text
alpha = NaN
fit_R2 = NaN
analysis_status = fit_failed
main_warning_flag = fit_failed
```

---

## 11. Classification

Implement `classify_waveform.py`.

Use only:

```text
02_config/classification_rules.yaml
```

to assign:

```text
waveform_class
quality_label
pass_flag
reject_reason
main_warning_flag
classification_rule_version
analysis_status
```

Do not invent new A-H meanings.

Read/parse failure should be handled according to the YAML.

Project-book class G means clipped/saturated/aliased waveform, not file read failure.

---

## 12. Figures

Implement `plot_waveform.py`.

Use:

```text
02_config/plot_style_origin.yaml
```

Generate:

```text
single_waveform/figures_time_domain/
single_waveform/figures_frequency_domain/
single_waveform/figures_fit/
group_summary/overlay_time_domain/
group_summary/overlay_frequency_domain/
group_summary/statistics_figures/
```

Use figure formats:

```text
png
```

Publication style must follow:

```text
white background
sans-serif font
boxed axes for quantitative plots
thin black axes
uppercase panel labels
no internal plot titles
no final grid
Science Robotics style palette
```

For single waveform frequency figures, mark:

```text
f1
f2
fsrc
```

if available.

For time-domain figures, mark:

```text
Apk
analysis window
waveform_class
quality_label
```

if available.

### Extra S001 Comparison Plots

For this run, generate two extra comparison plot types.

#### Type 1: Same Config, Multiple Distances

Group by:

```text
date + config_group + load_condition + ground_condition
```

Within each group:

1. find waveforms with `sample_index = S001`
2. select one waveform per distance
3. prefer `B01`
4. if multiple candidates remain, select the smallest `block_id`
5. if still tied, select the lexicographically smallest file name

If at least 2 distances are available, generate one time-domain overlay plot using peak-time alignment and one frequency-domain overlay plot.

Legend labels must use the complete waveform `file_id` without date.

Save outputs to:

```text
group_summary/distance_S001_comparison/
```

and record them in:

```text
group_summary/distance_S001_comparison/distance_S001_comparison_index.csv
```

#### Type 2: Multiple Configs, Minimum Available Distance

Group by:

```text
date + load_condition + ground_condition
```

Within each group:

1. for each `config_group`, find waveforms with `sample_index = S001`
2. choose the minimum available distance using priority:

```text
0.1m -> 0.3m -> 0.6m -> 0.8m
```

3. within the chosen distance, prefer `B01`
4. if multiple candidates remain, select the smallest `block_id`
5. if still tied, select the lexicographically smallest file name

If at least 2 config groups are available, generate one time-domain overlay plot using peak-time alignment and one frequency-domain overlay plot.

Legend labels must use the complete waveform `file_id` without date.

Save outputs to:

```text
group_summary/config_min_distance_S001_comparison/
```

and record them in:

```text
group_summary/config_min_distance_S001_comparison/config_min_distance_S001_comparison_index.csv
```

#### Type 3: Multiple Configs, Same Distance

Group by:

```text
date + distance_m
```

Within each group:

1. for each `config_group`, find waveforms with `sample_index = S001`
2. use only files at the same `distance_m`
3. prefer `B01`
4. if multiple candidates remain, select the smallest `block_id`
5. if still tied, select the lexicographically smallest file name

If at least 2 config groups are available at the same distance, generate one time-domain overlay plot using peak-time alignment and one frequency-domain overlay plot.

Legend labels must use the complete waveform `file_id` without date.

Save outputs to:

```text
group_summary/config_same_distance_S001_comparison/
```

and record them in:

```text
group_summary/config_same_distance_S001_comparison/config_same_distance_S001_comparison_index.csv
```

---

## 13. Output Tables

Generate these tables with fields from `parameter_definition.md`:

```text
04_results/run_*/single_waveform/single_waveform_features.csv
04_results/run_*/single_waveform/single_waveform_labels.csv
04_results/run_*/group_summary/group_statistics.csv
04_results/run_*/group_summary/group_quality_summary.csv
04_results/run_*/config_snapshot/config_snapshot.csv
04_results/run_*/logs/error_files.csv
04_results/run_*/logs/excluded_files.csv
```

CSV tables are primary.

Excel is secondary.

Do not skip CSV generation.

---

## 14. Group Statistics

Implement `summarize_group.py`.

Group by:

```text
group_id
```

Compute:

```text
median
IQR = Q3 - Q1
CV_percent = sample_std / mean × 100
quality ratios
class counts
dominant waveform class
group_decision
```

Use formal inclusion rules from:

```text
02_config/classification_rules.yaml
```

Use fields and definitions from:

```text
05_docs/parameter_definition.md
```

---

## 15. Excel and Report

Implement `export_report.py`.

Generate:

```text
04_results/run_*/excel_report/waveform_analysis_summary.xlsx
```

The workbook must include sheets:

```text
README
sample_index
format_detection_summary
single_waveform_features
single_waveform_labels
group_statistics
group_quality_summary
error_files
excluded_files
config_snapshot
```

Also generate:

```text
04_results/run_*/report/quick_report.md
```

Generate PDF if supported:

```text
04_results/run_*/report/quick_report.pdf
```

If PDF export is unsupported, skip it, log warning, and continue.

---

## 16. Config Snapshot

Copy:

```text
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
```

to:

```text
04_results/run_*/config_snapshot/
```

as:

```text
analysis_config_used.yaml
classification_rules_used.yaml
plot_style_origin_used.yaml
```

Generate:

```text
config_snapshot.csv
```

with key configuration values.

---

## 17. Logs

Generate:

```text
04_results/run_*/logs/run.log
04_results/run_*/logs/error_files.csv
04_results/run_*/logs/excluded_files.csv
```

Log at minimum:

```text
run_id
start_time
end_time
Python version
package versions
raw files found
files normalized
files analyzed
files failed
files excluded
config files used
warnings
errors
Excel export status
figure export status
```

---

## 18. Smoke Test First

Before full processing, run a smoke test.

The smoke test should:

1. Parse YAML files.
2. Read `group_definition.csv`.
3. Scan `00_raw_csv/`.
4. Detect waveform formats.
5. Normalize at least one waveform if available.
6. Extract features for at least one waveform if available.
7. Generate at least one time-domain figure.
8. Generate at least one frequency-domain figure.
9. Generate required output tables.
10. Generate run log.

If no real waveform files exist, create a temporary synthetic damped sine test only under:

```text
04_results/run_*/logs/test_artifacts/
```

Do not place synthetic data in `00_raw_csv/`.

Do not include synthetic data in final ML01 result tables.

---

## 19. Validation Checklist

After running, verify:

```text
00_raw_csv/ was not modified
new run folder exists
normalized_waveform/ exists
format_detection_summary.csv exists
single_waveform_features.csv exists
single_waveform_labels.csv exists
group_statistics.csv exists
group_quality_summary.csv exists
waveform_analysis_summary.xlsx exists
run.log exists
error_files.csv exists
```

Verify required columns exist.

Verify figure files exist for successfully analyzed files.

Verify Excel sheets are generated from CSV tables.

---

## 20. Final Codex Response

After completing the task, reply with a concise summary:

```text
Created/updated scripts:
Run folder:
Raw files found:
Files normalized:
Files analyzed:
Errors:
Excluded:
Excel report:
Run log:
Blocking issues:
```

Do not provide long scientific interpretation.

Do not claim results are physically valid before user inspection.

Only report execution status and file locations.

## 21. Initial Waveform Domain Check

Before normal feature extraction, detect the input data domain for every waveform file.

Classify each file as:

```text
time_domain
frequency_domain_magnitude
frequency_domain_complex
unknown
````

Then use the correct processing direction:

```text
time_domain -> FFT from time to frequency
frequency_domain_magnitude -> use frequency data directly
frequency_domain_complex -> IFFT only if complete complex spectrum exists
unknown -> write error and continue
```

For each successfully parsed waveform, generate:

```text
normalized_waveform/normalized_csv/{file_id}_normalized.csv
normalized_waveform/normalized_csv/{file_id}_normalized.xlsx
```

The XLSX workbook must contain:

```text
time_domain
frequency_domain
processing_info
```

Do not perform inverse FFT from magnitude-only spectrum.

````

## 22. f1/f2 Independent Peak Requirement

When extracting spectral peaks, do not choose f1 and f2 from small fluctuations within the same broad peak.

First detect independent peak clusters.

Use:

```text
f1 = highest-amplitude independent clear peak
f2 = second-highest-amplitude independent clear peak excluding f1
fdom = highest-amplitude independent peak
````

If two local maxima are within the same peak cluster, keep only the cluster representative and do not label the other as f2.

Use valley depth, frequency separation, and peak width to decide whether two local maxima are independent.

Record:

```text
f1_MHz
A1
f2_MHz
A2
fdom_MHz
Adom
independent_peak_count
shoulder_peak_flag
```

````

---
