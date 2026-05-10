# File Naming Rule

本文件定义原始波形 CSV 的命名规则、目录规则、字段解析规则、组合编号规则、输出图件命名规则和异常处理规则。

本项目中，Codex 和 Python 脚本必须优先依据本文件解析原始波形文件，不允许自行发明新的命名规则。

---

## 1. Raw CSV Naming Format

原始波形 CSV 推荐命名格式：

```text
YYYYMMDD_ML01_Gx_Dypzm_Lload_Gground_Bbb_Ssss.csv
```

示例：

```text
20260427_ML01_G3_D0p3m_L50ohm_Gshort_B01_S001.csv
```

---

## 2. Filename Field Meaning

| Field | Meaning | Example |
|---|---|---|
| `YYYYMMDD` | 实验日期 | `20260427` |
| `ML01` | 实验编号，实验一固定为 ML01 | `ML01` |
| `Gx` | 接收配置组 | `G1`, `G2`, `G3`, `G4` |
| `Dypzm` | 接收距离 | `D0p3m`, `D0p6m`, `D0p8m` |
| `Lload` | 终端负载 | `L1Mohm`, `L50ohm`, `L100ohm`, `L1kohm`, `Lopen` |
| `Gground` | 接地方式或返回路径 | `Glong`, `Gshort`, `Gspring`, `Gcoax`, `Gloop`, `Gnone` |
| `Bbb` | 采集块号 | `B01`, `B02`, `B03` |
| `Ssss` | 样本序号 | `S001`, `S002`, `S003` |

---

## 3. Allowed Values

### 3.1 Experiment ID

```text
ML01 = 实验一，测量链排伪影与接收端影响核查
```

当前项目只处理 `ML01`。  
若发现非 `ML01` 文件，Codex 不应中断程序，但应将该文件写入 `logs/error_files.csv` 或 `logs/excluded_files.csv`，并标记：

```text
analysis_status = invalid_experiment_id
```

---

### 3.2 Configuration Group

```text
G1 = 常规探头接法
G2 = 探头自环/伪影测试
G3 = 低环路接法
G4 = 同轴直连/定义负载接法
```

说明：

| Token | Meaning |
|---|---|
| `G1` | 当前常规探头接法 |
| `G2` | 探头自环或伪影测试组 |
| `G3` | 低环路接法，尽量减小探头地线回路 |
| `G4` | 同轴直连或定义负载接法 |

---

### 3.3 Distance

```text
D0p1m = 0.1 m
D0p2m = 0.2 m
D0p3m = 0.3 m
D0p6m = 0.6 m
D0p8m = 0.8 m
D1p0m = 1.0 m
```

距离字段必须转换为数值型 `distance_m`，单位固定为 m。

| Filename Token | Numeric Value |
|---|---:|
| `D0p1m` | `0.1` |
| `D0p2m` | `0.2` |
| `D0p3m` | `0.3` |
| `D0p6m` | `0.6` |
| `D0p8m` | `0.8` |
| `D1p0m` | `1.0` |

---

### 3.4 Load Condition

```text
L1Mohm = 1 MΩ
L50ohm = 50 Ω
L100ohm = 100 Ω
L1kohm = 1 kΩ
Lopen = 开路
```

建议同时保留两个字段：

```text
load_condition
load_ohm
```

| Filename Token | `load_condition` | `load_ohm` |
|---|---|---:|
| `L1Mohm` | `1Mohm` | `1000000` |
| `L50ohm` | `50ohm` | `50` |
| `L100ohm` | `100ohm` | `100` |
| `L1kohm` | `1kohm` | `1000` |
| `Lopen` | `open` | `NaN` |

---

### 3.5 Ground Condition

```text
Glong = 长地线
Gshort = 短地线
Gspring = 接地弹簧
Gcoax = 同轴外导体返回
Gloop = 探头自环
Gnone = 无明确接地返回
```

| Filename Token | Meaning |
|---|---|
| `Glong` | 长地线或长鳄鱼夹地线 |
| `Gshort` | 短地线 |
| `Gspring` | 接地弹簧 |
| `Gcoax` | 同轴外导体返回 |
| `Gloop` | 探头自环或伪影测试闭环 |
| `Gnone` | 无明确接地返回路径 |

---

### 3.6 Block ID

块号用于记录分块采集顺序，避免电极状态漂移与配置变化混淆。

```text
B01 = 第1个采集块
B02 = 第2个采集块
B03 = 第3个采集块
```

块号字段必须保留为字符串，不应转换为纯数字。

---

### 3.7 Sample Index

样本号用于标识同一组内的第几次放电。

```text
S001 = 第1个样本
S002 = 第2个样本
S003 = 第3个样本
```

样本号字段必须保留为字符串，不应转换为纯数字。

---

## 4. Folder Naming Rule

原始 CSV 建议按配置组和距离存放：

```text
00_raw_csv/
├─ G1_D0p1/
├─ G1_D0p3/
├─ G1_D0p6/
├─ G1_D0p8/
├─ G1_D1p0/
├─ G2_D0p3/
├─ G2_D0p6/
├─ G2_D0p8/
├─ G3_D0p1/
├─ G3_D0p3/
├─ G3_D0p6/
├─ G3_D0p8/
├─ G3_D1p0/
├─ G4_D0p1/
├─ G4_D0p3/
├─ G4_D0p6/
├─ G4_D0p8/
└─ G4_D1p0/
```

文件夹命名格式：

```text
Gx_Dypz
```

示例：

```text
G3_D0p3
```

含义：

```text
G3配置组，0.3 m距离
```

---

## 5. Folder and Filename Consistency Rule

Codex 解析文件时，应同时检查：

1. 文件夹名中的配置组和距离
2. 文件名中的配置组和距离

若二者一致，则正常处理。

若二者不一致：

1. 以文件名为主。
2. 在 `logs/run.log` 中记录 warning。
3. 在 `sample_index.csv` 中标记 `metadata_conflict`。
4. 在 `single_waveform_features.csv` 的 `analysis_status` 或 `notes` 中记录冲突。
5. 不应直接丢弃该文件，除非文件名也无法解析。

---

## 6. Filename Examples

| Filename | Meaning |
|---|---|
| `20260427_ML01_G3_D0p3m_L50ohm_Gshort_B01_S001.csv` | 实验一，G3，0.3 m，50 Ω，短地线，第1块第1次 |
| `20260427_ML01_G2_D0p8m_L1Mohm_Gloop_B02_S010.csv` | 实验一，G2，0.8 m，1 MΩ，自环，第2块第10次 |
| `20260427_ML01_G4_D0p6m_L50ohm_Gcoax_B03_S015.csv` | 实验一，G4，0.6 m，50 Ω，同轴返回，第3块第15次 |
| `20260427_ML01_G1_D0p8m_L1Mohm_Glong_B01_S005.csv` | 实验一，G1，0.8 m，1 MΩ，长地线，第1块第5次 |

---

## 7. Parsing Rule

Codex 应优先从文件名解析以下字段：

| Output Field | Source Filename Field |
|---|---|
| `date` | `YYYYMMDD` |
| `experiment_id` | `ML01` |
| `config_group` | `Gx` |
| `distance_token` | `Dypzm` |
| `distance_m` | `Dypzm` converted to number |
| `load_condition` | `Lload` |
| `load_ohm` | `Lload` converted to number |
| `ground_condition` | `Gground` |
| `block_id` | `Bbb` |
| `sample_index` | `Ssss` |

---

## 8. Recommended Regex

Codex 可使用以下正则表达式解析文件名：

```text
^(?P<date>\d{8})_(?P<experiment_id>ML01)_(?P<config_group>G[1-4])_(?P<distance_token>D\d+p\d+m)_(?P<load_token>L(?:1Mohm|50ohm|100ohm|1kohm|open))_(?P<ground_token>G(?:long|short|spring|coax|loop|none))_(?P<block_id>B\d{2})_(?P<sample_index>S\d{3})\.csv$
```

注意：

1. 匹配应大小写敏感。
2. 文件扩展名固定为 `.csv`。
3. 若后续存在大写 `.CSV`，Codex 可兼容读取，但应在日志中提示建议统一为 `.csv`。

---

## 9. Group ID Rule

`group_id` 用于组统计，应由以下字段组合生成：

```text
config_group + distance_token + load_token + ground_token
```

推荐格式：

```text
Gx_Dypzm_Lload_Gground
```

示例：

```text
G3_D0p3m_L50ohm_Gshort
G2_D0p8m_L1Mohm_Gloop
G4_D0p6m_L50ohm_Gcoax
```

`group_id` 必须在以下表中保持一致：

```text
sample_index.csv
single_waveform_features.csv
single_waveform_labels.csv
group_statistics.csv
group_quality_summary.csv
```

---

## 10. File ID Rule

`file_id` 应由 `group_id`、`block_id`、`sample_index` 组合生成。

推荐格式：

```text
group_id + "_" + block_id + "_" + sample_index
```

示例：

```text
G3_D0p3m_L50ohm_Gshort_B01_S001
```

`file_id` 必须唯一。  
若发现重复 `file_id`：

1. 记录到 `logs/run.log`。
2. 记录到 `logs/error_files.csv`。
3. 不应覆盖已有结果。
4. 可在重复项后附加 `_dup01` 继续保留，但必须在日志中记录。

---

## 11. Output Figure Naming Rule

单波形时域图：

```text
file_id_time.png
```

单波形频域图：

```text
file_id_freq.png
```

单波形拟合图：

```text
file_id_fit.png
```

组时域叠加图：

```text
group_id_overlay_time.png
```

组频域叠加图：

```text
group_id_overlay_freq.png
```

组统计图：

```text
group_id_statistics.png
```

---

## 12. Run ID Rule

每次运行必须生成唯一 `run_id`。

推荐格式：

```text
run_YYYYMMDD_HHMM
```

示例：

```text
run_20260427_1530
```

对应结果目录：

```text
04_results/run_20260427_1530/
```

Codex 不允许覆盖已有 run 目录。  
若同一分钟内重复运行导致目录已存在，应追加后缀：

```text
run_20260427_1530_01
run_20260427_1530_02
```

---

## 13. Fallback Rule

若文件名解析成功，则以文件名解析结果为准。

若文件名解析失败，则尝试从以下文件读取元数据：

```text
01_metadata/sample_index.csv
```

若文件名和 `sample_index.csv` 冲突：

1. 在 `logs/run.log` 中记录 warning。
2. 在 `sample_index.csv` 中增加冲突说明。
3. 默认以 `sample_index.csv` 为准。
4. 冲突文件仍可分析，但应标记：

```text
main_warning_flag = metadata_conflict
```

---

## 14. Invalid Filename Rule

若文件名不符合规则：

1. 不应中断整个批处理。
2. 该文件应写入 `logs/error_files.csv` 或 `logs/excluded_files.csv`。
3. `analysis_status` 标记为：

```text
filename_parse_failed
```

4. `suggested_action` 写明：

```text
Rename file according to file_naming_rule.md or add metadata to sample_index.csv.
```

---

## 15. Raw CSV Protection Rule

`00_raw_csv/` 中的文件是原始数据。

Codex 和 Python 脚本不允许：

1. 修改原始 CSV。
2. 重命名原始 CSV。
3. 删除原始 CSV。
4. 在原始 CSV 所在目录中写入分析结果。
5. 覆盖原始 CSV。

所有输出必须写入：

```text
04_results/run_YYYYMMDD_HHMM/
```

---

## 16. Summary

本项目中，文件身份由以下字段决定：

```text
date
experiment_id
config_group
distance_token
load_token
ground_token
block_id
sample_index
```

组统计身份由以下字段决定：

```text
config_group
distance_token
load_token
ground_token
```

所有图、表、日志和 Excel 结果必须能追溯到：

```text
file_name
file_path
file_id
group_id
run_id
```
