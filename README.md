# ML01 Breakdown Waveform Analysis Skill

`ml01-breakdown-waveform-analysis` 是一个面向 ML01 击穿放电波形数据的 Codex skill。它封装了冻结版 `breakdown_waveform_analysis` 数据处理流程，用于在用户只提供一个已重命名 CSV 波形目录的情况下，自动完成格式识别、归一化、特征提取、波形分类、组统计、科研作图、Excel 汇总和日志输出。

本 skill 服务的研究链路是：击穿放电伴生电磁信号的测量、排伪迹、频谱特征提取和组级统计。它不直接给出物理机理结论，只生成可复查的数据处理结果。

## 主要功能

- 自动复制用户指定目录下的 ML01 波形 CSV 到隔离工作区
- 先执行 smoke test，通过后删除 smoke 结果
- 执行完整 ML01 波形分析流程
- 输出单波形时域图、频域图、拟合图
- 输出组图、统计图和 S001 对比图
- 输出归一化 CSV/XLSX、特征表、标签表、组统计表、Excel 总表和日志
- 固定使用内置 `group_definition.csv`
- 支持额外对比图，例如两条波形对比、模板与指定波形对比

## 安装

将仓库克隆到 Codex 可发现的 skill 目录，例如：

```powershell
git clone https://github.com/wonderfulczc/breakdown_waveform_analysis_skill.git D:\PhD\research-agent\.agents\skills\ml01-breakdown-waveform-analysis
```

安装后重启 Codex，使 skill 重新加载。

## 触发方式

可以直接对 Codex 说：

```text
用 ML01 分析 D:\PhD\research-agent\data
```

或：

```text
使用 ML01-breakdown-waveform-analysis 处理 D:\path\to\waveform_csv_folder
```

## 输入要求

输入目录中应放置已经按 ML01 命名规则整理好的原始波形 CSV 文件，例如：

```text
20260506_ML01_G1_D0p3m_L1Mohm_Glong_B01_S001.csv
```

不符合命名规则的 CSV 不会参与正式分析，会写入 `logs/error_files.csv`。

## 输出位置

假设输入目录为：

```text
D:\PhD\research-agent\data
```

输出会写入同级日期前缀结果目录：

```text
D:\PhD\research-agent\YYYYMMDD_data_results\run_YYYYMMDD_HHMM\
```

主要输出包括：

```text
excel_report/waveform_analysis_summary.xlsx
single_waveform/single_waveform_features.csv
single_waveform/single_waveform_labels.csv
group_summary/group_statistics.csv
group_summary/group_quality_summary.csv
template/template_selection.csv
logs/run.log
logs/error_files.csv
logs/excluded_files.csv
```

## 命令行用法

也可以直接运行封装脚本：

```powershell
python D:\PhD\research-agent\.agents\skills\ml01-breakdown-waveform-analysis\scripts\run_ml01_breakdown_analysis.py D:\PhD\research-agent\data
```

额外对比图：

```powershell
python D:\PhD\research-agent\.agents\skills\ml01-breakdown-waveform-analysis\scripts\make_extra_comparison.py --run-dir <run_dir> --mode waveform-pair --file-id-a <file_id_a> --file-id-b <file_id_b>
```

模板与波形对比：

```powershell
python D:\PhD\research-agent\.agents\skills\ml01-breakdown-waveform-analysis\scripts\make_extra_comparison.py --run-dir <run_dir> --mode template-vs-waveform --file-id-a <file_id>
```

额外图会输出到：

```text
<run_dir>/extra_figures/
```

## 固定参考组

当前冻结流程固定参考组为：

```text
G3_D0p3m_L1Mohm_Gcoax
```

只有当该组存在时，才生成：

```text
fsrc_MHz
alpha_src
T1(t) template
rho
```

如果固定参考组不存在，模板保持为空，不使用其他组生成兜底模板。这是为了避免把不可信模板写入结果。

## 仓库内容

```text
SKILL.md
agents/openai.yaml
scripts/run_ml01_breakdown_analysis.py
scripts/make_extra_comparison.py
references/pipeline_summary.md
assets/frozen_pipeline/
```

`assets/frozen_pipeline/` 内含冻结版数据处理流程：

```text
01_metadata/group_definition.csv
02_config/
03_scripts/
05_docs/
codex_prompt/
freeze_manifest.csv
```

## 注意事项

- 本 skill 不修改用户输入目录中的原始 CSV。
- 输出结果保存在输入目录同级的日期前缀结果文件夹中。
- 原始数据和生成结果不应上传到 skill 仓库。
- 若后续数据处理规则需要变化，应直接修改本 skill 内置 pipeline，并重新提交到本仓库。
