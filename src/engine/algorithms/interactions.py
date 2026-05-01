from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel
from src.engine.preprocessor import BaziContext

class Interaction(BaseModel):
    type: str        # 合, 冲, 刑, 伏吟, 反吟
    source: str      # 位置 (年干/月支 等)
    target: str
    is_transformed: bool = False
    transformed_to: Optional[str] = None
    desc: str

class InteractionDetector:
    """
    干支作用关系检测器 (基于《渊海子平》)
    """

    # 十天干五合 — 用 frozenset 做键，避免顺序依赖
    STEM_COMBINATIONS = {
        frozenset(["甲", "己"]): "土",
        frozenset(["乙", "庚"]): "金",
        frozenset(["丙", "辛"]): "水",
        frozenset(["丁", "壬"]): "木",
        frozenset(["戊", "癸"]): "火"
    }

    # 地支六冲 — 双向，避免因柱位顺序遗漏
    BRANCH_CLASHES = {
        "子": "午", "午": "子",
        "丑": "未", "未": "丑",
        "寅": "申", "申": "寅",
        "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰",
        "巳": "亥", "亥": "巳"
    }

    # 天干相冲对 — 用于反吟判定 (甲庚、乙辛、丙壬、丁癸；戊己居中无对冲)
    STEM_CLASHES = {
        "甲": "庚", "庚": "甲",
        "乙": "辛", "辛": "乙",
        "丙": "壬", "壬": "丙",
        "丁": "癸", "癸": "丁"
    }

    # 自刑地支 — 辰午酉亥见同支即自刑
    SELF_PUNISHMENTS = {"辰", "午", "酉", "亥"}

    @staticmethod
    def validate_transformations(interactions: List[Interaction], ctx: BaziContext):
        """根据《渊海子平》标准校验合化是否成功"""
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        month_zhi = eight_char.getMonthZhi()
        all_stems = [eight_char.getYearGan(), eight_char.getMonthGan(),
                     eight_char.getDayGan(), eight_char.getTimeGan()]

        for inter in interactions:
            if inter.type == "合" and inter.transformed_to:
                from src.engine.algorithms.energy import EnergyModel
                target_gans = EnergyModel.ELEMENT_MAP[inter.transformed_to]
                # 条件1: 化神天干在四柱中透出
                has_leader = any(g in all_stems for g in target_gans)
                # 条件2: 化神在月令处于旺地 (长生至帝旺)
                state = EnergyModel.get_state(target_gans[0], month_zhi)
                is_supported = state in ["长生", "沐浴", "冠带", "临官", "帝旺"]
                inter.is_transformed = has_leader and is_supported

    @staticmethod
    def detect_all(ctx: BaziContext) -> List[Interaction]:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()

        interactions = []

        # 四柱天干地支，索引对齐: 0=年, 1=月, 2=日, 3=时
        stems = [
            (eight_char.getYearGan(),  "年干"),
            (eight_char.getMonthGan(), "月干"),
            (eight_char.getDayGan(),   "日干"),
            (eight_char.getTimeGan(),  "时干")
        ]
        branches = [
            (eight_char.getYearZhi(),  "年支"),
            (eight_char.getMonthZhi(), "月支"),
            (eight_char.getDayZhi(),   "日支"),
            (eight_char.getTimeZhi(),  "时支")
        ]

        # 1. 天干五合
        for i in range(len(stems)):
            for j in range(i + 1, len(stems)):
                pair = frozenset([stems[i][0], stems[j][0]])
                if pair in InteractionDetector.STEM_COMBINATIONS:
                    target_elem = InteractionDetector.STEM_COMBINATIONS[pair]
                    interactions.append(Interaction(
                        type="合",
                        source=stems[i][1], target=stems[j][1],
                        transformed_to=target_elem,
                        desc=f"{stems[i][0]}{stems[j][0]}合化{target_elem}"
                    ))

        # 2. 地支六冲
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if InteractionDetector.BRANCH_CLASHES.get(branches[i][0]) == branches[j][0]:
                    interactions.append(Interaction(
                        type="冲",
                        source=branches[i][1], target=branches[j][1],
                        desc=f"{branches[i][0]}{branches[j][0]}相冲"
                    ))

        # 3. 地支三刑
        # 无恩之刑 (寅巳申，见其中两支即成)
        wu_en = [b for b in branches if b[0] in ("寅", "巳", "申")]
        if len(wu_en) >= 2:
            interactions.append(Interaction(
                type="刑", source=wu_en[0][1], target=wu_en[-1][1],
                desc="无恩之刑：" + "".join(b[0] for b in wu_en)
            ))
        # 持势之刑 (丑戌未，见其中两支即成)
        chi_shi = [b for b in branches if b[0] in ("丑", "戌", "未")]
        if len(chi_shi) >= 2:
            interactions.append(Interaction(
                type="刑", source=chi_shi[0][1], target=chi_shi[-1][1],
                desc="持势之刑：" + "".join(b[0] for b in chi_shi)
            ))
        # 无礼之刑 (子卯)
        zi  = next((b for b in branches if b[0] == "子"), None)
        mao = next((b for b in branches if b[0] == "卯"), None)
        if zi and mao:
            interactions.append(Interaction(
                type="刑", source=zi[1], target=mao[1],
                desc="无礼之刑：子卯"
            ))
        # 自刑 (辰辰、午午、酉酉、亥亥)
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if (branches[i][0] == branches[j][0] and
                        branches[i][0] in InteractionDetector.SELF_PUNISHMENTS):
                    interactions.append(Interaction(
                        type="刑", source=branches[i][1], target=branches[j][1],
                        desc=f"自刑：{branches[i][0]}见{branches[j][0]}"
                    ))

        # 4. 伏吟 / 反吟
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b_i, b_j = branches[i][0], branches[j][0]
                s_i, s_j = stems[i][0], stems[j][0]
                # 伏吟: 两柱干支完全相同
                if b_i == b_j and s_i == s_j:
                    interactions.append(Interaction(
                        type="伏吟", source=branches[i][1], target=branches[j][1],
                        desc=f"{branches[i][1]}与{branches[j][1]}伏吟（{s_i}{b_i}重见）"
                    ))
                # 反吟: 地支相冲 且 天干相冲
                elif (InteractionDetector.BRANCH_CLASHES.get(b_i) == b_j and
                      InteractionDetector.STEM_CLASHES.get(s_i) == s_j):
                    interactions.append(Interaction(
                        type="反吟", source=branches[i][1], target=branches[j][1],
                        desc=f"{branches[i][1]}与{branches[j][1]}反吟（{s_i}{b_i}冲{s_j}{b_j}）"
                    ))

        return interactions
