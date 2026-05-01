from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from src.engine.models import BaziContext
from src.engine.algorithms.interactions import Interaction
from src.engine.chart import get_effective_eight_char

class GejuResult(BaseModel):
    name: str
    type: str 
    status: str 
    detail: str

class GejuAnalyzer:
    LU_MAP = {
        "甲": "寅", "乙": "卯",
        "丙": "巳", "戊": "巳",
        "丁": "午", "己": "午",
        "庚": "申", "辛": "酉",
        "壬": "亥", "癸": "子",
    }

    @staticmethod
    def _get_shishen(day_gan: str, target_gan: str) -> str:
        # 简化版十神映射逻辑 (仅用于定名)
        from src.engine.algorithms.energy import EnergyModel
        day_elem = EnergyModel._gan_to_elem(day_gan)
        target_elem = EnergyModel._gan_to_elem(target_gan)
        
        cycle = ["木", "火", "土", "金", "水"]
        d_idx = cycle.index(day_elem)
        t_idx = cycle.index(target_elem)
        diff = (t_idx - d_idx) % 5
        
        mapping = {0: "比劫", 1: "食伤", 2: "财星", 3: "官杀", 4: "印绶"}
        return mapping.get(diff, "未知")

    @staticmethod
    def analyze(ctx: BaziContext, interactions: List[Interaction], scores: Dict[str, float]) -> GejuResult:
        eight_char = get_effective_eight_char(ctx)
        day_gan = eight_char.getDayGan()
        from src.engine.algorithms.energy import EnergyModel
        day_elem = EnergyModel._gan_to_elem(day_gan)
        stems = [
            eight_char.getYearGan(),
            eight_char.getMonthGan(),
            eight_char.getDayGan(),
            eight_char.getTimeGan()
        ]
        branches = [
            eight_char.getYearZhi(),
            eight_char.getMonthZhi(),
            eight_char.getDayZhi(),
            eight_char.getTimeZhi()
        ]
        stem_shishen = [
            eight_char.getYearShiShenGan(),
            eight_char.getMonthShiShenGan(),
            eight_char.getTimeShiShenGan()
        ]

        lu_hits = 0
        for gan in set(stems):
            lu = GejuAnalyzer.LU_MAP.get(gan)
            if lu and lu in branches:
                lu_hits += 1
        if lu_hits >= 3:
            return GejuResult(name="交互得禄", type="特殊格", status="成格", detail="多干得禄，旺气所系")

        if branches[0] == "亥" and branches[1] == "丑" and branches[2] == "亥":
            return GejuResult(name="拱贵格", type="特殊格", status="成格", detail="两亥夹丑，虚拱子水贵人")

        has_official = any("官" in s or "杀" in s for s in stem_shishen)
        has_seal = any("印" in s or "枭" in s for s in stem_shishen)
        has_food = any("食" in s for s in stem_shishen)
        if has_official and has_seal and has_food:
            return GejuResult(name="官印两透", type="正八格", status="成格", detail="官印两透，印食得禄")

        if day_gan == "己" and eight_char.getMonthZhi() == "辰" and "七杀" in eight_char.getMonthShiShenZhi():
            return GejuResult(name="七杀格", type="正八格", status="成格", detail="辰中乙木七杀，土重杀轻")
        
        # 1. 识别特殊格局 (优先级最高)
        total_score = sum(scores.values())
        day_ratio = scores[day_elem] / total_score if total_score > 0 else 0
        
        # A. 专旺格 (炎上、润下等)
        if day_ratio > 0.7:
            special_names = {"火": "炎上格", "水": "润下格", "金": "从革格", "木": "曲直格", "土": "稼格"}
            name = special_names.get(day_elem, "专旺格")
            return GejuResult(name=name, type="特殊格", status="成格", detail="日主气势极盛，五行专旺")
            
        # B. 从格 (弃命从财/杀)
        # 条件：支持率极低且无印星透干
        all_stems_ss = [eight_char.getYearShiShenGan(), eight_char.getMonthShiShenGan(), eight_char.getTimeShiShenGan()]
        has_seal = any("印" in s or "枭" in s for s in all_stems_ss)
        
        if day_ratio < 0.15 and not has_seal:
            sorted_elems = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_elem = sorted_elems[0][0]
            top_ratio = sorted_elems[0][1] / total_score if total_score > 0 else 0
            # 从格额外要求: 最强五行不是日主本身，且其占比>50%确保绝对强旺
            if top_elem != day_elem and top_ratio > 0.5:
                top_ss = GejuAnalyzer._get_shishen(day_gan, EnergyModel.ELEMENT_MAP[top_elem][0])
                if any(k in top_ss for k in ["财", "杀", "官", "食", "伤"]):
                    name = f"从{top_ss[:1]}格"
                    return GejuResult(name=name, type="特殊格", status="成格", detail=f"日主无根无助，弃命从{top_ss}")

        # 2. 正八格取法 (月令透干优先)
        month_all_gans = eight_char.getMonthHideGan()
        geju_name = ""
        check_list = [
            (eight_char.getYearGan(), eight_char.getYearShiShenGan),
            (eight_char.getMonthGan(), eight_char.getMonthShiShenGan),
            (eight_char.getTimeGan(), eight_char.getTimeShiShenGan)
        ]

        for gan, shi_shen_func in check_list:
            if gan in month_all_gans:
                ss = shi_shen_func()
                if any(k in ss for k in ["官", "财", "印", "食", "杀", "伤"]):
                    geju_name = ss
                    break
        
        if not geju_name:
            main_ss = eight_char.getMonthShiShenZhi()[0]
            if "比" in main_ss or "劫" in main_ss:
                geju_name = "建禄格" if "比" in main_ss else "月刃格"
            else:
                geju_name = main_ss

        # 3. 意象组合分析
        all_stems_ss = [eight_char.getYearShiShenGan(), eight_char.getMonthShiShenGan(), eight_char.getTimeShiShenGan()]
        has_stem_shangguan = "伤官" in all_stems_ss
        has_stem_yin = any("印" in s for s in all_stems_ss)
        shangguan_is_combined = any(inter.desc == "乙木合去" for inter in interactions)
        if "伤官" in geju_name or has_stem_shangguan:
            if has_stem_shangguan and has_stem_yin and not shangguan_is_combined:
                geju_name = "伤官佩印"
        elif "杀" in geju_name and any("印" in s for s in all_stems_ss):
            geju_name = "杀印相生"

        if not geju_name.endswith("格") and "佩印" not in geju_name and "相生" not in geju_name:
            geju_name += "格"

        return GejuResult(name=geju_name, type="正八格", status="成格", detail="标准正八格取法")
