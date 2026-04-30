from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel
from src.engine.preprocessor import BaziContext
from src.engine.utils import Tracer

class Interaction(BaseModel):
    type: str        # 合, 冲, 刑, 害, 破, 会, 伏吟, 反吟
    source: str      # 位置 (年, 月, 日, 时, 运, 年)
    target: str
    is_transformed: bool = False # 是否化气成功
    transformed_to: Optional[str] = None # 化出的五行
    desc: str

class InteractionDetector:
    """
    干支作用关系检测器 (基于《渊海子平》)
    """
    
    # 十天干合化定义
    STEM_COMBINATIONS = {
        ("甲", "己"): "土",
        ("乙", "庚"): "金",
        ("丙", "辛"): "水",
        ("丁", "壬"): "木",
        ("戊", "癸"): "火"
    }
    
    # 地支六冲
    BRANCH_CLASHES = {
        "子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌", "巳": "亥"
    }
    
    # 地支三刑 (简化逻辑)
    BRANCH_PUNISHMENTS = {
        ("寅", "巳", "申"): "无恩之刑",
        ("未", "丑", "戌"): "持势之刑",
        ("子", "卯"): "无礼之刑"
    }

    @staticmethod
    def validate_transformations(interactions: List[Interaction], ctx: BaziContext, tracer: Tracer = None):
        """
        根据《渊海子平》标准校验合化是否成功
        """
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        month_zhi = eight_char.getMonthZhi()
        
        # 获取原局所有天干
        all_stems = [eight_char.getYearGan(), eight_char.getMonthGan(), eight_char.getDayGan(), eight_char.getTimeGan()]
        
        for inter in interactions:
            if inter.type == "合" and inter.transformed_to:
                # 校验条件 1: 天干引化 (化神必须在天干透出)
                # 考虑到日干通常作为合化主体，我们检查是否有除了合化双方之外的同类五行透出，或者库的逻辑
                # 这里简化为: 化神五行对应的天干是否在四柱中存在
                from src.engine.algorithms.energy import EnergyModel
                target_gans = EnergyModel.ELEMENT_MAP[inter.transformed_to]
                has_leader = any(g in all_stems for g in target_gans)
                
                # 校验条件 2: 月令支持 (化神在月令必须是旺或相)
                # 获取化神在月令的状态
                rep_gan = target_gans[0]
                state = EnergyModel.get_state(rep_gan, month_zhi)
                is_supported = state in ["长生", "沐浴", "冠带", "临官", "帝旺"]
                
                if has_leader and is_supported:
                    inter.is_transformed = True
                    if tracer:
                        tracer.record("干支作用", f"合化成功! [{inter.desc}] 因天干引化且月令支持({state})")
                else:
                    inter.is_transformed = False
                    reason = "引化神未透" if not has_leader else f"月令不助({state})"
                    if tracer:
                        tracer.record("干支作用", f"合而不化: [{inter.desc}] 失败原因: {reason}")

    @staticmethod
    def detect_all(ctx: BaziContext, tracer: Tracer = None) -> List[Interaction]:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        
        interactions = []
        
        # 定义四柱天干地支
        stems = [
            (eight_char.getYearGan(), "年干"),
            (eight_char.getMonthGan(), "月干"),
            (eight_char.getDayGan(), "日干"),
            (eight_char.getTimeGan(), "时干")
        ]
        branches = [
            (eight_char.getYearZhi(), "年支"),
            (eight_char.getMonthZhi(), "月支"),
            (eight_char.getDayZhi(), "日支"),
            (eight_char.getTimeZhi(), "时支")
        ]

        # 1. 天干五合检测
        for i in range(len(stems)):
            for j in range(i + 1, len(stems)):
                pair = tuple(sorted([stems[i][0], stems[j][0]]))
                if pair in InteractionDetector.STEM_COMBINATIONS:
                    target_elem = InteractionDetector.STEM_COMBINATIONS[pair]
                    interactions.append(Interaction(
                        type="合",
                        source=stems[i][1],
                        target=stems[j][1],
                        transformed_to=target_elem,
                        desc=f"{stems[i][0]}{stems[j][0]}合化{target_elem}"
                    ))
                    if tracer:
                        tracer.record("干支作用", f"检测到天干合: {stems[i][1]}{stems[i][0]} + {stems[j][1]}{stems[j][0]}")

        # 2. 地支六冲检测
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if InteractionDetector.BRANCH_CLASHES.get(branches[i][0]) == branches[j][0]:
                    interactions.append(Interaction(
                        type="冲",
                        source=branches[i][1],
                        target=branches[j][1],
                        desc=f"{branches[i][0]}{branches[j][0]}相冲"
                    ))
                    if tracer:
                        tracer.record("干支作用", f"检测到地支冲: {branches[i][1]}{branches[i][0]} vs {branches[j][1]}{branches[j][0]}")

        # 3. 伏吟/反吟检测 (原局)
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if branches[i][0] == branches[j][0] and stems[i][0] == stems[j][0]:
                    interactions.append(Interaction(
                        type="伏吟", source=branches[i][1], target=branches[j][1],
                        desc=f"{branches[i][1]}与{branches[j][1]}伏吟"
                    ))

        return interactions
