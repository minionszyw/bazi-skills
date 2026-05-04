# 八字排盘引擎

遵循《渊海子平》核心标准，结合现代天文精密算法构建的八字排盘分析引擎。它不仅能完成基础的干支提取，还能执行深度的命理逻辑推演。

## 🌟 核心特性

### 1. 高精度时间修正 (Phase 1)
*   **真太阳时校正**：内置均时差 (EoT) 公式与经度时差计算，消除“北京时间”与出生地实际地方时的偏差。
*   **夏令时自动处理**：精准识别 1986-1991 年间中国夏令时政策，自动回拨偏差。

### 2. 完备的数据提取 (Phase 2)
*   **核心命盘**：四柱干支、十神（天干/地支藏干）、纳音五行、每柱旬空。
*   **动态运程**：精确到分钟的起运时刻、大运流转、起运前小运展示。
*   **辅助命盘**：十二长生（地势）、胎元、命宫、身宫。

### 3. 深度自研算法 (Phase 3)
*   **月令分司用事**：根据分钟级交节深度判定司权天干，并支持“真气引出”权重逻辑。
*   **五行量化状态机**：结合“旺相休囚死”气数修正与地支通根系数的能量评分系统。
*   **严苛格局审计**：支持从格、专旺格等特殊格局识别，以及格局“成败病药”质量分析。
*   **古籍对账神煞**：严格对齐《渊海子平》标准的玉堂天乙、天月二德、咸池、截路空亡等专业神煞。

## 🚀 快速开始

### 本地安装

项目依赖统一由 `pyproject.toml` 管理。

```bash
git clone <repo-url>
cd bazi
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -e .
```

开发或运行测试时安装开发依赖：

```bash
pip install -e ".[dev]"
```

### AGENT Skill 安装

项目内置 `skills/bazi`，可复制到本地 AGENT skills 目录使用：

```bash
cp -R skills/bazi <AGENT_SKILLS_DIR>/bazi
```

使用 skill 前，AGENT 的运行环境需要能找到本项目安装后的 CLI：`paipan`、`analyze`、`search`。如果使用虚拟环境安装，请在启动 AGENT 前激活同一个 venv，或把 `venv/bin` 加入 `PATH`。

### 八字排盘

用途：生成命盘 JSON。

CLI 示例：

```bash
paipan --name 张三 --gender 1 --calendar LUNAR \
    --birth "1999-9-9 05:30:00" --location 深圳
```

参数说明：

| 参数 | 短选项 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `--name` | `-n` | 是 | 姓名 |
| `--gender` | `-g` | 是 | `1`:男  `0`:女 |
| `--calendar` | `-c` | 是 | `SOLAR`:公历  `LUNAR`:农历 |
| `--birth` | `-b` | 是 | 格式: `YYYY-MM-DD HH:MM:SS` |
| `--location` | `-l` | 是 | 出生地，支持短名（`深圳` / `广州市` / `天河区`） |
| `--time-mode` | | 否 | `TRUE_SOLAR`(默认) / `MEAN_SOLAR` |
| `--month-mode` | | 否 | `SOLAR_TERM`(默认) / `LUNAR_MONTH` |
| `--zi-shi-mode` | | 否 | `LATE_ZI_IN_DAY`(默认) / `NEXT_DAY` |
| `--date` | `-d` | 否 | 查询指定日期的流年/流月/流日，格式：`YYYY-MM-DD` |
| `--xiao-yun` | | 否 | 展开每步大运的小运列表（默认折叠） |

### 命理分析

用途：根据排盘 JSON 生成古法分析步骤、阶段结论、分层检索词与核心古籍依据。

CLI 示例：

```bash
paipan --name 张三 --gender 1 --calendar LUNAR \
    --birth "1999-9-9 05:30:00" --location 深圳 > chart.json

analyze --chart chart.json --topic overall
analyze --chart chart.json --topic career --format text
analyze --chart chart.json --topic wealth
analyze --chart chart.json --topic health
```

参数说明：

| 参数 | 必填 | 说明 |
| :--- | :--- | :--- |
| `--chart` | 否 | 排盘 JSON 文件路径，默认从 stdin 读取；用 `-` 表示 stdin |
| `--topic` | 否 | 分析主题，默认 `overall` |
| `--with-evidence` | 否 | 调用 `search` 并嵌入古籍依据，默认开启 |
| `--no-evidence` | 否 | 只输出分析步骤与检索词，不嵌入古籍依据 |
| `--evidence-tier` | 否 | evidence 检索层级，可重复；可选 `required`、`topic_specific`、`optional` |
| `--book` | 否 | 古籍代号，默认 `yuanhai` |
| `--limit` | 否 | 每个检索词返回条数，默认 `2` |
| `--max-chars` | 否 | 每条原文最大字符数，默认 `260` |
| `--format` | 否 | 输出格式：`json` / `text` |

`analyze` 默认会对核心分层检索词调用 `search`，并在输出中附加 `evidence`。如果只需要分析步骤和检索词，可使用：

```bash
analyze --chart chart.json --topic overall --no-evidence
```

当前支持的主题：

| 主题 | 说明 |
| :--- | :--- |
| `overall` | 原命局总论 |
| `career` | 事业分析 |
| `wealth` | 财运分析 |
| `marriage` | 婚姻分析 |
| `health` | 健康分析 |
| `study` | 学业分析 |
| `parents` | 父母缘分析 |
| `children` | 子女缘分析 |
| `siblings` | 兄弟朋友分析 |
| `social` | 人际合作分析 |
| `remedy` | 趋避建议 |

### 古籍检索

用途：检索本地古籍原文，适合在排盘后根据命盘要素主动查找依据。当前内置 `yuanhai`（《渊海子平》）语料。

CLI 示例：

```bash
search "月令" --book yuanhai --limit 3 --format text
search "天乙贵人" --book yuanhai --limit 3
```

参数说明：

| 参数 | 必填 | 说明 |
| :--- | :--- | :--- |
| `query` | 是 | 检索词，例如 `月令`、`偏印格`、`天乙贵人` |
| `--book` | 否 | 古籍代号，默认 `yuanhai` |
| `--limit` | 否 | 返回条数，默认 `5` |
| `--max-chars` | 否 | 每条正文最大字符数，默认 `500` |
| `--format` | 否 | 输出格式：`json` / `text` |

典型流程：

```text
获取命主出生信息 -> paipan 排盘 -> analyze 生成分析步骤、分层检索词与核心 evidence -> search 按需补充古籍原文 -> 综合中文回复
```

`analyze` 输出会为每个步骤附加 `steps[].method_refs`，用于查看该步骤绑定的古籍方法来源、方法原则和对账检索词；同时保留扁平 `search_queries` 和分层 `search_query_layers`：

| 层级 | 用途 |
| :--- | :--- |
| `required` | 月令、日主、旺衰、用神、格局等核心依据 |
| `topic_specific` | 事业、财运、婚姻、健康等专题依据 |
| `optional` | 冲合刑害、大运流年等补充依据 |

综合回复引用古籍时，建议固定为 `《书名·篇名》：原文短句`，再接白话解释。

## 🧪 质量保证
项目包含 50 例基于《千里命稿》的黄金审计测试集：8 例端到端排盘命例，42 例古籍四柱直测命例。`expected` 字段以古籍原文为准；古籍没有明确标注的字段保留为 `古籍未标注`，不计入对应字段覆盖率。

```bash
PYTHONPATH=. python3 -m pytest -q
```

当前完整审计结果：

| 审计项 | 准确率 | 覆盖率 |
| --- | ---: | ---: |
| 基础干支 | 100.0% (50/50) | 100.0% (50/50) |
| 格局判定 | 100.0% (50/50) | 100.0% (50/50) |
| 强弱判定 | 100.0% (40/40) | 80.0% (40/50) |
| 用神判定 | 100.0% (36/36) | 72.0% (36/50) |
| 干支作用 | 100.0% (16/16) | 32.0% (16/50) |
| 神煞判定 | 100.0% (8/8) | 16.0% (8/50) |
| 全字段通过 | 100.0% (50/50) | 100.0% (50/50) |

`pytest` 会执行古籍 expected 与排盘引擎输出的全字段断言，用于防止基础排盘、格局、强弱和用神算法回退。

如需查看审计报告而不是执行断言测试：

```bash
PYTHONPATH=. python3 tests/supreme_audit.py
```

## ⚖️ 命理标准
本引擎算法主要参考以下经典：
*   《渊海子平》 (明·徐大升 著)
*   《千里命稿》 (韦千里 著)
