from src.engine.models import BaziContext, MonthMode, ZiShiMode

try:
    from lunar_python.util.LunarUtil import LunarUtil
except ImportError:  # pragma: no cover - dependency API guard
    LunarUtil = None


STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}
STEM_YANG = {"甲", "丙", "戊", "庚", "壬"}
ELEMENT_CYCLE = ["木", "火", "土", "金", "水"]


def shishen(day_gan: str, target_gan: str) -> str:
    if day_gan == target_gan:
        return "日主"

    day_elem = STEM_ELEMENT[day_gan]
    target_elem = STEM_ELEMENT[target_gan]
    same_polarity = (day_gan in STEM_YANG) == (target_gan in STEM_YANG)
    day_idx = ELEMENT_CYCLE.index(day_elem)
    target_idx = ELEMENT_CYCLE.index(target_elem)

    if target_elem == day_elem:
        return "比肩" if same_polarity else "劫财"
    if target_idx == (day_idx + 1) % 5:
        return "食神" if same_polarity else "伤官"
    if target_idx == (day_idx + 2) % 5:
        return "偏财" if same_polarity else "正财"
    if target_idx == (day_idx - 1) % 5:
        return "偏印" if same_polarity else "正印"
    if target_idx == (day_idx - 2) % 5:
        return "七杀" if same_polarity else "正官"
    return "未知"


class EffectiveEightChar:
    def __init__(self, eight_char, month_pillar: str | None = None):
        self._eight_char = eight_char
        self._month_pillar = month_pillar

    def __getattr__(self, name):
        return getattr(self._eight_char, name)

    def getMonth(self):
        return self._month_pillar or self._eight_char.getMonth()

    def getMonthGan(self):
        return self.getMonth()[0]

    def getMonthZhi(self):
        return self.getMonth()[1]

    def getMonthHideGan(self):
        if not self._month_pillar:
            return self._eight_char.getMonthHideGan()
        return LunarUtil.ZHI_HIDE_GAN[self.getMonthZhi()]

    def getMonthShiShenGan(self):
        if not self._month_pillar:
            return self._eight_char.getMonthShiShenGan()
        return shishen(self.getDayGan(), self.getMonthGan())

    def getMonthShiShenZhi(self):
        if not self._month_pillar:
            return self._eight_char.getMonthShiShenZhi()
        return [shishen(self.getDayGan(), gan) for gan in self.getMonthHideGan()]

    def getMonthNaYin(self):
        if not self._month_pillar:
            return self._eight_char.getMonthNaYin()
        return LunarUtil.NAYIN[self.getMonth()]

    def getMonthXun(self):
        if not self._month_pillar:
            return self._eight_char.getMonthXun()
        return LunarUtil.getXun(self.getMonth())

    def getMonthXunKong(self):
        if not self._month_pillar:
            return self._eight_char.getMonthXunKong()
        return tuple(LunarUtil.getXunKong(self.getMonth()))

    def getMonthDiShi(self):
        if not self._month_pillar:
            return self._eight_char.getMonthDiShi()
        from src.engine.algorithms.energy import EnergyModel
        return EnergyModel.get_state(self.getDayGan(), self.getMonthZhi())


def get_effective_eight_char(ctx: BaziContext):
    lunar = ctx.solar.getLunar()
    eight_char = lunar.getEightChar()
    request = getattr(ctx, "request", None)

    if hasattr(eight_char, "setSect"):
        if getattr(request, "zi_shi_mode", None) == ZiShiMode.NEXT_DAY:
            eight_char.setSect(1)
        else:
            eight_char.setSect(2)

    month_pillar = None
    if getattr(request, "month_mode", None) == MonthMode.LUNAR_MONTH:
        from lunar_python import LunarYear
        ly = LunarYear.fromYear(lunar.getYear())
        for month_obj in ly.getMonths():
            same_month = abs(month_obj.getMonth()) == abs(lunar.getMonth())
            same_leap = (lunar.getMonth() < 0) == (month_obj.getMonth() < 0)
            if same_month and same_leap:
                month_pillar = month_obj.getGanZhi()
                break

    return EffectiveEightChar(eight_char, month_pillar)
