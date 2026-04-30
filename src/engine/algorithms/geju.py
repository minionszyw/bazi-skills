from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from src.engine.preprocessor import BaziContext
from src.engine.utils import Tracer
from src.engine.algorithms.interactions import Interaction

class GejuResult(BaseModel):
    name: str
    type: str 
    status: str 
    detail: str

class GejuAnalyzer:
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
    def analyze(ctx: BaziContext, interactions: List[Interaction], scores: Dict[str, float], tracer: Tracer = None) -> GejuResult:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        day_gan = eight_char.getDayGan()
        from src.engine.algorithms.energy import EnergyModel
        day_elem = EnergyModel._gan_to_elem(day_gan)
        
        # 1. 识别特殊格局 (优先级最高)
        total_score = sum(scores.values())
        day_ratio = scores[day_elem] / total_score if total_score > 0 else 0
        
        # A. 专旺格 (炎上、润下等)
        if day_ratio > 0.7:
            special_names = {"火": "炎上格", "水": "润下格", "金": "从革格", "木": "曲直格", "土": "稼格"}
            name = special_names.get(day_elem, "专旺格")
            return GejuResult(name=name, type="SPECIAL", status="成格", detail="日主气势极盛，五行专旺")
            
        # B. 从格 (弃命从财/杀)
        # 条件：支持率极低且无印星透干
        all_stems_ss = [eight_char.getYearShiShenGan(), eight_char.getMonthShiShenGan(), eight_char.getTimeShiShenGan()]
        has_seal = any("印" in s or "枭" in s for s in all_stems_ss)
        
        if day_ratio < 0.15 and not has_seal:
            # 找到最强五行并转化为十神定名
            sorted_elems = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_elem = sorted_elems[0][0]
            # 获取最强五行对日主的十神名
            top_ss = GejuAnalyzer._get_shishen(day_gan, EnergyModel.ELEMENT_MAP[top_elem][0])
            
            if any(k in top_ss for k in ["财", "杀", "官", "食", "伤"]):
                name = f"从{top_ss[:1]}格" # 如 从财格, 从杀格
                return GejuResult(name=name, type="SPECIAL", status="成格", detail=f"日主无根无助，弃命从{top_ss}")

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
        if "伤官" in geju_name or "伤官" in all_stems_ss:
            if any("印" in s for s in all_stems_ss): geju_name = "伤官佩印"
        elif "杀" in geju_name and any("印" in s for s in all_stems_ss):
            geju_name = "杀印相生"

        if not geju_name.endswith("格") and "佩印" not in geju_name and "相生" not in geju_name:
            geju_name += "格"

        return GejuResult(name=geju_name, type="INNER_EIGHT", status="成格", detail="标准正八格取法")