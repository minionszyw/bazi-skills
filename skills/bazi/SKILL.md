---
name: bazi
description: 所有命理计算、命理问题都使用这套工具链，包括八字排盘、看八字、起盘、排命盘、帮我算个命、看一下我的命、四柱查看、命理分析、八字分析、格局分析、用神喜忌、大运/流年/流月/流日查询，以及基于出生信息分析原命局、事业、财运、婚姻、健康、学业、父母/子女缘、兄弟朋友、人际合作、趋避建议、古籍依据，以及已有命盘后的后续追问（如"那婚姻呢"、"今年运势"、"再说说财运"、"如何提升财运"、"怎么化解"）。
---

# 八字命理分析

**任何命理问题，包括基于已有命盘的后续追问，必须调用 `paipan`/`analyze`/`search` 工具链，不得凭自有知识作答。**

本 skill 用于调用本地八字命理工具链，完成出生信息排盘、结构化命理分析、古籍原文检索与中文综合说明。核心 CLI 为 `paipan`、`analyze`、`search`。


## 工作流

```text
paipan -> analyze（内置 evidence） -> search（按需补充） -> 中文综合回复
```

1. 先判断用户意图：排盘、原命局总论、专题分析、运程查询、专题提升或后续追问。
2. 排盘前必须确认 `name`、`gender`、`calendar`、`birth`、`location`；缺少字段先补问，不要猜测。已有命盘时，后续专题直接复用，跳过步骤 3。
3. 信息完整后调用 `paipan`，并保存为会话内固定文件，例如 `/tmp/bazi_current_chart.json`；仅当用户问题明确涉及某个日期或时段（如"今年5月事业运"、"今天运势"）时，从问题中提取日期并传入 `--date YYYY-MM-DD`。
4. 按意图选择 `analyze --topic`：未指定用 `overall`；事业 `career`；财运 `wealth`；婚姻 `marriage`；健康 `health`；学业 `study`；父母 `parents`；子女 `children`；兄弟朋友 `siblings`；人际合作 `social`；泛化提升/改善/化解/趋避用 `remedy`。
5. 专题提升类问题使用 `remedy --focus`：提升财运用 `analyze --topic remedy --focus wealth`；提升事业用 `--focus career`；改善婚姻用 `--focus marriage`。若工具不支持对应 focus，则先跑专题 topic，再跑 `remedy`，综合回复。
6. 默认使用 `analyze` 的 `compact` 输出，优先读取 `judgement_hierarchy`、`steps` 和 `evidence`；依据不足时用 `analyze --view full` 查看 `evidence_plan`、`search_query_layers`，或按命盘核心要素调用 `search` 补充，不要只检索一次就下结论。
7. 中文回复按“命盘事实 -> 裁断主次 -> 分析步骤 -> 古籍依据 -> 白话结论 -> 注意事项”组织；古籍引用用 `《书名·篇名》：原文短句`，除非用户明确要求，不要原样粘贴完整 JSON。

## 安全调用约束

- 不要把 `paipan`、`analyze` 或 `search` 的输出管道传给 `python`、`python3`、`node`、`bash`、`sh`、`perl`、`ruby` 等解释器。
- 不要使用 heredoc 解析 JSON，例如 `python3 - <<'PY'`。
- 需要串联时，优先把 `paipan` 输出保存为 JSON 文件，再交给 `analyze --chart`。
- 需要精简结果时，使用 `analyze --view compact` 或 `analyze --format text`，不要自行写脚本抽取字段。
- 只有 `paipan | analyze --chart -` 这种 CLI 到 CLI 的直接串联可以使用；在安全策略严格的环境中，也优先使用临时文件。

## 八字排盘

用途：调用 `paipan` 生成命盘 JSON。

CLI 示例：

```bash
paipan --name "<姓名>" --gender <1|0> --calendar <SOLAR|LUNAR> \
  --birth "YYYY-MM-DD HH:MM:SS" --location "<出生地>"
```

```bash
paipan --name "<姓名>" --gender <1|0> --calendar <SOLAR|LUNAR> \
  --birth "YYYY-MM-DD HH:MM:SS" --location "<出生地>" --date "YYYY-MM-DD"
```

参数说明：

- `name`：姓名或称呼。
- `gender`：性别，男为 `1`，女为 `0`。
- `calendar`：历法，公历为 `SOLAR`，农历为 `LUNAR`。
- `birth`：出生时间，格式为 `YYYY-MM-DD HH:MM:SS`。
- `location`：出生地，例如 `深圳`、`广州市`、`天河区`。
- `--time-mode`：时间模式，默认 `TRUE_SOLAR`，可选 `MEAN_SOLAR`。
- `--month-mode`：月柱模式，默认 `SOLAR_TERM`，可选 `LUNAR_MONTH`。
- `--zi-shi-mode`：子时换日规则，默认 `LATE_ZI_IN_DAY`，可选 `NEXT_DAY`。
- `--date`：查询指定日期的流年、流月、流日，格式为 `YYYY-MM-DD`。
- `--xiao-yun`：展开小运。

缺少必填字段时，先向用户补问，不要猜测。

当用户要求查询某日运程、流年、流月或流日时，使用 `--date`。当用户明确要求展开小运时，使用 `--xiao-yun`。

## 命理分析

用途：调用 `analyze`，根据排盘 JSON 生成分析步骤、阶段结论、步骤证据计划和核心古籍依据。

CLI 示例：

```bash
paipan ... > chart.json
analyze --chart chart.json --topic career
analyze --chart chart.json --topic remedy --focus wealth
analyze --chart chart.json --topic overall --no-evidence
```

`--topic` 可选值：

| 值 | 说明 |
| :--- | :--- |
| `overall` | 原命局总论（默认；用户只说”分析八字”时使用） |
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

CLI 参数：

- `--chart`：排盘 JSON 文件路径；用 `-` 表示从 stdin 读取。
- `--topic`：分析主题，默认 `overall`。
- `--focus`：专题趋避焦点，仅与 `--topic remedy` 搭配，例如 `--focus wealth`。
- `--with-evidence`：调用 `search` 并把古籍检索结果嵌入输出，默认开启。
- `--no-evidence`：只输出分析步骤与检索词，不嵌入古籍检索结果。
- `--evidence-tier`：手动指定分层检索层级，可重复；可选 `required`、`topic_specific`、`optional`。不传时默认使用步骤证据计划。
- `--book`：古籍代号，默认 `yuanhai`。
- `--limit`：每个检索词返回条数。
- `--max-chars`：每条原文最大字符数。
- `--view`：JSON 输出视图，`compact` 或 `full`，默认 `compact`。
- `--format`：输出格式，`json` 或 `text`。

输出说明：

- `judgement_hierarchy`：主次裁断规则，用于处理格局、用神、运限、神煞等结论冲突。
- `chart_summary`：命盘摘要。
- `steps`：精简后的分析步骤、输入依据和阶段结论。
- `evidence`：默认内置的古籍检索结果。
- `--view full` 会额外输出 `steps[].method_refs`、`steps[].evidence_queries`、`evidence_plan`、`evidence_meta`、`search_query_layers`、`search_queries`，用于审计、调试和人工补充检索。

## 古籍检索

用途：调用 `search`，根据关键词检索本地古籍原文。

CLI 示例：

```bash
search "<关键词>" --book yuanhai --limit 3
search "<关键词>" --book yuanhai --limit 3 --format text
```

参数说明：

- `query`：检索词，例如 `月令`、`偏印格`、`天乙贵人`。
- `--book`：古籍代号，默认 `yuanhai`。
- `--limit`：返回条数。
- `--max-chars`：每条正文最大字符数。
- `--format`：输出格式，`json` 或 `text`。

排盘与分析后，先使用 `analyze.evidence`；必要时用 `analyze --view full` 查看 `steps[].evidence_queries` 和 `search_query_layers`，再结合命盘结果补充关键词：

- 日主、月令：如 `癸日`、`酉月`、`月令`。
- 格局、强弱：如 `偏印格`、`印绶`、`官杀混杂`。
- 用喜忌与十神：如 `正官`、`偏印`、`食神`、`财官`。
- 神煞：如 `天乙贵人`、`文昌贵人`、`禄神`。
- 干支作用：如 `相冲`、`六合`、`三合`、`刑害`。

不要只检索一次就下结论。先检查默认 evidence 是否覆盖分析步骤；仍不足时再按 `required`、`topic_specific`、`optional` 或命盘特异关键词补查 2-5 组，优先采用标题或正文直接命中的原文。

## 输出处理

CLI 默认输出 compact JSON。读取结果后直接用中文整理重点，不要再调用解释器脚本解析：

- 四柱：年柱、月柱、日柱、时柱。
- 起运：起运时间、起运年龄、大运列表。
- 格局与强弱：`geju`、`analysis.strength_level`、`analysis.strength_score`。
- 用喜忌：`yong_shen`、`xi_shen`、`ji_shen`、`chou_shen`。
- 神煞、冲合刑害等只摘要关键项，避免把完整 JSON 原样贴给用户。
- 裁断主次：按 `judgement_hierarchy` 先看日主月令、格局、用神，再看组合、运限、专题十神，神煞只作辅证。
- 分析步骤：说明 `analyze` 给出的旺衰、格局、用忌、组合、运限或专题判断链。
- 古籍依据：按 `《书名·篇名》：原文短句` 列出依据，再做白话解释。

如果用户明确要求原始数据，可以返回完整 JSON 或相关字段。

## 错误处理

- CLI 不可用时，提示用户在项目目录执行 `pip install -e .`，不要继续排盘。
- CLI 返回非零状态时，读取 stderr 中的 JSON 或错误文本，说明具体问题。
- 地名找不到时，提示用户提供更完整的出生地，或使用 CLI 支持的地名。
- 日期格式错误时，要求用户改为 `YYYY-MM-DD HH:MM:SS`。
- 古籍检索无结果时，换用更短或更通用的关键词，例如从 `偏印格` 改查 `偏印`、`印绶`。
