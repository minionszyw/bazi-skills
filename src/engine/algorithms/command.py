from typing import Dict, Tuple
from lunar_python import Lunar, Solar
from src.engine.models import BaziContext, MonthMode
from src.engine.chart import get_effective_eight_char
class MonthCommandExtractor:
    """
    《渊海子平》人元司令分野计算器
    计算出生时刻在月令中所司权的天干
    """
    
    # 司令分野映射表 (月份地支: [(天干, 天数), ...])
    # 注意：一个月按30天计，逻辑根据《渊海子平》
    COMMAND_TABLE = {
        "寅": [("戊", 7), ("丙", 7), ("甲", 16)],
        "卯": [("甲", 10), ("乙", 20)],
        "辰": [("乙", 9), ("癸", 3), ("戊", 18)],
        "巳": [("戊", 5), ("庚", 9), ("丙", 16)],
        "午": [("丙", 10), ("己", 9), ("丁", 11)],
        "未": [("丁", 9), ("乙", 3), ("己", 18)],
        "申": [("己", 7), ("壬", 3), ("庚", 20)],
        "酉": [("庚", 10), ("辛", 20)],
        "戌": [("辛", 9), ("丁", 3), ("戊", 18)],
        "亥": [("戊", 7), ("甲", 5), ("壬", 18)],
        "子": [("壬", 10), ("癸", 20)],
        "丑": [("癸", 9), ("辛", 3), ("己", 18)],
    }

    @staticmethod
    def get_command(ctx: BaziContext) -> Tuple[str, str]:
        """
        返回: (司令天干, 详情描述)
        """
        from datetime import datetime
        lunar = ctx.solar.getLunar()
        eight_char = get_effective_eight_char(ctx)
        month_zhi = eight_char.getMonthZhi()
        
        # 1. 计算出生时刻在所选月制中的时间深度。
        if ctx.request.month_mode == MonthMode.LUNAR_MONTH:
            days_passed = lunar.getDay() - 1
        else:
            prev_jie = lunar.getPrevJie()

            # 辅助函数：将 Solar 转换为 datetime 时间戳
            def solar_to_ts(s: Solar):
                dt = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond())
                return dt.timestamp()

            birth_ts = solar_to_ts(ctx.solar)
            jie_ts = solar_to_ts(prev_jie.getSolar())

            diff_seconds = birth_ts - jie_ts
            days_passed = diff_seconds / 86400.0 # 浮点天数
        
        # 2. 检索分野
        rules = MonthCommandExtractor.COMMAND_TABLE.get(month_zhi, [])
        accumulated_days = 0
        command_gan = ""
        
        for gan, days in rules:
            accumulated_days += days
            if days_passed <= accumulated_days:
                command_gan = gan
                break
        
        # 保底逻辑 (处理 30 天之外的极少数边界)
        if not command_gan and rules:
            command_gan = rules[-1][0]

        # 3. 引出逻辑 (DESIGN 4.5)
        # 检查分野天干是否在原局天干中透出
        is_induced = False
        pillars_stems = [
            eight_char.getYearGan(),
            eight_char.getMonthGan(),
            # 日干不计入引出，因为日干是受气主体
            eight_char.getTimeGan()
        ]
        
        if command_gan in pillars_stems:
            is_induced = True

        detail = f"处于{command_gan}司权第{int(days_passed)+1}天"
        if is_induced:
            detail += " (真气引出)"
            
        return command_gan, detail
