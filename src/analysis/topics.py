from dataclasses import dataclass
from typing import Any

from src.analysis.context import build_context


SUPPORTED_TOPICS = (
    "overall",
    "career",
    "wealth",
    "marriage",
    "health",
    "study",
    "parents",
    "children",
    "siblings",
    "social",
    "remedy",
)
TOPIC_TITLES = {
    "overall": "原命局总论",
    "career": "事业分析",
    "wealth": "财运分析",
    "marriage": "婚姻分析",
    "health": "健康分析",
    "study": "学业分析",
    "parents": "父母缘分析",
    "children": "子女缘分析",
    "siblings": "兄弟朋友分析",
    "social": "人际合作分析",
    "remedy": "趋避建议",
}


@dataclass(frozen=True)
class StepTemplate:
    name: str
    method: str
    kind: str


TOPIC_STEPS = {
    "overall": [
        StepTemplate("定四柱提纲", "以日主为核心，以月令为提纲，先看命局气势来源。", "foundation"),
        StepTemplate("定日主旺衰", "结合月令、通根、透干、生扶克泄耗判断日主强弱。", "strength"),
        StepTemplate("取用喜忌", "身强宜克泄耗，身弱宜生扶；再结合格局病药取用。", "useful_gods"),
        StepTemplate("看格局成败", "先看格局名称与成败，再看是否清纯、有无破格。", "geju"),
        StepTemplate("看组合冲合", "观察天干地支冲合刑害对格局、用神和宫位的影响。", "interactions"),
        StepTemplate("观运限承接", "以大运流年是否扶起喜用、触动忌神来判断阶段变化。", "fortune"),
    ],
    "career": [
        StepTemplate("定事业主轴", "先看格局与用神，确定事业判断的主轴。", "geju"),
        StepTemplate("看官杀印星", "官杀主规则职位，印星主资质文凭与承载，重在是否为喜用。", "official"),
        StepTemplate("看食伤才华", "食伤主表达、技术、产出，也要看是否泄秀或伤官见官。", "output"),
        StepTemplate("看运限承接", "事业成败常在大运流年引动喜用或冲破原局时显现。", "fortune"),
    ],
    "wealth": [
        StepTemplate("定位财星", "财星代表资源、经营、收益，先看是否出现、是否得力。", "wealth"),
        StepTemplate("判断身财关系", "身强能任财，身弱财多反成压力；需结合旺衰与用忌。", "strength"),
        StepTemplate("看食伤生财", "食伤能生财，代表以技能、产出、经营路径求财。", "output"),
        StepTemplate("看比劫夺财", "比劫旺时需防竞争、分利、冲动投资。", "peers"),
        StepTemplate("看运限财机", "财运重在大运流年是否引动财星与喜用。", "fortune"),
    ],
    "marriage": [
        StepTemplate("定位配偶星", "男命以财星为配偶星，女命以官杀为配偶星，同时看喜忌。", "spouse_star"),
        StepTemplate("看夫妻宫", "日支为夫妻宫，看其十神、喜忌与是否受冲合刑害。", "spouse_palace"),
        StepTemplate("看宫星关系", "配偶星与夫妻宫同看，忌星或受伤时需谨慎判断。", "spouse_relation"),
        StepTemplate("看运限触发", "婚恋应期常由大运流年触动配偶星或夫妻宫。", "fortune"),
    ],
    "health": [
        StepTemplate("看五行偏枯", "健康类判断先看五行是否偏旺偏弱，偏枯处只作风险提示。", "health_balance"),
        StepTemplate("看寒燥湿热", "结合月令季节与命局气势，看是否需要调候。", "climate"),
        StepTemplate("看冲刑伤动", "冲刑多见时，关注被冲宫位、五行和运限触发。", "interactions"),
        StepTemplate("看运限触发", "健康风险不凭原局单断，需看大运流年是否加重偏枯或冲刑。", "fortune"),
    ],
    "study": [
        StepTemplate("看印星资质", "印星主学习、吸收、文凭、师承，先看是否为喜用。", "study_print"),
        StepTemplate("看食伤表达", "食伤主理解输出、技艺表达，与考试、作品、表达能力相关。", "output"),
        StepTemplate("看文昌贵人", "文昌等神煞只作辅助，不替代格局与喜用判断。", "study_stars"),
        StepTemplate("看运限助学", "学业阶段重看印星、食伤、喜用是否被运限扶起。", "fortune"),
    ],
    "parents": [
        StepTemplate("看父母星", "古法多以财印参看父母，需结合性别、宫位与喜忌。", "parents_star"),
        StepTemplate("看年柱月柱", "年柱、月柱为祖上父母早年环境的重要参考。", "parents_palace"),
        StepTemplate("看财印受伤", "财印被冲克或为忌时，父母缘与助力需谨慎判断。", "parents_relation"),
        StepTemplate("看运限分离", "迁移、离家、亲缘变化常由运限冲动年/月柱或财印引发。", "fortune"),
    ],
    "children": [
        StepTemplate("看子女星", "男命多看官杀，女命多看食伤，同时结合喜忌。", "children_star"),
        StepTemplate("看时柱子女宫", "时柱为子女宫，重点看时干时支十神与冲合刑害。", "children_palace"),
        StepTemplate("看子女星受制", "子女星或子女宫受冲克时，只作缘分、操心程度与阶段提示。", "children_relation"),
        StepTemplate("看运限引动", "子女缘应期需看运限是否触动子女星或时柱。", "fortune"),
    ],
    "siblings": [
        StepTemplate("看比劫同类", "比肩劫财主同辈、竞争、朋友、兄弟姐妹。", "peers"),
        StepTemplate("看比劫喜忌", "比劫为喜则多助力，为忌则多竞争分夺。", "siblings_relation"),
        StepTemplate("看组合冲合", "同辈关系也受冲合刑害影响，需结合宫位与运限。", "interactions"),
        StepTemplate("看运限变化", "同辈合作与竞争常随大运流年引动比劫而变化。", "fortune"),
    ],
    "social": [
        StepTemplate("看官杀边界", "官杀代表规则、压力、外部评价与组织关系。", "official"),
        StepTemplate("看比劫合作", "比劫代表同辈、团队、竞争和资源分配。", "peers"),
        StepTemplate("看食伤表达", "食伤代表表达方式、说服力与对规则的冲击。", "output"),
        StepTemplate("看财星资源", "财星代表资源交换、利益关系与经营能力。", "wealth"),
    ],
    "remedy": [
        StepTemplate("确定喜忌方向", "以用神、喜神、忌神为趋避依据，不作绝对化承诺。", "useful_gods"),
        StepTemplate("匹配现实场景", "把五行喜忌转为行业、环境、节奏、合作方式等现实建议。", "remedy_scene"),
        StepTemplate("避开忌神模式", "忌神代表失衡来源，建议减少对应的行为与环境暴露。", "remedy_avoid"),
        StepTemplate("结合运限取舍", "当前运限顺喜用则进取，触忌神则保守修正。", "fortune"),
    ],
}


TEN_GOD_QUERIES = {
    "正官": ["正官", "官星", "财官"],
    "七杀": ["偏官", "七杀", "杀印相生"],
    "偏官": ["偏官", "七杀", "杀印相生"],
    "正印": ["印绶", "正印", "官印"],
    "偏印": ["印绶", "偏印", "枭神"],
    "食神": ["食神", "食神生财"],
    "伤官": ["伤官", "伤官见官", "伤官生财"],
    "正财": ["正财", "财星", "财官"],
    "偏财": ["偏财", "财星", "财多"],
    "比肩": ["比肩", "比劫", "分财"],
    "劫财": ["劫财", "比劫", "夺财"],
}

FIVE_ELEMENT_SCENES = {
    "木": "宜重视成长、规划、学习、协作与长期建设。",
    "火": "宜重视表达、传播、曝光、审美、礼仪与行动节奏。",
    "土": "宜重视规则、责任、稳定、管理、信用与承载。",
    "金": "宜重视制度、技术、决断、边界、金融与精细化。",
    "水": "宜重视流通、信息、研究、迁移、沟通与弹性。",
}


def analyze_chart(chart: dict[str, Any], topic: str = "overall") -> dict[str, Any]:
    if topic not in SUPPORTED_TOPICS:
        raise ValueError(f"不支持的 topic：{topic}，可选：{', '.join(SUPPORTED_TOPICS)}")

    ctx = build_context(chart)
    steps = [_build_step(ctx, step) for step in TOPIC_STEPS[topic]]
    query_layers = _query_layers(topic, steps)
    queries = _dedupe(query for step in steps for query in step["search_queries"])

    return {
        "topic": topic,
        "title": TOPIC_TITLES[topic],
        "chart_summary": _chart_summary(ctx),
        "steps": steps,
        "search_query_layers": query_layers,
        "search_queries": queries,
        "notes": [
            "本结果是命理分析流程，不是确定性预测。",
            "古籍原文应作为判断依据之一，最终回复需结合用户具体问题与现实背景。",
        ],
    }


def _build_step(ctx: dict[str, Any], template: StepTemplate) -> dict[str, Any]:
    inputs = _inputs_for(ctx, template.kind)
    conclusion = _conclusion_for(ctx, template.kind)
    return {
        "name": template.name,
        "method": template.method,
        "kind": template.kind,
        "inputs": inputs,
        "conclusion": conclusion,
        "search_queries": _queries_for(ctx, template.kind),
    }


def _query_layers(topic: str, steps: list[dict[str, Any]]) -> dict[str, list[str]]:
    required_kinds = {"foundation", "strength", "useful_gods", "geju"}
    common_optional_kinds = {"interactions", "fortune"}
    required = []
    topic_specific = []
    optional = []

    for step in steps:
        kind = step.get("kind")
        queries = step.get("search_queries", [])
        if kind in required_kinds:
            required.extend(queries[:3])
            optional.extend(queries[3:])
        elif topic != "overall" and kind not in common_optional_kinds:
            topic_specific.extend(queries[:5])
            optional.extend(queries[5:])
        else:
            optional.extend(queries)

    return {
        "required": _dedupe(required),
        "topic_specific": _dedupe(topic_specific),
        "optional": _dedupe(optional),
    }


def _chart_summary(ctx: dict[str, Any]) -> dict[str, Any]:
    pillars = ctx["pillars"]
    useful = ctx["useful_gods"]
    return {
        "name": ctx.get("name"),
        "four_pillars": {
            "year": pillars["year"]["gan_zhi"],
            "month": pillars["month"]["gan_zhi"],
            "day": pillars["day"]["gan_zhi"],
            "time": pillars["time"]["gan_zhi"],
        },
        "day_master": ctx.get("day_master"),
        "month_branch": ctx.get("month_branch"),
        "geju": ctx["geju"],
        "strength": ctx["strength"],
        "useful_gods": useful,
        "key_interactions": ctx["interactions"][:5],
        "key_stars": ctx["stars"][:5],
    }


def _inputs_for(ctx: dict[str, Any], kind: str) -> list[str]:
    pillars = ctx["pillars"]
    useful = ctx["useful_gods"]
    ten_gods = ctx["ten_gods"]
    common = {
        "foundation": [
            f"日主：{ctx.get('day_master')}",
            f"月令：{ctx.get('month_branch')}",
            f"四柱：{pillars['year']['gan_zhi']}、{pillars['month']['gan_zhi']}、{pillars['day']['gan_zhi']}、{pillars['time']['gan_zhi']}",
        ],
        "strength": [
            f"旺衰：{ctx['strength'].get('level')}",
            f"强弱分：{ctx['strength'].get('score')}",
            f"分析逻辑：{ctx['strength'].get('logic_type')}",
        ],
        "useful_gods": [
            f"用神：{useful.get('yong_shen')}",
            f"喜神：{useful.get('xi_shen')}",
            f"忌神：{useful.get('ji_shen')}",
            f"仇神：{useful.get('chou_shen')}",
        ],
        "geju": [
            f"格局：{ctx['geju'].get('name')}",
            f"类型：{ctx['geju'].get('type')}",
            f"状态：{ctx['geju'].get('status')}",
            f"说明：{ctx['geju'].get('detail')}",
        ],
        "interactions": ctx["interactions"][:8] or ["未见明显冲合刑害输出"],
        "fortune": _fortune_inputs(ctx),
        "official": _ten_god_inputs(ten_gods, ["正官", "七杀", "偏官", "正印", "偏印"]),
        "output": _ten_god_inputs(ten_gods, ["食神", "伤官"]),
        "wealth": _ten_god_inputs(ten_gods, ["正财", "偏财"]),
        "peers": _ten_god_inputs(ten_gods, ["比肩", "劫财"]),
        "spouse_star": _spouse_star_inputs(ctx),
        "spouse_palace": [
            f"日支夫妻宫：{pillars['day']['zhi']}",
            f"夫妻宫藏干十神：{'、'.join(pillars['day']['shi_shen_zhi']) or '未标注'}",
        ],
        "spouse_relation": _spouse_star_inputs(ctx) + ctx["interactions"][:5],
        "health_balance": _health_balance_inputs(ctx),
        "climate": _climate_inputs(ctx),
        "study_print": _ten_god_inputs(ten_gods, ["正印", "偏印"]),
        "study_stars": _star_inputs(ctx, ["文昌贵人", "天乙贵人", "学堂", "词馆"]),
        "parents_star": _ten_god_inputs(ten_gods, ["正印", "偏印", "正财", "偏财"]),
        "parents_palace": [
            f"年柱：{pillars['year']['gan_zhi']}，天干十神：{pillars['year']['shi_shen_gan']}，地支十神：{'、'.join(pillars['year']['shi_shen_zhi']) or '未标注'}",
            f"月柱：{pillars['month']['gan_zhi']}，天干十神：{pillars['month']['shi_shen_gan']}，地支十神：{'、'.join(pillars['month']['shi_shen_zhi']) or '未标注'}",
        ],
        "parents_relation": _ten_god_inputs(ten_gods, ["正印", "偏印", "正财", "偏财"]) + ctx["interactions"][:5],
        "children_star": _children_star_inputs(ctx),
        "children_palace": [
            f"时柱子女宫：{pillars['time']['gan_zhi']}",
            f"时干十神：{pillars['time']['shi_shen_gan']}",
            f"时支藏干十神：{'、'.join(pillars['time']['shi_shen_zhi']) or '未标注'}",
        ],
        "children_relation": _children_star_inputs(ctx) + ctx["interactions"][:5],
        "siblings_relation": _ten_god_inputs(ten_gods, ["比肩", "劫财"]) + [
            f"比劫对当前命局的影响需结合用神 {useful.get('yong_shen')} 与忌神 {useful.get('ji_shen')} 判断。"
        ],
        "remedy_scene": [
            f"用神：{useful.get('yong_shen')}",
            f"喜神：{useful.get('xi_shen')}",
            _scene_for(useful.get("yong_shen")),
            _scene_for(useful.get("xi_shen")),
        ],
        "remedy_avoid": [
            f"忌神：{useful.get('ji_shen')}",
            f"仇神：{useful.get('chou_shen')}",
            f"减少{useful.get('ji_shen') or '忌神'}过旺所代表的失衡模式。",
        ],
    }
    return [item for item in common.get(kind, []) if item]


def _conclusion_for(ctx: dict[str, Any], kind: str) -> str:
    useful = ctx["useful_gods"]
    geju = ctx["geju"]
    strength = ctx["strength"]
    ten_gods = ctx["ten_gods"]

    if kind == "foundation":
        return f"以{ctx.get('day_master')}日为命主，以{ctx.get('month_branch')}月令为提纲展开判断。"
    if kind == "strength":
        return f"排盘层判为{strength.get('level')}，后续以该旺衰结论校验取用与专题判断。"
    if kind == "useful_gods":
        return f"以{useful.get('yong_shen')}为用，{useful.get('xi_shen')}为喜；分析时优先看喜用是否得力。"
    if kind == "geju":
        return f"当前格局为{geju.get('name')}，状态为{geju.get('status')}，需看是否被冲合刑害或运限破坏。"
    if kind == "interactions":
        return "组合关系用于判断命局是否清纯、宫位是否受动、喜忌是否被引发。"
    if kind == "fortune":
        return "大运流年不是孤立判断，需看其对原局喜用忌神的引动。"
    if kind == "official":
        return _presence_conclusion(ten_gods, ["正官", "七杀", "偏官"], "官杀")
    if kind == "output":
        return _presence_conclusion(ten_gods, ["食神", "伤官"], "食伤")
    if kind == "wealth":
        return _presence_conclusion(ten_gods, ["正财", "偏财"], "财星")
    if kind == "peers":
        return _presence_conclusion(ten_gods, ["比肩", "劫财"], "比劫")
    if kind in {"spouse_star", "spouse_relation"}:
        return "配偶星与夫妻宫需合看，不能只凭单一神煞或单一宫位下结论。"
    if kind == "spouse_palace":
        return f"日支{ctx['pillars']['day'].get('zhi')}为夫妻宫，若被冲合刑害需纳入婚恋判断。"
    if kind == "health_balance":
        return "健康专题只提示五行偏枯与作息趋避，不能替代医学诊断。"
    if kind == "climate":
        return "调候重在寒暖燥湿的平衡，需结合季节、五行气势与运限变化。"
    if kind == "study_print":
        return _presence_conclusion(ten_gods, ["正印", "偏印"], "印星")
    if kind == "study_stars":
        return "文昌、学堂等只作学习取象辅助，核心仍看印星、食伤与喜用。"
    if kind == "parents_star":
        return "父母缘以财印、年柱月柱同参，不能只凭单一十神断亲缘厚薄。"
    if kind == "parents_palace":
        return "年柱、月柱可参考早年环境与父母助力，仍需结合财印喜忌。"
    if kind == "parents_relation":
        return "财印受冲克或为忌时，多提示沟通成本、距离感或助力有限。"
    if kind == "children_star":
        return "子女星需结合性别、喜忌和时柱子女宫共同判断。"
    if kind == "children_palace":
        return "时柱为子女宫，若时柱被冲合刑害，子女缘与操心程度需纳入判断。"
    if kind == "children_relation":
        return "子女缘不作数量断语，重点看缘分深浅、互动方式与阶段触发。"
    if kind == "siblings_relation":
        return "比劫为喜多助力，为忌多竞争分夺，需结合财星和运限判断。"
    if kind == "remedy_scene":
        return "趋避建议以扶助喜用、减少忌神失衡为原则。"
    if kind == "remedy_avoid":
        return "改运类结论只作行为与环境取舍建议，不作保证性承诺。"
    return "按本步骤继续结合原文与命盘事实分析。"


def _queries_for(ctx: dict[str, Any], kind: str) -> list[str]:
    useful = ctx["useful_gods"]
    geju_name = ctx["geju"].get("name")
    base = {
        "foundation": ["月令", f"{ctx.get('day_master')}日", f"{ctx.get('month_branch')}月"],
        "strength": ["身旺", "身弱", "旺相休囚"],
        "useful_gods": ["用神", "喜忌", str(useful.get("yong_shen") or "")],
        "geju": [str(geju_name or ""), "成格", "破格"],
        "interactions": ["冲", "合", "刑害"],
        "fortune": ["大运", "流年", "岁运"],
        "official": ["正官", "偏官", "官印", "杀印相生"],
        "output": ["食神", "伤官", "食神生财", "伤官见官"],
        "wealth": ["正财", "偏财", "财星", "财官"],
        "peers": ["比肩", "劫财", "比劫夺财"],
        "spouse_star": ["财星", "官杀", "妻", "夫"],
        "spouse_palace": ["日支", "夫妻", "婚姻"],
        "spouse_relation": ["合婚", "刑冲", "夫妻"],
        "health_balance": ["五行偏枯", "疾病", "金木水火土"],
        "climate": ["调候", "寒暖燥湿", "旺相休囚"],
        "study_print": ["印绶", "文昌", "学堂", "食神"],
        "study_stars": ["文昌贵人", "学堂", "词馆"],
        "parents_star": ["印绶", "财星", "父母"],
        "parents_palace": ["年柱", "月柱", "祖业", "父母"],
        "parents_relation": ["财印", "印绶被伤", "财星有破"],
        "children_star": ["食神", "伤官", "官杀", "子息"],
        "children_palace": ["时柱", "子息", "子女"],
        "children_relation": ["食神遭刑克", "子息", "刑冲"],
        "siblings_relation": ["比肩", "劫财", "兄弟", "朋友"],
        "remedy_scene": ["用神", "喜神", str(useful.get("yong_shen") or "")],
        "remedy_avoid": ["忌神", "病药", str(useful.get("ji_shen") or "")],
    }
    queries = base.get(kind, [])
    for ten_god in ctx["ten_gods"]:
        if ten_god in TEN_GOD_QUERIES and kind in {
            "official",
            "output",
            "wealth",
            "peers",
            "geju",
            "study_print",
            "parents_star",
            "parents_relation",
            "children_star",
            "children_relation",
            "siblings_relation",
        }:
            queries.extend(TEN_GOD_QUERIES[ten_god])
    return _dedupe(query for query in queries if query and query != "None")


def _ten_god_inputs(ten_gods: dict[str, int], names: list[str]) -> list[str]:
    values = [f"{name}：{ten_gods.get(name, 0)}" for name in names]
    return values if values else ["未见对应十神统计"]


def _spouse_star_inputs(ctx: dict[str, Any]) -> list[str]:
    gender = ctx.get("gender")
    ten_gods = ctx["ten_gods"]
    if gender == 1:
        return [f"男命配偶星看财星：正财 {ten_gods.get('正财', 0)}，偏财 {ten_gods.get('偏财', 0)}"]
    if gender == 0:
        return [f"女命配偶星看官杀：正官 {ten_gods.get('正官', 0)}，七杀/偏官 {ten_gods.get('七杀', 0) + ten_gods.get('偏官', 0)}"]
    return ["性别未知，配偶星需先确认男命看财、女命看官杀。"]


def _children_star_inputs(ctx: dict[str, Any]) -> list[str]:
    gender = ctx.get("gender")
    ten_gods = ctx["ten_gods"]
    if gender == 1:
        return [f"男命子女星参考官杀：正官 {ten_gods.get('正官', 0)}，七杀/偏官 {ten_gods.get('七杀', 0) + ten_gods.get('偏官', 0)}"]
    if gender == 0:
        return [f"女命子女星参考食伤：食神 {ten_gods.get('食神', 0)}，伤官 {ten_gods.get('伤官', 0)}"]
    return ["性别未知，子女星需先确认男命看官杀、女命看食伤。"]


def _health_balance_inputs(ctx: dict[str, Any]) -> list[str]:
    scores = (ctx.get("five_elements") or {}).get("scores") or {}
    states = (ctx.get("five_elements") or {}).get("states") or {}
    items = [f"{element}：{score}（{states.get(element, '未标注')}）" for element, score in scores.items()]
    if not items:
        return ["五行分数未输出，需结合命局五行分布判断偏枯。"]
    sorted_scores = sorted(scores.items(), key=lambda item: item[1])
    weakest = sorted_scores[0][0]
    strongest = sorted_scores[-1][0]
    items.append(f"最弱五行：{weakest}")
    items.append(f"最旺五行：{strongest}")
    return items


def _climate_inputs(ctx: dict[str, Any]) -> list[str]:
    month_branch = ctx.get("month_branch")
    states = (ctx.get("five_elements") or {}).get("states") or {}
    items = [f"月令：{month_branch}"]
    if states:
        items.append("五行状态：" + "、".join(f"{key}{value}" for key, value in states.items()))
    month_command = ctx.get("month_command") or {}
    if month_command:
        items.append(f"司令：{month_command.get('current')}，{month_command.get('detail')}")
    return [item for item in items if item]


def _star_inputs(ctx: dict[str, Any], names: list[str]) -> list[str]:
    stars = ctx.get("stars") or []
    matched = [name for name in names if name in stars]
    if matched:
        return [f"命局见：{'、'.join(matched)}"]
    return [f"未见明确输出：{'、'.join(names)}"]


def _fortune_inputs(ctx: dict[str, Any]) -> list[str]:
    fortune = ctx["fortune"]
    items = [
        f"起运年龄：{fortune.get('start_age')}",
        f"起运时间：{fortune.get('start_solar')}",
    ]
    query = fortune.get("query")
    if query:
        items.extend(
            [
                f"查询日期：{query.get('date')}",
                f"大运：{(query.get('da_yun') or {}).get('gan_zhi')}",
                f"流年：{(query.get('liu_nian') or {}).get('gan_zhi')}",
                f"流月：{(query.get('liu_yue') or {}).get('gan_zhi')}",
                f"流日：{(query.get('liu_ri') or {}).get('gan_zhi')}",
            ]
        )
    else:
        da_yun = fortune.get("da_yun") or []
        if da_yun:
            items.append("大运序列：" + "、".join(item.get("gan_zhi", "") for item in da_yun[:4]))
    return [item for item in items if item]


def _presence_conclusion(ten_gods: dict[str, int], names: list[str], label: str) -> str:
    count = sum(ten_gods.get(name, 0) for name in names)
    if count:
        return f"命局见{label}，需继续判断其是否为喜用、是否透干通根、是否受冲合。"
    return f"命局中{label}不显，专题分析应更多观察藏干、宫位与运限引动。"


def _scene_for(element: Any) -> str:
    if not element:
        return ""
    text = str(element)
    for key, value in FIVE_ELEMENT_SCENES.items():
        if key in text:
            return value
    return f"{text}为喜用时，现实取象需结合行业、环境、人际与阶段运限。"


def _dedupe(items) -> list[str]:
    seen = set()
    result = []
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
