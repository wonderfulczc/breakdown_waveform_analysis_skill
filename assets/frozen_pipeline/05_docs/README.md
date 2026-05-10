# Breakdown Waveform Analysis

本项目用于处理击穿放电无线传感实验中的波形 CSV 文件，自动生成 Origin 风格图件、单波形参数、波形类别标签、质量等级、组统计结果、汇总 Excel、日志和快速报告。

本项目只处理当前实验：

```text
ML01 = 实验一，测量链排伪影与接收端影响核查
```

---

## File System Permission Summary

Codex must follow the file-system permission matrix in:

```text
codex_prompt/project_rules.md
```

Summary:

| Path | Permission |
|---|---|
| `00_raw_csv/` | read-only raw waveform input |
| `01_metadata/group_definition.csv` | read-only user-defined group table |
| `01_metadata/sample_index.csv` | Codex may create/update while preserving user notes |
| `02_config/` | read-only configuration files |
| `03_scripts/` | Codex may write Python scripts |
| `04_results/run_*/` | Codex may write generated outputs only |
| `05_docs/` | read-only documentation |
| `codex_prompt/` | read-only prompt files |

Codex may write only to:

```text
03_scripts/
01_metadata/sample_index.csv
01_metadata/sample_index.xlsx
04_results/run_YYYYMMDD_HHMM/
```

Codex must not modify raw waveform files, configuration files, documentation files, or prompt files.

---

## Repeated Data Processing Rule

After the first successful pipeline build, later data-processing runs should reuse existing scripts.

Default mode:

```text
run_mode
```

Codex should only regenerate or modify scripts if:

1. required scripts are missing;
2. smoke test fails;
3. scripts are incompatible with current configs/docs;
4. required outputs cannot be generated;
5. user explicitly requests script modification.

For normal repeated processing, Codex should:

```text
reuse existing scripts
create a new run folder
process current raw waveform files
generate new results
write script_reuse_audit.csv
```
---

## 1. Project Goal

本项目目标是将原始波形 CSV 批量处理为可复现、可追溯、可检查的分析结果。

输入：

```text
00_raw_csv/
01_metadata/
02_config/
05_docs/
```

输出：

```text
03_scripts/
04_results/run_YYYYMMDD_HHMM/
```

核心输出包括：

1. Origin 风格时域图
2. Origin 风格频域图
3. 单波形拟合图
4. 每组时域叠加图
5. 每组频域叠加图
6. 每组统计图
7. 单波形参数表
8. 单波形分类表
9. 每组统计表
10. 每组质量汇总表
11. 汇总 Excel
12. 运行日志
13. 错误文件表
14. 剔除文件表
15. 配置快照
16. 快速报告

---

## 2. Core Rules

Codex 和 Python 脚本必须遵守以下规则：

1. `00_raw_csv/` 中的原始 CSV 只允许读取，不允许修改。
2. 每次分析必须生成新的 `04_results/run_YYYYMMDD_HHMM/` 文件夹。
3. 不允许覆盖旧 run 结果。
4. CSV 是主结果数据。
5. Excel 只是汇总查看文件，由 CSV 自动生成。
6. 配置文件必须复制到本次 run 的 `config_snapshot/` 中。
7. 所有图件必须能追溯到原始 CSV。
8. 所有分类结果必须能追溯到 `classification_rules.yaml`。
9. 所有算法参数必须能追溯到 `analysis_config.yaml`。
10. 所有绘图参数必须能追溯到 `plot_style_origin.yaml`。
11. 运行失败、读取失败、计算失败、被剔除文件必须记录。
12. 不允许只生成图片而不生成参数表。
13. 不允许只生成 Excel 而不生成 CSV。
14. 不允许在无记录情况下剔除文件。
15. 不允许改变 `05_docs/` 中定义的核心字段顺序。

---

## 3. Final Directory Structure

```text
breakdown_waveform_analysis/
├─ 00_raw_csv/
│  ├─ G1_D0p3/
│  ├─ G1_D0p6/
│  ├─ G1_D0p8/
│  ├─ G2_D0p8/
│  ├─ G3_D0p3/
│  ├─ G3_D0p6/
│  ├─ G3_D0p8/
│  ├─ G4_D0p3/
│  ├─ G4_D0p6/
│  └─ G4_D0p8/
│
├─ 01_metadata/
│  ├─ sample_index.csv
│  ├─ sample_index.xlsx
│  └─ group_definition.csv
│
├─ 02_config/
│  ├─ analysis_config.yaml
│  ├─ classification_rules.yaml
│  └─ plot_style_origin.yaml
│
├─ 03_scripts/
│  ├─ run_all.py
│  ├─ read_waveform.py
│  ├─ preprocess.py
│  ├─ extract_features.py
│  ├─ classify_waveform.py
│  ├─ plot_waveform.py
│  ├─ summarize_group.py
│  └─ export_report.py
│
├─ 04_results/
│  └─ run_YYYYMMDD_HHMM/
│     ├─ single_waveform/
│     │  ├─ figures_time_domain/
│     │  ├─ figures_frequency_domain/
│     │  ├─ figures_fit/
│     │  ├─ single_waveform_features.csv
│     │  └─ single_waveform_labels.csv
│     │
|     ├─ normalized_waveform/
│     │  ├─ normalized_csv/
│     │  ├─ format_detection_summary.csv/  
│     │
│     ├─ group_summary/
│     │  ├─ overlay_time_domain/
│     │  ├─ overlay_frequency_domain/
│     │  ├─ statistics_figures/
│     │  ├─ group_statistics.csv
│     │  └─ group_quality_summary.csv
│     │
│     ├─ config_snapshot/
│     │  ├─ analysis_config_used.yaml
│     │  ├─ classification_rules_used.yaml
│     │  ├─ plot_style_origin_used.yaml
│     │  └─ config_snapshot.csv
│     │
│     ├─ excel_report/
│     │  └─ waveform_analysis_summary.xlsx
│     │
│     ├─ logs/
│     │  ├─ run.log
│     │  ├─ error_files.csv
│     │  └─ excluded_files.csv
│     │
│     └─ report/
│        ├─ quick_report.md
│        └─ quick_report.pdf
│
├─ 05_docs/
│  ├─ README.md
│  ├─ file_naming_rule.md
│  └─ parameter_definition.md
│
└─ codex_prompt/
   ├─ task_prompt.md
   └─ project_rules.md
```

---

## 4. Directory and Responsibility

| Path | Role | Source |
|---|---|---|
| `00_raw_csv/` | 原始波形 CSV 输入目录，只读 | User |
| `00_raw_csv/Gx_Dyp/` | 按配置组和距离存放 CSV | User |
| `01_metadata/` | 样本索引和组合定义 | User + Codex |
| `sample_index.csv` | 每个 CSV 一行，记录文件路径、实验条件、是否纳入分析 | Codex生成，User可补充 |
| `sample_index.xlsx` | 给用户人工查看和编辑的索引表 | Codex从CSV导出 |
| `group_definition.csv` | 每组组合的定义 | User |
| `02_config/` | 分析参数、分类规则、绘图风格 | User |
| `analysis_config.yaml` | FFT、峰搜索、SNR、拟合、采样单位等参数 | User |
| `classification_rules.yaml` | A/B/C/D/E/F/G/H 和质量等级判据 | User |
| `plot_style_origin.yaml` | Origin 风格绘图参数 | User |
| `03_scripts/` | Python 分析脚本 | Codex |
| `run_all.py` | 一键运行完整流程 | Codex |
| `read_waveform.py` | 读取 CSV，识别时间列和电压列 | Codex |
| `preprocess.py` | 去直流、截取主 burst、滤波、归一化 | Codex |
| `extract_features.py` | 提取 Apk、f1、f2、PSR、SNR、α、ρ 等 | Codex |
| `classify_waveform.py` | 输出波形类别和质量标签 | Codex |
| `plot_waveform.py` | 生成时域、频域、拟合、叠加、统计图 | Codex |
| `summarize_group.py` | 计算每组统计参数和质量比例 | Codex |
| `export_report.py` | 导出 Excel、Markdown、PDF 报告 | Codex |
| `04_results/` | 所有分析输出 | Codex |
| `run_YYYYMMDD_HHMM/` | 单次分析结果文件夹 | Codex |
| `single_waveform/` | 单波形图和单波形结果表 | Codex |
| `group_summary/` | 组叠加图、组统计图、组统计表 | Codex |
| `config_snapshot/` | 本次 run 使用的配置快照 | Codex |
| `excel_report/` | 汇总 Excel 工作簿 | Codex |
| `logs/` | 运行日志、错误文件、剔除文件 | Codex |
| `report/` | 快速报告 | Codex |
| `05_docs/` | 项目说明、命名规则、字段定义 | User |
| `codex_prompt/` | 后续给 Codex 的任务 prompt | User |

---

## 5. Codex Fixed Workflow

以下工作流必须由 Codex 在开始任何代码编写或数据处理前读取并遵守。

### 5.1 Work Order

Codex 必须按以下顺序工作：

```text
Step 01: Read 05_docs/README.md
Step 02: Read 05_docs/file_naming_rule.md
Step 03: Read 05_docs/parameter_definition.md
Step 04: Read 02_config/analysis_config.yaml
Step 05: Read 02_config/classification_rules.yaml
Step 06: Read 02_config/plot_style_origin.yaml
Step 07: Scan 00_raw_csv/
Step 08: Detect the real file format of each waveform file.
Step 09: Parse waveform files using format-specific loaders.
Step 10: Convert each successfully parsed waveform to normalized CSV.
Step 11: Save normalized waveform files to normalized_waveform/normalized_csv/.
Step 12: Save format detection results to normalized_waveform/format_detection_summary.csv.
Step 13: Run all downstream analysis from normalized waveform files.
Step 14: Parse file names according to file_naming_rule.md
Step 15: Create or update 01_metadata/sample_index.csv
Step 16: Create or update 01_metadata/sample_index.xlsx
Step 17: Read 01_metadata/group_definition.csv
Step 18: Generate or update Python scripts in 03_scripts/
Step 19: Create a new 04_results/run_YYYYMMDD_HHMM/ folder
Step 20: Copy current config files into config_snapshot/
Step 21: Generate config_snapshot.csv
Step 22: Run single-waveform analysis
Step 23: Generate single-waveform time-domain figures
Step 24: Generate single-waveform frequency-domain figures
Step 25: Generate single-waveform fitting figures
Step 26: Generate single_waveform_features.csv
Step 27: Generate single_waveform_labels.csv
Step 28: Run group-level statistics
Step 29: Generate group overlay time-domain figures
Step 30: Generate group overlay frequency-domain figures
Step 31: Generate group statistics figures
Step 32: Generate group_statistics.csv
Step 33: Generate group_quality_summary.csv
Step 34: Generate logs/run.log
Step 35: Generate logs/error_files.csv
Step 36: Generate logs/excluded_files.csv
Step 37: Generate excel_report/waveform_analysis_summary.xlsx
Step 38: Generate report/quick_report.md
Step 39: Generate report/quick_report.pdf if the environment supports it
```

---

### 5.2 Input Rule

Codex 只能从以下目录读取输入：

```text
00_raw_csv/
01_metadata/
02_config/
05_docs/
```

Codex 可以读取 `codex_prompt/` 中的 prompt，但不应把它作为数据输入。

---

### 5.3 Output Rule

Codex 只能向以下位置写入代码、索引和结果：

```text
03_scripts/
04_results/run_YYYYMMDD_HHMM/
01_metadata/sample_index.csv
01_metadata/sample_index.xlsx
```

---

### 5.4 Forbidden Operations

Codex 不允许：

1. 修改 `00_raw_csv/` 中的任何原始 CSV。
2. 重命名 `00_raw_csv/` 中的任何原始 CSV。
3. 删除 `00_raw_csv/` 中的任何原始 CSV。
4. 在 `00_raw_csv/` 中写入任何结果文件。
5. 覆盖旧的 `04_results/run_*/`。
6. 删除用户手动维护的配置文件。
7. 删除用户手动维护的文档文件。
8. 在没有日志记录的情况下剔除文件。
9. 只生成 Excel 而不生成 CSV。
10. 只生成图片而不生成参数表。
11. 生成无法追溯到原始 CSV 的图件或表格。
12. 自行改变 `parameter_definition.md` 中定义的核心字段名和字段顺序。
13. 自行改变 `file_naming_rule.md` 中定义的文件命名规则。
14. 忽略 `classification_rules.yaml` 而自行创造波形分类规则。
15. Codex must not modify, rename, delete, or overwrite raw waveform files.
16. Codex must not silently guess waveform format when parsing fails.
17. Codex must not run feature extraction on a file before generating a normalized waveform representation.

---

## 6. Required User Prepared Files

用户需要提前准备或确认以下文件。

| File | Required | Description |
|---|---:|---|
| `00_raw_csv/*.csv` | Yes | 原始波形 CSV |
| `01_metadata/group_definition.csv` | Yes | 组合定义 |
| `01_metadata/sample_index.csv` | Recommended | 可先建空表，Codex 自动更新 |
| `02_config/analysis_config.yaml` | Yes | 分析参数 |
| `02_config/classification_rules.yaml` | Yes | 分类规则 |
| `02_config/plot_style_origin.yaml` | Yes | 绘图风格 |
| `05_docs/README.md` | Yes | 项目说明 |
| `05_docs/file_naming_rule.md` | Yes | 文件命名规则 |
| `05_docs/parameter_definition.md` | Yes | 参数定义 |

---

## 7. Required Codex Generated Files

Codex 应生成以下文件。

| File | Description |
|---|---|
| `03_scripts/*.py` | 分析脚本 |
| `single_waveform_features.csv` | 单波形完整参数 |
| `single_waveform_labels.csv` | 单波形分类和质量标签 |
| `group_statistics.csv` | 每组统计结果 |
| `group_quality_summary.csv` | 每组质量比例 |
| `config_snapshot.csv` | 本次配置快照 |
| `error_files.csv` | 错误文件记录 |
| `excluded_files.csv` | 剔除文件记录 |
| `waveform_analysis_summary.xlsx` | 汇总 Excel |
| `quick_report.md` | 快速报告 |
| `quick_report.pdf` | 快速报告 PDF |

---

## 8. Result Files

每次运行后，应生成：

```text
04_results/run_YYYYMMDD_HHMM/
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

---

## 9. Excel Summary Workbook

`waveform_analysis_summary.xlsx` 是一个 Excel 工作簿，不是多个 Excel 文件。

位置：

```text
04_results/run_YYYYMMDD_HHMM/excel_report/waveform_analysis_summary.xlsx
```

它由多个 CSV 汇总而来。

| Excel Sheet | Source |
|---|---|
| `README` | Codex 根据 run 信息生成 |
| `sample_index` | `01_metadata/sample_index.csv` |
| `single_waveform_features` | `single_waveform/single_waveform_features.csv` |
| `single_waveform_labels` | `single_waveform/single_waveform_labels.csv` |
| `group_statistics` | `group_summary/group_statistics.csv` |
| `group_quality_summary` | `group_summary/group_quality_summary.csv` |
| `error_files` | `logs/error_files.csv` |
| `excluded_files` | `logs/excluded_files.csv` |
| `config_snapshot` | `config_snapshot/config_snapshot.csv` |

规则：

1. Excel 只做汇总查看。
2. CSV 是主结果源。
3. Excel 必须由 CSV 自动生成。
4. Excel 中每个重要 sheet 都必须能找到对应 CSV 来源。

---

## 10. Data Flow

本项目固定数据流如下：

```text
00_raw_csv/
01_metadata/
02_config/
05_docs/
        ↓
03_scripts/
        ↓
04_results/run_YYYYMMDD_HHMM/
        ↓
single_waveform_features.csv
single_waveform_labels.csv
group_statistics.csv
group_quality_summary.csv
error_files.csv
excluded_files.csv
config_snapshot.csv
        ↓
waveform_analysis_summary.xlsx
quick_report.md
quick_report.pdf
```

---

## 11. Metadata Rule

元数据优先级：

```text
filename parsing
sample_index.csv
folder path
error or warning
```

若文件名和 `sample_index.csv` 冲突：

1. 以 `sample_index.csv` 为准。
2. 在 `logs/run.log` 中记录 warning。
3. 在结果表中标记 `metadata_conflict`。
4. 不应中断整个批处理。

---

## 12. Figure Output Rule

单波形时域图输出到：

```text
04_results/run_YYYYMMDD_HHMM/single_waveform/figures_time_domain/
```

单波形频域图输出到：

```text
04_results/run_YYYYMMDD_HHMM/single_waveform/figures_frequency_domain/
```

单波形拟合图输出到：

```text
04_results/run_YYYYMMDD_HHMM/single_waveform/figures_fit/
```

组时域叠加图输出到：

```text
04_results/run_YYYYMMDD_HHMM/group_summary/overlay_time_domain/
```

组频域叠加图输出到：

```text
04_results/run_YYYYMMDD_HHMM/group_summary/overlay_frequency_domain/
```

组统计图输出到：

```text
04_results/run_YYYYMMDD_HHMM/group_summary/statistics_figures/
```

图件格式：

```text
PNG
```

---

## 13. Logging Rule

Codex 必须生成：

```text
04_results/run_YYYYMMDD_HHMM/logs/run.log
```

日志至少记录：

1. run_id
2. 运行开始时间
3. 运行结束时间
4. 输入 CSV 总数
5. 成功分析文件数
6. 失败文件数
7. 被剔除文件数
8. 读取的配置文件
9. 复制到 config_snapshot 的配置文件
10. 文件名解析失败记录
11. 元数据冲突记录
12. 计算失败记录
13. 分类失败记录
14. Excel 导出状态

---

## 14. Error Handling Rule

若某个文件失败：

1. 不应中断全局批处理。
2. 应写入 `logs/error_files.csv`。
3. 应在 `logs/run.log` 中记录。
4. 应继续处理其他文件。

常见错误状态：

```text
filename_parse_failed
csv_read_failed
invalid_time_column
invalid_voltage_column
feature_extract_failed
fit_failed
classification_failed
```

---

## 15. Exclusion Rule

若文件被排除出正式统计：

1. 应写入 `logs/excluded_files.csv`。
2. 应记录剔除原因。
3. 应保留原始文件路径。
4. 应保留原始质量标签。
5. 不应删除原始 CSV。

剔除来源：

```text
algorithm
user
```

---

## 16. Config Snapshot Rule

每次 run 必须复制以下配置文件：

```text
02_config/analysis_config.yaml
02_config/classification_rules.yaml
02_config/plot_style_origin.yaml
```

复制到：

```text
04_results/run_YYYYMMDD_HHMM/config_snapshot/
```

并重命名为：

```text
analysis_config_used.yaml
classification_rules_used.yaml
plot_style_origin_used.yaml
```

同时生成：

```text
config_snapshot.csv
```

---

## 17. Script Responsibility

| Script | Responsibility |
|---|---|
| `run_all.py` | 调用完整流程 |
| `read_waveform.py` | 读取 CSV，识别时间列和电压列 |
| `preprocess.py` | 去直流、截取 burst、滤波、归一化 |
| `extract_features.py` | 提取 Apk、f1、f2、PSR、SNR、α、ρ |
| `classify_waveform.py` | 根据 `classification_rules.yaml` 分类 |
| `plot_waveform.py` | 生成单波形图、叠加图、统计图 |
| `summarize_group.py` | 生成组统计和质量比例 |
| `export_report.py` | 导出 Excel、Markdown、PDF 报告 |

---

## 18. Final Requirement

Codex 完成工作后，应保证：

1. 原始 CSV 未被修改。
2. 每次 run 结果独立保存。
3. 每个原始 CSV 都有对应处理状态。
4. 每个成功分析的 CSV 都有单波形参数。
5. 每个成功分析的 CSV 都有分类标签。
6. 每个组都有统计结果。
7. 每个组都有质量比例。
8. Excel 是从 CSV 汇总生成。
9. 配置快照完整保存。
10. 日志能够追溯所有错误和剔除。
11. 图件路径写入结果表。
12. 结果可复现、可检查、可追溯。

## 19. Template Selection Summary

Template correlation uses a two-pass strategy with manual override.

Priority:

```text
0. Manual template specified in the initial prompt
1. Auto medoid from G3_D0p3m_L1Mohm_Gshort
2. Auto medoid from G4_D0p3m_L50ohm_Gcoax
3. Fallback medoid from available non-G2 data
4. G2 only as low-confidence last resort
