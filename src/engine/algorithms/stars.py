from typing import List, Dict, Optional
from pydantic import BaseModel
from src.engine.preprocessor import BaziContext
from src.engine.utils import Tracer

class Star(BaseModel):
    name: str
    pos: str  # 出现位置
    desc: str

class StarDetector:
    """
    专业神煞检测器 (严格对齐《渊海子平》明朝版标准)
    """
    
    # 1. 玉堂天乙贵人 (日干查地支)
    TIAN_YI = {
        "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
        "乙": ["子", "申"], "己": ["子", "申"],
        "丙": ["亥", "酉"], "丁": ["亥", "酉"],
        "壬": ["巳", "卯"], "癸": ["巳", "卯"],
        "辛": ["午", "寅"]
    }
    
    # 2. 月德贵人 (月支查天干)
    # 寅午戌月见丙, 申子辰月见壬, 亥卯未月见甲, 巳酉丑月见庚
    YUE_DE = {
        "寅": "丙", "午": "丙", "戌": "丙",
        "申": "壬", "子": "壬", "辰": "壬",
        "亥": "甲", "卯": "甲", "未": "甲",
        "巳": "庚", "酉": "庚", "丑": "庚"
    }

    # 3. 天德贵人 (月支查干支)
    # 正丁二申三壬, 四辛五亥六甲, 七癸八寅九丙, 十乙冬巳腊庚
    TIAN_DE = {
        "寅": "丁", "卯": "申", "辰": "壬",
        "巳": "辛", "午": "亥", "未": "甲",
        "申": "癸", "酉": "寅", "戌": "丙",
        "亥": "乙", "子": "巳", "丑": "庚"
    }

    # 4. 驿马 (年/日支查地支)
    YI_MA = {
        "申": "寅", "子": "寅", "辰": "寅",
        "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥",
        "亥": "巳", "卯": "巳", "未": "巳"
    }
    
    # 5. 咸池 (原'桃花', 年/日支查地支)
    XIAN_CHI = {
        "申": "酉", "子": "酉", "辰": "酉",
        "寅": "卯", "午": "卯", "戌": "卯",
        "巳": "午", "酉": "午", "丑": "午",
        "亥": "子", "卯": "子", "未": "子"
    }

    # 6. 截路空亡 (日干查时干)
    # 甲己申酉, 乙庚午未, 丙辛辰巳, 丁壬寅卯, 戊癸子丑
    JIE_LU_VOID = {
        "甲": ["壬申", "癸酉"], "己": ["壬申", "癸酉"],
        "乙": ["壬午", "癸未"], "庚": ["壬午", "癸未"],
        "丙": ["壬辰", "癸巳"], "辛": ["壬辰", "癸巳"],
        "丁": ["壬寅", "癸卯"], "壬": ["壬寅", "癸卯"],
        "戊": ["壬子", "癸丑"], "癸": ["壬子", "癸丑"]
    }

    @staticmethod
    def detect(ctx: BaziContext, tracer: Tracer = None) -> List[Star]:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        
        day_gan = eight_char.getDayGan()
        day_zhi = eight_char.getDayZhi()
        year_zhi = eight_char.getYearZhi()
        month_zhi = eight_char.getMonthZhi()
        time_gan = eight_char.getTimeGan()
        time_zhi = eight_char.getTimeZhi()
        
        stems = [
            (eight_char.getYearGan(), "年柱"),
            (eight_char.getMonthGan(), "月柱"),
            (eight_char.getDayGan(), "日柱"),
            (eight_char.getTimeGan(), "时柱")
        ]
        branches = [
            (eight_char.getYearZhi(), "年柱"),
            (eight_char.getMonthZhi(), "月柱"),
            (eight_char.getDayZhi(), "日柱"),
            (eight_char.getTimeZhi(), "时柱")
        ]
        
        found_stars = []

        # 1. 判定天乙 (玉堂)
        for zhi, pos in branches:
            if zhi in StarDetector.TIAN_YI.get(day_gan, []):
                found_stars.append(Star(name="天乙贵人", pos=pos, desc="玉堂金马，逢凶化吉"))

        # 2. 判定月德 (月令查天干)
        target_yd = StarDetector.YUE_DE.get(month_zhi)
        for gan, pos in stems:
            if gan == target_yd:
                found_stars.append(Star(name="月德贵人", pos=pos, desc="阴德护佑，灾难不侵"))

        # 3. 判定天德 (月令查干支)
        target_td = StarDetector.TIAN_DE.get(month_zhi)
        # 查干
        for gan, pos in stems:
            if gan == target_td:
                found_stars.append(Star(name="天德贵人", pos=pos, desc="上天之德，化险为夷"))
        # 查支
        for zhi, pos in branches:
            if zhi == target_td:
                found_stars.append(Star(name="天德贵人", pos=pos, desc="上天之德，化险为夷"))

        # 4. 判定驿马与咸池
        check_sources = [year_zhi, day_zhi]
        for zhi, pos in branches:
            if any(zhi == StarDetector.YI_MA.get(s) for s in check_sources):
                if not any(s.name == "驿马" and s.pos == pos for s in found_stars):
                    found_stars.append(Star(name="驿马", pos=pos, desc="主迁徙变动"))
            if any(zhi == StarDetector.XIAN_CHI.get(s) for s in check_sources):
                if not any(s.name == "咸池" and s.pos == pos for s in found_stars):
                    found_stars.append(Star(name="咸池", pos=pos, desc="一名桃花，主性情风流"))

        # 5. 判定截路空亡 (查时柱)
        void_times = StarDetector.JIE_LU_VOID.get(day_gan, [])
        if (time_gan + time_zhi) in void_times:
            found_stars.append(Star(name="截路空亡", pos="时柱", desc="行路受阻，晚年寥落"))

        if tracer:
            tracer.record("神煞检测", f"遵循《渊海子平》标准，共检出 {len(found_stars)} 个神煞")

        return found_stars