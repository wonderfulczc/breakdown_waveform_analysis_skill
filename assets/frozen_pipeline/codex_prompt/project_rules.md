# Project Rules for Codex

You are working inside the local project:

```text
breakdown_waveform_analysis/
```

This project processes waveform files from ML01:

```text
ML01 = 实验一，测量链排伪影与接收端影响核查
```

Your job is to create and maintain a reproducible Python waveform analysis pipeline.

You must follow all rules in this file and in:

```text
05_docs/README.md
05_docs/file_naming_rule.md
05_docs/parameter_definition.md
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
```

Do not invent new project structure, file naming rules, table fields, or classification rules unless explicitly required by the existing documents.

---

## File System Permission Matrix

Codex must obey the following file-system permission matrix.

### Permission Levels

| Permission | Meaning |
|---|---|
| `read_only` | Codex may read files, but must not modify, rename, delete, move, or overwrite them. |
| `write_allowed` | Codex may create or update files only according to the allowed content type. |
| `create_only` | Codex may create new files or folders, but must not overwrite existing files unless explicitly allowed. |
| `generated_only` | Codex may write only generated outputs from the current run. |
| `forbidden` | Codex must not read or write unless explicitly instructed by the user. |

---

### Directory Permission Matrix

| Path | Permission | Allowed Content | Forbidden Actions |
|---|---|---|---|
| `00_raw_csv/` | `read_only` | Raw waveform files only | modify, rename, delete, move, overwrite, write result files |
| `01_metadata/group_definition.csv` | `read_only` | User-defined group table | overwrite, reorder columns, delete rows |
| `01_metadata/sample_index.csv` | `write_allowed` | Sample index table | overwrite user-filled `manual_note`, overwrite user-edited `included` |
| `01_metadata/sample_index.xlsx` | `write_allowed` | Excel view of sample index | overwrite without regenerating from `sample_index.csv` |
| `02_config/analysis_config.yaml` | `read_only` | Analysis configuration | modify, overwrite, delete |
| `02_config/classification_rules.yaml` | `read_only` | Classification rules | modify, overwrite, delete |
| `02_config/plot_style_origin.yaml` | `read_only` | Plot style configuration | modify, overwrite, delete |
| `03_scripts/` | `write_allowed` | Python scripts only | write raw data, write results, write large binary files |
| `04_results/` | `create_only` | New run folders only | overwrite old run folders |
| `04_results/run_*/normalized_waveform/` | `generated_only` | Normalized waveform CSV and format detection table | write raw waveform originals |
| `04_results/run_*/single_waveform/` | `generated_only` | Single-waveform figures and tables | write config source files |
| `04_results/run_*/group_summary/` | `generated_only` | Group-level figures and tables | write raw files |
| `04_results/run_*/config_snapshot/` | `generated_only` | Copies of config files and config snapshot table | modify source config files |
| `04_results/run_*/excel_report/` | `generated_only` | One Excel summary workbook | store raw waveform data |
| `04_results/run_*/logs/` | `generated_only` | Logs, error files, excluded files | delete existing logs during same run |
| `04_results/run_*/report/` | `generated_only` | Quick report markdown/PDF | store raw waveform data |
| `05_docs/` | `read_only` | Project documentation | modify, overwrite, delete |
| `codex_prompt/` | `read_only` | Prompt files and project rules | modify, overwrite, delete |
| other paths outside project root | `forbidden` | none | read, write, scan, delete |

---

### Allowed Write Targets

Codex may write only to the following locations:

```text
03_scripts/
01_metadata/sample_index.csv
01_metadata/sample_index.xlsx
04_results/run_YYYYMMDD_HHMM/
```

Codex must not write to any other location.

---

### Allowed File Types by Directory

| Directory | Allowed File Types |
|---|---|
| `03_scripts/` | `.py`, `.txt` for script notes only |
| `01_metadata/` | `.csv`, `.xlsx` |
| `04_results/run_*/normalized_waveform/normalized_csv/` | `.csv` |
| `04_results/run_*/normalized_waveform/` | `.csv` |
| `04_results/run_*/single_waveform/figures_time_domain/` | `.png` |
| `04_results/run_*/single_waveform/figures_frequency_domain/` | `.png` |
| `04_results/run_*/single_waveform/figures_fit/` | `.png` |
| `04_results/run_*/single_waveform/` | `.csv` |
| `04_results/run_*/group_summary/overlay_time_domain/` | `.png` |
| `04_results/run_*/group_summary/overlay_frequency_domain/` | `.png` |
| `04_results/run_*/group_summary/statistics_figures/` | `.png` |
| `04_results/run_*/group_summary/distance_S001_comparison/` | `.csv`, `.png` |
| `04_results/run_*/group_summary/config_min_distance_S001_comparison/` | `.csv`, `.png` |
| `04_results/run_*/group_summary/config_same_distance_S001_comparison/` | `.csv`, `.png` |
| `04_results/run_*/group_summary/` | `.csv` |
| `04_results/run_*/template/` | `.csv`, `.png` |
| `04_results/run_*/config_snapshot/` | `.yaml`, `.csv` |
| `04_results/run_*/excel_report/` | `.xlsx` |
| `04_results/run_*/logs/` | `.log`, `.csv`, `.txt` |
| `04_results/run_*/report/` | `.md`, `.pdf` |

If Codex needs to create any other file type, it must stop and report the reason.

---

### Write Protection Rules

Codex must never modify these files:

```text
00_raw_csv/*
01_metadata/group_definition.csv
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
05_docs/*
codex_prompt/*
```

Codex may read these files, but they are read-only.

---

### Raw Data Protection

Raw waveform files are immutable.

Codex must not:

```text
modify raw files
rename raw files
delete raw files
move raw files
convert raw files in place
write normalized data into raw folders
write figures into raw folders
write logs into raw folders
```

All standardized waveform files must be written to:

```text
04_results/run_YYYYMMDD_HHMM/normalized_waveform/normalized_csv/
```

---

### Run Folder Protection

Every analysis run must create a new folder:

```text
04_results/run_YYYYMMDD_HHMM/
```

If the folder already exists, Codex must create:

```text
04_results/run_YYYYMMDD_HHMM_01/
04_results/run_YYYYMMDD_HHMM_02/
```

Codex must never overwrite previous run folders.

---

### User-Edited Metadata Protection

Codex may update:

```text
01_metadata/sample_index.csv
```

But it must preserve user-edited fields:

```text
included
manual_note
notes
```

If these columns already contain values, Codex must not overwrite them.

---

### Config Snapshot Rule

Codex must copy configuration files from:

```text
02_config/
```

to:

```text
04_results/run_YYYYMMDD_HHMM/config_snapshot/
```

as:

```text
analysis_config_used.yaml
classification_rules_used.yaml
plot_style_origin_used.yaml
```

Codex must not modify the source config files.

---

### Write Audit Requirement

At the end of each run, Codex must generate:

```text
04_results/run_YYYYMMDD_HHMM/logs/write_audit.csv
```

with fields:

```text
run_id,path,file_type,operation,allowed_by_rule,status,notes
```

Every created or updated file must be listed.

---

### Violation Handling

If Codex detects that a requested write operation violates this permission matrix, it must:

1. Stop that operation.
2. Write the attempted operation to `logs/run.log`.
3. Add a row to `logs/write_audit.csv`.
4. Continue with allowed operations if possible.
5. Report the violation in the final response.

Codex must not bypass this permission matrix.

---

## Script Reuse and Execution Mode

Codex must distinguish between two modes:

```text
build_mode = create or repair the analysis pipeline
run_mode = reuse the existing pipeline to process new data
```

### Default Mode

If `03_scripts/` already contains the required scripts, Codex must default to:

```text
run_mode
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

### Run Mode Rules

In `run_mode`, Codex must:

1. Reuse existing scripts in `03_scripts/`.
2. Run smoke test using existing scripts.
3. Create a new `04_results/run_YYYYMMDD_HHMM/` folder.
4. Process the current files in `00_raw_csv/`.
5. Generate new outputs only under the new run folder.
6. Preserve all existing scripts unless a blocking error is found.

In `run_mode`, Codex must not:

1. Rewrite existing scripts.
2. Refactor existing scripts.
3. Change script architecture.
4. Rename script files.
5. Delete script files.
6. Modify working scripts just for style or optimization.
7. Regenerate the whole pipeline.

### When Script Modification Is Allowed

Codex may modify files in `03_scripts/` only if at least one condition is met:

1. A required script is missing.
2. A required script fails during smoke test.
3. Existing scripts cannot read the current configuration files.
4. Existing scripts are incompatible with the current `parameter_definition.md`.
5. Existing scripts cannot generate required outputs.
6. The user explicitly requests script modification.

If Codex modifies any script, it must:

1. Explain the reason in `logs/run.log`.
2. Add the modified script path to `logs/write_audit.csv`.
3. Preserve a backup copy under:

```text
04_results/run_YYYYMMDD_HHMM/logs/script_backup/
```

4. Modify only the minimum necessary code.

### Script Reuse Audit

Every run must record script reuse status in:

```text
04_results/run_YYYYMMDD_HHMM/logs/script_reuse_audit.csv
```

Required fields:

```text
run_id,script_name,script_path,exists,reused,modified,modification_reason,backup_path,status
```

### Preferred Behavior

For second and later data processing runs, Codex should normally do only:

```text
read rules
check scripts
run smoke test
create new run folder
process data
export results
write logs
```

Codex should not spend time regenerating scripts if existing scripts pass checks.

---

## 1. Scope

Only process ML01 waveform data.

Do not expand to other experiments.

Do not create new research tasks.

Do not modify the scientific meaning of A/B/C/D/E/F/G/H classes.

Use the classification logic from:

```text
02_config/classification_rules.yaml
```

Use the plotting style from:

```text
02_config/plot_style_origin.yaml
```

Use the field definitions from:

```text
05_docs/parameter_definition.md
```

Use the file naming rule from:

```text
05_docs/file_naming_rule.md
```

---

## 2. Fixed Directory Structure

The expected project structure is:

```text
breakdown_waveform_analysis/
├─ 00_raw_csv/
├─ 01_metadata/
├─ 02_config/
├─ 03_scripts/
├─ 04_results/
├─ 05_docs/
└─ codex_prompt/
```

Raw waveform files are in:

```text
00_raw_csv/
```

User-maintained metadata files are in:

```text
01_metadata/
```

Configuration files are in:

```text
02_config/
```

Python scripts must be created or updated in:

```text
03_scripts/
```

All analysis outputs must be written to a new run folder:

```text
04_results/run_YYYYMMDD_HHMM/
```

Project documentation is in:

```text
05_docs/
```

Prompt files are in:

```text
codex_prompt/
```

---

## 3. Read-Only Raw Data Rule

The following directory is strictly read-only:

```text
00_raw_csv/
```

You must not:

1. Modify raw waveform files.
2. Rename raw waveform files.
3. Delete raw waveform files.
4. Move raw waveform files.
5. Write result files into `00_raw_csv/`.
6. Overwrite any raw waveform file.

If waveform format conversion is needed, write standardized copies to:

```text
04_results/run_YYYYMMDD_HHMM/normalized_waveform/normalized_csv/
```

Never modify the original raw files.

---

## 4. Required Codex Workflow

Before writing or running code, read these files in order:

```text
05_docs/README.md
05_docs/file_naming_rule.md
05_docs/parameter_definition.md
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
codex_prompt/project_rules.md
```

Then perform the workflow:

```text
Step 01: Scan 00_raw_csv/
Step 02: Parse filenames according to file_naming_rule.md
Step 03: Detect the real waveform file format
Step 04: Load waveform files using format-specific loaders
Step 05: Convert each valid waveform to normalized CSV
Step 06: Save normalized waveform files to normalized_waveform/normalized_csv/
Step 07: Save format detection results to normalized_waveform/format_detection_summary.csv
Step 08: Update or create 01_metadata/sample_index.csv
Step 09: Export 01_metadata/sample_index.xlsx
Step 10: Read 01_metadata/group_definition.csv
Step 11: Create a new 04_results/run_YYYYMMDD_HHMM/ folder
Step 12: Copy config files into config_snapshot/
Step 13: Generate config_snapshot.csv
Step 14: Run single-waveform feature extraction
Step 15: Generate time-domain figures
Step 16: Generate frequency-domain figures
Step 17: Generate fitting figures
Step 18: Generate single_waveform_features.csv
Step 19: Generate single_waveform_labels.csv
Step 20: Run group statistics
Step 21: Generate overlay figures
Step 22: Generate statistics figures
Step 23: Generate group_statistics.csv
Step 24: Generate group_quality_summary.csv
Step 25: Generate logs/run.log
Step 26: Generate logs/error_files.csv
Step 27: Generate logs/excluded_files.csv
Step 28: Generate excel_report/waveform_analysis_summary.xlsx
Step 29: Generate report/quick_report.md
Step 30: Generate report/quick_report.pdf if supported
```

---

## 5. Waveform Format Handling

Do not assume all files are true text CSV.

You must detect the real file format before analysis.

Supported input types should include:

```text
true_text_csv
oscilloscope_sequence_volt_csv
csv_with_preamble
excel_xlsx
excel_xls_or_ole_binary
mislabeled_excel_binary_with_csv_extension
unknown_binary
```

For each raw file, produce or record:

```text
detected_format
loader_used
parse_status
time_column_mode
voltage_column_mode
start_time_s
time_increment_s
sampling_rate_Hz
record_length
error_message
suggested_action
```

Write this table to:

```text
04_results/run_YYYYMMDD_HHMM/normalized_waveform/format_detection_summary.csv
```

If a file can be safely parsed, save a normalized waveform file:

```text
04_results/run_YYYYMMDD_HHMM/normalized_waveform/normalized_csv/{file_id}_normalized.csv
```

The normalized CSV must contain at least:

```text
time_s,voltage_V
```

Downstream analysis must use normalized CSV files, not raw files.

If a file cannot be safely parsed, write it to:

```text
04_results/run_YYYYMMDD_HHMM/logs/error_files.csv
```

and continue processing other files.

Do not silently guess waveform format.

---

## 6. Oscilloscope Sequence-Volt Format

Some oscilloscope exports use this structure:

```text
Row 0: X, CH1, Start, Increment
Row 1: Sequence, Volt, start_s, increment_s
Row 2+: sequence_index, voltage
```

For this format:

```text
time_s = start_s + sequence_index × increment_s
voltage_V = Volt
sampling_rate_Hz = 1 / increment_s
```

Do not treat `Sequence` as physical time.

---

## 7. Metadata Rules

Filename parsing has high priority, but `sample_index.csv` may override metadata if manually corrected.

Metadata priority:

```text
sample_index.csv manual correction
filename parsing
folder path
error or warning
```

If filename and metadata conflict:

1. Use `sample_index.csv` as final metadata.
2. Write warning to `logs/run.log`.
3. Mark `main_warning_flag = metadata_conflict`.
4. Continue processing.

If a group is not defined in:

```text
01_metadata/group_definition.csv
```

then mark:

```text
main_warning_flag = undefined_group
```

Do not silently create official groups without logging.

---

## 8. Required Scripts

Create or update scripts in:

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

Script responsibilities:

| Script | Responsibility |
|---|---|
| `run_all.py` | Run the complete pipeline |
| `detect_waveform_format.py` | Detect real file format |
| `load_waveform.py` | Load raw waveform using format-specific loader |
| `normalize_waveform.py` | Write normalized `time_s, voltage_V` CSV |
| `read_waveform.py` | Provide standardized waveform to downstream analysis |
| `preprocess.py` | Baseline correction, burst detection, optional filtering |
| `extract_features.py` | Extract Apk, f1, f2, PSR, SNR, alpha, rho, fsrc fields |
| `classify_waveform.py` | Apply classification_rules.yaml |
| `plot_waveform.py` | Generate Science Robotics style figures |
| `summarize_group.py` | Compute group medians, IQR, CV, ratios |
| `export_report.py` | Export Excel and quick report |

---

## 9. Required Output Structure

Each run must generate:

```text
04_results/run_YYYYMMDD_HHMM/
├─ normalized_waveform/
│  ├─ normalized_csv/
│  └─ format_detection_summary.csv
│
├─ single_waveform/
│  ├─ figures_time_domain/
│  ├─ figures_frequency_domain/
│  ├─ figures_fit/
│  ├─ single_waveform_features.csv
│  └─ single_waveform_labels.csv
│
├─ group_summary/
│  ├─ overlay_time_domain/
│  ├─ overlay_frequency_domain/
│  ├─ statistics_figures/
│  ├─ group_statistics.csv
│  └─ group_quality_summary.csv
│
├─ config_snapshot/
│  ├─ analysis_config_used.yaml
│  ├─ classification_rules_used.yaml
│  ├─ plot_style_origin_used.yaml
│  └─ config_snapshot.csv
│
├─ excel_report/
│  └─ waveform_analysis_summary.xlsx
│
├─ logs/
│  ├─ run.log
│  ├─ error_files.csv
│  └─ excluded_files.csv
│
└─ report/
   ├─ quick_report.md
   └─ quick_report.pdf
```

Do not overwrite old run folders.

If the run folder already exists, append a counter:

```text
run_YYYYMMDD_HHMM_01
run_YYYYMMDD_HHMM_02
```

---

## 10. Required Tables

Use the fields defined in:

```text
05_docs/parameter_definition.md
```

Do not change field names or field order unless explicitly instructed.

Required tables:

```text
01_metadata/sample_index.csv
04_results/run_*/normalized_waveform/format_detection_summary.csv
04_results/run_*/single_waveform/single_waveform_features.csv
04_results/run_*/single_waveform/single_waveform_labels.csv
04_results/run_*/group_summary/group_statistics.csv
04_results/run_*/group_summary/group_quality_summary.csv
04_results/run_*/config_snapshot/config_snapshot.csv
04_results/run_*/logs/error_files.csv
04_results/run_*/logs/excluded_files.csv
```

The Excel workbook:

```text
04_results/run_*/excel_report/waveform_analysis_summary.xlsx
```

must be generated from CSV tables.

CSV is the primary data source.

Excel is only a human-readable summary.

---

## 11. Feature Extraction Requirements

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

for all numeric processing parameters.

Do not hard-code thresholds if they already exist in YAML.

---

## 12. Classification Requirements

Classify each waveform into:

```text
A
B
C
D
E
F
G
H
unknown
```

Use:

```text
02_config/classification_rules.yaml
```

Do not invent new A-H definitions.

Output:

```text
waveform_class
quality_label
pass_flag
reject_reason
main_warning_flag
classification_rule_version
analysis_status
```

Write classification results to both:

```text
single_waveform_features.csv
single_waveform_labels.csv
```

---

## 13. Plotting Requirements

Use:

```text
02_config/plot_style_origin.yaml
```

Figures must follow the Science Robotics style configuration.

Required figure outputs:

```text
single_waveform/figures_time_domain/
single_waveform/figures_frequency_domain/
single_waveform/figures_fit/
group_summary/overlay_time_domain/
group_summary/overlay_frequency_domain/
group_summary/statistics_figures/
```

Export formats:

```text
png
```

For publication-style figures:

```text
dpi = 600
white background
sans-serif font
uppercase panel labels
boxed axes for quantitative plots
thin black axes
no grid
no internal plot titles
```

---

## 14. Group Statistics Requirements

Group by:

```text
group_id
```

Calculate:

```text
f1_median_MHz
f1_IQR_MHz
f1_CV_percent
alpha_median
alpha_IQR
alpha_CV_percent
Apk_median
Apk_IQR
Apk_CV_percent
PSR_median_dB
PSR_IQR_dB
SNR_median_dB
SNR_IQR_dB
rho_median
rho_IQR
fit_R2_median
dominant_waveform_class
excellent_ratio_percent
usable_ratio_percent
suspicious_ratio_percent
unusable_ratio_percent
pass_ratio_percent
group_decision
```

Use inclusion rules from:

```text
02_config/classification_rules.yaml
```

Do not include excluded/unusable waveforms in formal numerical statistics unless the config explicitly says so.

Quality ratios should include all analyzed files unless otherwise configured.

---

## 15. Logging Requirements

Always create:

```text
logs/run.log
logs/error_files.csv
logs/excluded_files.csv
```

`run.log` must include:

```text
run_id
start_time
end_time
Python version
package versions
command line
number of raw input files
number of parsed files
number of normalized files
number of successful feature extractions
number of failed files
number of excluded files
configuration files used
warnings
errors
Excel export status
report export status
```

Single-file failures must not stop the entire batch.

---

## 16. Testing Requirements

Before full analysis, implement and run basic tests:

1. Check project folders exist.
2. Check YAML files can be parsed.
3. Check `group_definition.csv` can be read.
4. Check raw files can be detected.
5. Check at least one waveform can be normalized.
6. Check at least one waveform can produce features.
7. Check result CSVs have required columns.
8. Check Excel export works.
9. Check figures export to PNG.

If no raw waveform file exists, create a temporary synthetic waveform only for internal testing under:

```text
04_results/run_*/logs/test_artifacts/
```

Do not put synthetic files in `00_raw_csv/`.

Do not mix synthetic data with real result tables.

---

## 17. Error Handling

If any file fails:

1. Write to `logs/error_files.csv`.
2. Write error to `logs/run.log`.
3. Continue with other files.
4. Do not crash the entire run.

If any group has no valid files:

1. Write empty or NaN statistics row if appropriate.
2. Mark `group_decision = insufficient_valid_data`.
3. Write warning to `run.log`.

---

## 18. Final Response Requirement

When finished, report only:

1. What files were created or updated.
2. The run folder path.
3. How many raw files were found.
4. How many files were successfully normalized.
5. How many files were successfully analyzed.
6. How many errors occurred.
7. Where to find the Excel report.
8. Where to find the run log.
9. Any blocking issues.

Do not provide long scientific interpretation in the final Codex response.

## 19. Extra S001 Comparison Plot Rules

Codex must generate three extra waveform comparison plot types when the corresponding data exist.

---

### Plot Type 1: Same Config, Multiple Distances

Codex must group files by:

```text
date + config_group + load_condition + ground_condition
```

Within each group, Codex must search for waveform files whose:

```text
sample_index = S001
```

If at least 2 different `distance_m` values have valid `S001` waveforms, Codex must generate one time-domain overlay plot and one frequency-domain overlay plot.

#### Per-Distance Selection Rule

For each distance, Codex must select exactly one waveform:

1. `sample_index` must equal `S001`
2. Prefer `block_id = B01`
3. If multiple matches exist, choose the smallest `block_id`
4. If there is still more than one match, choose the lexicographically smallest file name

Codex must not randomly choose a waveform.

#### Plot Type

Required plots:

```text
time-domain overlay comparison plot
frequency-domain overlay comparison plot
```

Alignment:

```text
peak-time alignment
```

Legend labels must use the complete waveform `file_id` without date, for example:

```text
G1_D0p1m_L1Mohm_Glong_B01_S001
G1_D0p3m_L1Mohm_Glong_B01_S001
```

#### Required Output

Save outputs to:

```text
04_results/run_*/group_summary/distance_S001_comparison/
```

Required index file:

```text
group_summary/distance_S001_comparison/distance_S001_comparison_index.csv
```

Suggested file name patterns:

```text
{date}_{config_group}_{load_condition}_{ground_condition}_S001_distance_compare_time
{date}_{config_group}_{load_condition}_{ground_condition}_S001_distance_compare_freq
```

---

### Plot Type 2: Multiple Configs, Minimum Available Distance

Codex must group files by:

```text
date + load_condition + ground_condition
```

Within each group, Codex must compare different `config_group` values.

For each `config_group`, Codex must select exactly one waveform using this rule:

1. use only files with `sample_index = S001`
2. search distances in this priority order:

```text
0.1m -> 0.3m -> 0.6m -> 0.8m
```

3. choose the smallest available distance that has a valid `S001`
4. within that distance, prefer `block_id = B01`
5. if multiple matches remain, choose the smallest `block_id`
6. if still tied, choose the lexicographically smallest file name

If at least 2 different `config_group` values have valid selected waveforms, Codex must generate one time-domain overlay plot and one frequency-domain overlay plot.

#### Plot Type

Required plots:

```text
time-domain overlay comparison plot
frequency-domain overlay comparison plot
```

Alignment:

```text
peak-time alignment
```

Legend labels must use the complete waveform `file_id` without date, for example:

```text
G1_D0p1m_L1Mohm_Glong_B01_S001
G3_D0p1m_L1Mohm_Gshort_B01_S001
```

#### Required Output

Save outputs to:

```text
04_results/run_*/group_summary/config_min_distance_S001_comparison/
```

Required index file:

```text
group_summary/config_min_distance_S001_comparison/config_min_distance_S001_comparison_index.csv
```

Suggested file name patterns:

```text
{date}_{load_condition}_{ground_condition}_config_min_distance_S001_compare_time
{date}_{load_condition}_{ground_condition}_config_min_distance_S001_compare_freq
```

---

### Plot Type 3: Multiple Configs, Same Distance

Codex must group files by:

```text
date + distance_m
```

Within each group, Codex must compare different `config_group` values.

For each `config_group`, Codex must select exactly one waveform using this rule:

1. use only files with `sample_index = S001`
2. use only files at the same `distance_m`
3. prefer `block_id = B01`
4. if multiple matches remain, choose the smallest `block_id`
5. if still tied, choose the lexicographically smallest file name

If at least 2 different `config_group` values have valid selected waveforms, Codex must generate one time-domain overlay plot and one frequency-domain overlay plot.

#### Plot Type

Required plots:

```text
time-domain overlay comparison plot
frequency-domain overlay comparison plot
```

Alignment:

```text
peak-time alignment for time-domain overlay
```

Legend labels must use the complete waveform `file_id` without date.

#### Required Output

Save outputs to:

```text
04_results/run_*/group_summary/config_same_distance_S001_comparison/
```

Required index file:

```text
group_summary/config_same_distance_S001_comparison/config_same_distance_S001_comparison_index.csv
```

Suggested file name patterns:

```text
{date}_{distance_token}_config_same_distance_S001_compare_time
{date}_{distance_token}_config_same_distance_S001_compare_freq
```

---

### Forbidden Behavior

Codex must not:

```text
mix different dates in one comparison plot
mix different load_condition values in Plot Type 1 or Plot Type 2
mix different ground_condition values in Plot Type 1 or Plot Type 2
mix different config_group values in Plot Type 1
mix different distances in the selection logic for one config_group in Plot Type 2
mix different distances in Plot Type 3
randomly choose waveforms
use non-S001 waveforms unless explicitly requested by the user
```

## 20. Template Selection Rule

Codex must use a two-pass template strategy with manual override.

### Template Priority

Codex must select the template using the following priority:

```text
Priority 0: manual template specified by the user in the initial prompt
Priority 1: auto medoid template from G3_D0p3m_L1Mohm_Gshort
Priority 2: auto medoid template from G4_D0p3m_L50ohm_Gcoax
Priority 3: fallback auto medoid template from available non-G2 data
Priority 4: low-confidence fallback template from G2 only if no other candidate exists

### Manual Template Override

If the initial user prompt specifies either:

```text
manual_template_file_id = ...
```

or

```text
manual_template_file_path = ...
```

Codex must:

1. Validate the specified waveform.
2. Use the specified waveform as the template if valid.
3. Skip automatic template selection.
4. Record `manual_template_used = 1`.
5. Record the template in `template/template_selection.csv`.
6. Save the normalized template waveform as `template/selected_template_waveform.csv`.

If the manual template is specified but invalid, Codex must not silently choose another template. It must:

1. Mark `template_status = manual_template_invalid`.
2. Write the error to `logs/run.log`.
3. Write the error to `logs/error_files.csv`.
4. Set `rho = NaN` for waveform-correlation outputs if no valid template is available.
5. Report the issue in the final response.

### Two-Pass Auto Template Strategy

If no valid manual template is specified, Codex must use the two-pass automatic medoid strategy.

First pass:

```text
Read and normalize all waveforms.
Extract features that do not depend on rho.
Screen candidate template waveforms using non-rho metrics.
```

The first-pass candidate screening must not use `rho`.

Allowed first-pass screening metrics include:

```text
parse_status
analysis_status
included
Apk
f1_MHz
PSR_dB
narrowband_SNR_dB
fit_R2
num_bursts
single_burst
envelope_monotonic
clipped
saturated
aliasing_flag
reignition_flag
multiburst_flag
overdamped_flag
nonoscillatory_flag
echo_flag
multi_peak_flag
beating_flag
period_drift_flag
```

Second pass:

```text
Build the medoid template.
Compute rho for all waveforms.
Perform final A-H classification.
Write final features and labels.
```

### Default Reference Groups

Codex must first try to build the template from:

```text
G3_D0p3m_L1Mohm_Gshort
```

If no usable data exist in that group, Codex must try:

```text
G4_D0p3m_L50ohm_Gcoax
```

### Fallback Rule When Both Reference Groups Are Missing

If both reference groups have no usable data, Codex must select a fallback template from the existing data.

Fallback group priority:

```text
1. G3, all available distances, distance priority 0.3 m -> 0.6 m -> 0.8 m
2. G4, all available distances, distance priority 0.3 m -> 0.6 m -> 0.8 m
3. G1, all available distances, distance priority 0.3 m -> 0.6 m -> 0.8 m
4. G2, all available distances, only if no non-G2 candidate exists
```

G2 is a probe-loop artifact test group. Codex must avoid using G2 as a template source unless no non-G2 candidate exists.

If G2 is used as template source, Codex must set:

```text
template_confidence = low
warning_flag = low_confidence_template_from_G2
fallback_used = 1
```

### Candidate Quality Rules

Codex should prefer candidate waveforms satisfying:

```text
included = 1
parse_status = success
valid normalized waveform
valid f1_MHz
valid Apk
PSR_dB >= 10
narrowband_SNR_dB >= 10
fit_R2 >= 0.70
single_burst = true
envelope_monotonic = true
clipped = false
saturated = false
aliasing_flag = false
reignition_flag = false
multiburst_flag = false
```

If fewer than 10 candidates satisfy the preferred rules, Codex may use relaxed rules:

```text
PSR_dB >= 6
narrowband_SNR_dB >= 6
fit_R2 >= 0.50
```

If at least 3 candidates remain, Codex must use:

```text
medoid_waveform_after_alignment
```

If fewer than 3 candidates remain, Codex may use the best-ranked single waveform as the template, but must record:

```text
fallback_used = 1
warning_flag = single_candidate_template
template_confidence = low or medium
```

### Medoid Definition

The medoid template is the real measured waveform that has the minimum total distance to all other candidate waveforms after:

```text
peak-time alignment
max-absolute normalization
common-window trimming
```

Codex must not use an average waveform as the primary template.

### Required Template Outputs

Every run must generate:

```text
04_results/run_*/template/template_selection.csv
04_results/run_*/template/template_candidates.csv
04_results/run_*/template/selected_template_waveform.csv
04_results/run_*/template/template_overlay_check.png
```

The selected template must also be recorded in:

```text
04_results/run_*/logs/run.log
04_results/run_*/config_snapshot/config_snapshot.csv
```

### Forbidden Template Behavior

Codex must not:

```text
randomly choose a template
silently switch template source
use rho to select the initial template
use G2 as template source when G1/G3/G4 candidates exist
use an average waveform as the primary template
hide fallback template selection
continue with an invalid manual template
```

````

---

## Independent Peak Rule for f1 and f2

Codex must not identify f1 and f2 by simply selecting the largest and second-largest raw local maxima.

Codex must first identify independent peak clusters.

### Same-Peak Cluster Rule

Two local maxima must be treated as the same peak cluster if any of the following are true:

```text
frequency separation < 5 MHz
valley depth between peaks < 6 dB
separation is less than half of the main peak width
````

Small drops and re-rises inside the same broad peak must not be labeled as f2.

### f1 Definition

```text
f1 = highest-amplitude independent clear peak that satisfies prominence and SNR requirements
```

f1 is selected after independent peak clustering by amplitude priority.

### f2 Definition

```text
f2 = second-highest-amplitude independent clear peak excluding f1
```

f2 must belong to a different independent peak cluster from f1.

### Dominant Peak

Codex must additionally record:

```text
fdom_MHz
Adom
```

where `fdom_MHz` is the highest-amplitude independent peak.

### Forbidden Behavior

Codex must not:

```text
label two shoulders inside the same broad peak as f1 and f2
use raw unsmoothed local ripples as independent peaks
select f2 from the same peak cluster as f1
hide when f1 falls back to dominant peak
```

````

---
