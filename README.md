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
*   **逻辑轨迹审计**：每一项命理判定均附带 `Calculation Trace`，逻辑透明可追溯。
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
python3 -m src.cli --name 张三 --gender 1 --calendar SOLAR \
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

### 输出模型 (`BaziResult`) - 核心字段
```json
{
  "request": { ... },
  "birth_solar_datetime": "校正后的公历时刻",
  "core": { "year": { "gan": "庚", "zhi": "午", "na_yin": "路旁土", ... }, ... },
  "geju": { "name": "伤官佩印", "status": "成格", ... },
  "analysis": { "strength_level": "身弱", "yong_shen": "火", ... },
  "stars": [ { "name": "天乙贵人", "pos": "日柱" }, ... ],
  "analysis_trace": [ "算法逻辑每一步推导的详情..." ]
}
```

## 🧪 质量保证
项目包含 50 例基于《千里命稿》和《渊海子平》的黄金回归测试集，确保核心逻辑永不退化。
```bash
pytest tests/supreme_audit.py
```

## ⚖️ 命理标准
本引擎算法主要参考以下经典：
*   《渊海子平》 (明·徐大升 著)
*   《千里命稿》 (韦千里 著)
