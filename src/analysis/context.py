from collections import Counter
from typing import Any


PILLARS = ("year", "month", "day", "time")
PILLAR_LABELS = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "time": "时柱",
}


def _pillar_name(pillar: dict[str, Any]) -> str:
    return f"{pillar.get('gan', '')}{pillar.get('zhi', '')}"


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_context(chart: dict[str, Any]) -> dict[str, Any]:
    core = chart.get("core", {})
    analysis = chart.get("analysis", {})
    geju = chart.get("geju", {})
    fortune = chart.get("fortune", {})

    pillars = {
        name: {
            "label": PILLAR_LABELS[name],
            "gan": core.get(name, {}).get("gan"),
            "zhi": core.get(name, {}).get("zhi"),
            "gan_zhi": _pillar_name(core.get(name, {})),
            "shi_shen_gan": core.get(name, {}).get("shi_shen_gan"),
            "shi_shen_zhi": _listify(core.get(name, {}).get("shi_shen_zhi")),
        }
        for name in PILLARS
    }

    ten_gods = Counter()
    for pillar in pillars.values():
        gan_ten_god = pillar.get("shi_shen_gan")
        if gan_ten_god and gan_ten_god != "日主":
            ten_gods[gan_ten_god] += 1
        for zhi_ten_god in pillar.get("shi_shen_zhi", []):
            if zhi_ten_god and zhi_ten_god != "日主":
                ten_gods[zhi_ten_god] += 1

    interactions = chart.get("interactions", []) or []
    stars = chart.get("stars", []) or []

    return {
        "name": chart.get("request", {}).get("name"),
        "gender": chart.get("request", {}).get("gender"),
        "pillars": pillars,
        "day_master": pillars["day"].get("gan"),
        "month_branch": pillars["month"].get("zhi"),
        "month_command": chart.get("month_command", {}),
        "ten_gods": dict(ten_gods),
        "geju": {
            "name": geju.get("name"),
            "type": geju.get("type"),
            "status": geju.get("status"),
            "detail": geju.get("detail"),
        },
        "strength": {
            "level": analysis.get("strength_level"),
            "score": analysis.get("strength_score"),
            "logic_type": analysis.get("logic_type"),
        },
        "useful_gods": {
            "yong_shen": analysis.get("yong_shen"),
            "xi_shen": analysis.get("xi_shen"),
            "ji_shen": analysis.get("ji_shen"),
            "chou_shen": analysis.get("chou_shen"),
        },
        "five_elements": chart.get("five_elements", {}),
        "interactions": [
            item.get("desc") or f"{item.get('source', '')}{item.get('type', '')}{item.get('target', '')}"
            for item in interactions
            if item
        ],
        "stars": [item.get("name") for item in stars if item.get("name")],
        "fortune": {
            "start_age": fortune.get("start_age"),
            "start_solar": fortune.get("start_solar"),
            "query": fortune.get("query"),
            "da_yun": fortune.get("da_yun", []),
        },
    }
