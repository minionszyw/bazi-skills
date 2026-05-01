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

### 安装依赖
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### CLI 排盘
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m src.cli --name 张三 --gender 1 --calendar LUNAR \
    --birth "1993-08-04 05:30:00" --location 深圳
```

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


## 📋 API 契约

### 输入模型 (`BaziRequest`)
| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `name` | str | 是 | 姓名 |
| `gender` | int | 是 | 1:男, 0:女 |
| `calendar_type` | enum | 是 | SOLAR(公历), LUNAR(农历) |
| `birth_datetime` | str | 是 | 格式: YYYY-MM-DD HH:MM:SS |
| `birth_location` | str | 是 | 深圳/西安等 (对应 `data/latlng.json`) |
| `time_mode` | enum | 否 | TRUE_SOLAR(真太阳时), MEAN_SOLAR(平太阳时) |
| `month_mode` | enum | 否 | SOLAR_TERM(节气定月), LUNAR_MONTH(农历月定月) |
| `zi_shi_mode` | enum | 否 | LATE_ZI_IN_DAY(晚子不换日), NEXT_DAY(23点换日) |

### 输出模型 (`BaziResult`)

以下为 CLI 示例的节选输出；完整样例见 `tests/bazi.json`。

```json
{
  "processed_at": "2026-05-01 13:14:33",
  "request": {
    "name": "张三",
    "gender": 1,
    "calendar_type": "LUNAR",
    "birth_datetime": "1993-08-04 05:30:00",
    "birth_location": "深圳",
    "longitude": null,
    "time_mode": "TRUE_SOLAR",
    "month_mode": "SOLAR_TERM",
    "zi_shi_mode": "LATE_ZI_IN_DAY"
  },
  "birth_solar_datetime": "1993-09-19 05:13:18 星期日",
  "birth_lunar_datetime": "一九九三年八月初四 癸酉(鸡)年 辛酉(鸡)月 癸卯(兔)日 卯(兔)时 ...",
  "core": {
    "year": {
      "gan": "癸",
      "zhi": "酉",
      "shi_shen_gan": "比肩",
      "shi_shen_zhi": ["偏印"],
      "hide_gan": ["辛"],
      "na_yin": "剑锋金",
      "xun_kong": ["戌", "亥"]
    },
    "month": { "gan": "辛", "zhi": "酉", "...": "..." },
    "day": { "gan": "癸", "zhi": "卯", "...": "..." },
    "time": { "gan": "乙", "zhi": "卯", "...": "..." },
    "jie_qi": {
      "prev_name": "白露",
      "prev_jie": "1993-09-07 23:07:47 星期二",
      "next_name": "寒露",
      "next_jie": "1993-10-08 14:40:02 星期五"
    }
  },
  "fortune": {
    "start_solar": "1997-06-29 05:13:18 星期日",
    "start_age": 5,
    "da_yun": [
      { "index": 1, "start_year": 1997, "start_age": 5, "gan_zhi": "庚申", "xun": "甲寅", "xiao_yun": [] }
    ],
    "before_start_xiao_yun": [
      { "index": 0, "gan_zhi": "甲寅" },
      { "...": "..." }
    ],
    "query": null
  },
  "auxiliary": {
    "year_di_shi": "病", "month_di_shi": "病", "day_di_shi": "长生", "time_di_shi": "长生",
    "tai_yuan": "壬子", "tai_yuan_na_yin": "桑柘木",
    "ming_gong": "丁巳", "ming_gong_na_yin": "沙中土",
    "shen_gong": "乙丑", "shen_gong_na_yin": "海中金"
  },
  "month_command": { "current": "辛", "detail": "处于辛司权第12天 (真气引出)" },
  "five_elements": {
    "scores": { "木": 42.5, "火": 0.0, "土": 0.0, "金": 210.6, "水": 16.5 },
    "states": { "木": "胎", "火": "死", "土": "死", "金": "帝旺", "水": "沐浴" }
  },
  "interactions": [
    { "type": "冲", "source": "月干", "target": "时干", "is_transformed": false, "transformed_to": null, "desc": "辛乙相冲" },
    { "type": "冲", "source": "年支", "target": "日支", "is_transformed": false, "transformed_to": null, "desc": "酉卯相冲" }
  ],
  "geju": { "name": "偏印格", "type": "正八格", "status": "成格", "detail": "标准正八格取法" },
  "analysis": { "strength_level": "极强", "strength_score": 84.24, "yong_shen": "土", "xi_shen": "火", "ji_shen": "金", "chou_shen": "水", "logic_type": "扶抑平衡" },
  "stars": [
    { "name": "天乙贵人", "pos": "日柱", "desc": "玉堂金马，逢凶化吉" },
    { "name": "文昌贵人", "pos": "日柱", "desc": "聪明好学，文艺秀发" },
    { "name": "禄神", "pos": "年柱", "desc": "辛禄在酉" }
  ]
}
```

传入 `--date` 时，`fortune.query` 返回该日期的完整运程上下文：

```json
"query": {
  "date": "2030-03-15",
  "da_yun":   { "gan_zhi": "丁巳", "start_year": 2027, "start_age": 35 },
  "liu_nian": { "year": 2030, "gan_zhi": "庚戌", "xun": "甲辰" },
  "liu_yue":  { "month": 3, "gan_zhi": "己卯" },
  "liu_ri":   { "day": 15, "gan_zhi": "己酉" }
}
```

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
