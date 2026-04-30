from typing import Dict, List, Tuple
from src.engine.preprocessor import BaziContext
from src.engine.utils import Tracer

class EnergyModel:
    """
    五行能量量化与状态机模型 (基于《渊海子平》深度标准)
    """
    
    # 旺相休囚死 系数 (平滑化处理，避免分值断崖)
    SEASON_POWER_FACTORS = {
        "旺": 1.3,
        "相": 1.1,
        "休": 0.9,
        "囚": 0.7,
        "死": 0.5
    }

    # 四时五行状态表 (月令地支: {五行: 旺相休囚死})
    SEASON_STATUS_MAP = {
        "寅": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
        "卯": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
        "巳": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
        "午": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
        "申": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
        "酉": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
        "亥": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
        "子": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
        "辰": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
        "戌": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
        "丑": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
        "未": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    }

    SHENG_WANG_TABLE = {
        "甲": {"亥": "长生", "子": "沐浴", "丑": "冠带", "寅": "临官", "卯": "帝旺", "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "绝", "酉": "胎", "戌": "养"},
        "丙": {"寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝", "子": "胎", "丑": "养"},
        "戊": {"寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝", "子": "胎", "丑": "养"},
        "庚": {"巳": "长生", "午": "沐浴", "未": "冠带", "申": "临官", "酉": "帝旺", "戌": "衰", "亥": "病", "子": "死", "丑": "墓", "寅": "绝", "卯": "胎", "辰": "养"},
        "壬": {"申": "长生", "酉": "沐浴", "戌": "冠带", "亥": "临官", "子": "帝旺", "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "绝", "午": "胎", "未": "养"},
        "乙": {"午": "长生", "巳": "沐浴", "辰": "冠带", "卯": "临官", "寅": "帝旺", "丑": "衰", "子": "病", "亥": "死", "戌": "墓", "酉": "绝", "申": "胎", "未": "养"},
        "丁": {"酉": "长生", "申": "沐浴", "未": "冠带", "午": "临官", "巳": "帝旺", "辰": "衰", "卯": "病", "寅": "死", "丑": "墓", "子": "绝", "亥": "胎", "戌": "养"},
        "己": {"酉": "长生", "申": "沐浴", "未": "冠带", "午": "临官", "巳": "帝旺", "辰": "衰", "卯": "病", "寅": "死", "丑": "墓", "子": "绝", "亥": "胎", "戌": "养"},
        "辛": {"子": "长生", "亥": "沐浴", "戌": "冠带", "酉": "官官", "申": "帝旺", "未": "衰", "午": "病", "巳": "死", "辰": "墓", "卯": "绝", "寅": "胎", "丑": "养"},
        "癸": {"卯": "长生", "寅": "沐浴", "丑": "冠带", "子": "临官", "亥": "帝旺", "戌": "衰", "酉": "病", "申": "死", "未": "墓", "午": "绝", "巳": "胎", "辰": "养"},
    }

    ELEMENT_MAP = {
        "木": ["甲", "乙"], "火": ["丙", "丁"], "土": ["戊", "己"], "金": ["庚", "辛"], "水": ["壬", "癸"]
    }
    
    ROOT_WEIGHTS = {
        "MAIN": 3.0,
        "MEDIUM": 1.5,
        "RESIDUAL": 1.0
    }

    @staticmethod
    def get_state(gan: str, zhi: str) -> str:
        return EnergyModel.SHENG_WANG_TABLE.get(gan, {}).get(zhi, "未知")

    @staticmethod
    def calculate_scores(ctx: BaziContext, tracer: Tracer = None) -> Dict[str, Dict]:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        month_zhi = eight_char.getMonthZhi()
        day_gan = eight_char.getDayGan()
        
        raw_scores = {elem: 0.0 for elem in EnergyModel.ELEMENT_MAP.keys()}
        
        # 1. 计算原始物理分数 (位置 x 通根)
        stems = [
            (eight_char.getYearGan(), 1.0, "年干"),
            (eight_char.getMonthGan(), 1.2, "月干"),
            (eight_char.getTimeGan(), 1.0, "时干"),
            (eight_char.getDayGan(), 0.5, "日主")
        ]
        for gan, weight, pos in stems:
            elem = EnergyModel._gan_to_elem(gan)
            raw_scores[elem] += 10.0 * weight

        branches = [
            (eight_char.getYearZhi(), 1.0, "年支", eight_char.getYearHideGan),
            (eight_char.getMonthZhi(), 4.0, "月支", eight_char.getMonthHideGan),
            (eight_char.getDayZhi(), 1.5, "日支", eight_char.getDayHideGan),
            (eight_char.getTimeZhi(), 1.0, "时支", eight_char.getTimeHideGan)
        ]
        for zhi, weight, pos, hide_func in branches:
            hide_gans = hide_func() 
            for i, gan in enumerate(hide_gans):
                elem = EnergyModel._gan_to_elem(gan)
                rt = "MAIN" if i == 0 else "MEDIUM" if i == 1 else "RESIDUAL"
                raw_scores[elem] += 10.0 * weight * EnergyModel.ROOT_WEIGHTS[rt]

        # 2. 气数修正 (旺相休囚死)
        final_data = {}
        season_rules = EnergyModel.SEASON_STATUS_MAP.get(month_zhi, {})
        
        for elem, raw_val in raw_scores.items():
            status = season_rules.get(elem, "休")
            factor = EnergyModel.SEASON_POWER_FACTORS.get(status, 1.0)
            
            # 执行定性修正
            adjusted_score = raw_val * factor
            
            # 日主特殊状态记录
            rep_gan = EnergyModel.ELEMENT_MAP[elem][0]
            dm_state = EnergyModel.get_state(rep_gan, month_zhi)
            
            if tracer and elem == EnergyModel._gan_to_elem(day_gan):
                tracer.record("五行评分", f"日主在月令[{month_zhi}]处于[{status}]位({dm_state}), 气数修正系数: {factor}")

            final_data[elem] = {
                "score": round(adjusted_score, 2),
                "state": dm_state,
                "season_status": status
            }
            
        return final_data

    @staticmethod
    def _gan_to_elem(gan: str) -> str:
        for elem, gans in EnergyModel.ELEMENT_MAP.items():
            if gan in gans: return elem
        return ""