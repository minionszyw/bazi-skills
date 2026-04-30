import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from lunar_python import EightChar, Lunar, Solar
from src.engine.models import ZiShiMode, MonthMode, BaziRequest
from src.engine.preprocessor import BaziContext

# --- 核心命盘 ---
class Column(BaseModel):
    gan: str
    zhi: str
    shi_shen_gan: str
    shi_shen_zhi: List[str]
    hide_gan: List[str]
    na_yin: str
    xun_kong: List[str]

class JieQiContext(BaseModel):
    prev_name: str # 上一个节气名称
    prev_jie: str  # 上一个节气时刻
    next_name: str # 下一个节气名称
    next_jie: str  # 下一个节气时刻

class CoreChart(BaseModel):
    year: Column
    month: Column
    day: Column
    time: Column
    jie_qi: JieQiContext

# --- 动态运程 ---
class XiaoYunData(BaseModel):
    index: int
    gan_zhi: str

class DaYunData(BaseModel):
    index: int
    start_year: int
    start_age: int
    gan_zhi: str
    xun: str
    xiao_yun: List[XiaoYunData] = []

# --- 日期查询结果 ---
class DaYunQueryData(BaseModel):
    gan_zhi: str
    start_year: int
    start_age: int

class LiuNianQueryData(BaseModel):
    year: int
    gan_zhi: str
    xun: str

class LiuYueQueryData(BaseModel):
    month: int
    gan_zhi: str

class LiuRiQueryData(BaseModel):
    day: int
    gan_zhi: str

class FortuneQueryResult(BaseModel):
    date: str
    da_yun: Optional[DaYunQueryData]
    liu_nian: LiuNianQueryData
    liu_yue: LiuYueQueryData
    liu_ri: LiuRiQueryData

class FortuneData(BaseModel):
    start_solar: str
    start_age: int
    da_yun: List[DaYunData]
    before_start_xiao_yun: List[XiaoYunData] = []
    query: Optional[FortuneQueryResult] = None

# --- 辅助命盘 ---
class AuxiliaryChart(BaseModel):
    year_di_shi: str
    month_di_shi: str
    day_di_shi: str
    time_di_shi: str
    tai_yuan: str
    tai_yuan_na_yin: str
    ming_gong: str
    ming_gong_na_yin: str
    shen_gong: str
    shen_gong_na_yin: str

# --- 提取逻辑 ---
class CoreExtractor:
    @staticmethod
    def extract(ctx: BaziContext) -> CoreChart:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        
        # 应用子时流派
        if ctx.request.zi_shi_mode == ZiShiMode.NEXT_DAY:
            eight_char.setSect(1)
        else:
            eight_char.setSect(2)
            
        # 统一从 EightChar 获取，以确保 Sect 设置生效
        y, m, d, t = eight_char.getYear(), eight_char.getMonth(), eight_char.getDay(), eight_char.getTime()

        # 补救 2.1.3: 处理月柱分支模式 (仅当选择农历月定月时覆盖)
        if ctx.request.month_mode == MonthMode.LUNAR_MONTH:
            from lunar_python import LunarYear
            ly = LunarYear.fromYear(lunar.getYear())
            lm = None
            for month_obj in ly.getMonths():
                if abs(month_obj.getMonth()) == abs(lunar.getMonth()):
                    if (lunar.getMonth() < 0 and month_obj.getMonth() < 0) or (lunar.getMonth() > 0 and month_obj.getMonth() > 0):
                        lm = month_obj
                        break
            if lm:
                m = lm.getGanZhi()

        return CoreChart(
            year=Column(
                gan=y[0], zhi=y[1],
                shi_shen_gan=eight_char.getYearShiShenGan(),
                shi_shen_zhi=eight_char.getYearShiShenZhi(),
                hide_gan=eight_char.getYearHideGan(),
                na_yin=eight_char.getYearNaYin(),
                xun_kong=list(eight_char.getYearXunKong())
            ),
            month=Column(
                gan=m[0], zhi=m[1],
                shi_shen_gan=eight_char.getMonthShiShenGan(),
                shi_shen_zhi=eight_char.getMonthShiShenZhi(),
                hide_gan=eight_char.getMonthHideGan(),
                na_yin=eight_char.getMonthNaYin(),
                xun_kong=list(eight_char.getMonthXunKong())
            ),
            day=Column(
                gan=d[0], zhi=d[1],
                shi_shen_gan=eight_char.getDayShiShenGan(),
                shi_shen_zhi=eight_char.getDayShiShenZhi(),
                hide_gan=eight_char.getDayHideGan(),
                na_yin=eight_char.getDayNaYin(),
                xun_kong=list(eight_char.getDayXunKong())
            ),
            time=Column(
                gan=t[0], zhi=t[1],
                shi_shen_gan=eight_char.getTimeShiShenGan(),
                shi_shen_zhi=eight_char.getTimeShiShenZhi(),
                hide_gan=eight_char.getTimeHideGan(),
                na_yin=eight_char.getTimeNaYin(),
                xun_kong=list(eight_char.getTimeXunKong())
            ),
            jie_qi=JieQiContext(
                prev_name=lunar.getPrevJie().getName(),
                prev_jie=re.sub(r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座", "", lunar.getPrevJie().getSolar().toFullString()),
                next_name=lunar.getNextJie().getName(),
                next_jie=re.sub(r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座", "", lunar.getNextJie().getSolar().toFullString())
            )
        )


class FortuneExtractor:
    @staticmethod
    def extract(ctx: BaziContext, include_xiao_yun: bool = False) -> FortuneData:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()

        if ctx.request.zi_shi_mode == ZiShiMode.NEXT_DAY:
            eight_char.setSect(1)
        else:
            eight_char.setSect(2)

        yun = eight_char.getYun(ctx.request.gender)

        da_yun_list = []
        before_start_xiao_yun = []

        for i, dy in enumerate(yun.getDaYun()):
            xiao_yun_objs = [XiaoYunData(index=xy.getIndex(), gan_zhi=xy.getGanZhi()) for xy in dy.getXiaoYun()]

            if i == 0:
                before_start_xiao_yun = xiao_yun_objs
                continue

            da_yun_list.append(DaYunData(
                index=i,
                start_year=dy.getStartYear(),
                start_age=dy.getStartAge(),
                gan_zhi=dy.getGanZhi(),
                xun=dy.getXun(),
                xiao_yun=xiao_yun_objs if include_xiao_yun else []
            ))

        return FortuneData(
            start_solar=re.sub(r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座", "", yun.getStartSolar().toFullString()),
            start_age=yun.getStartYear() - ctx.solar.getYear() if yun.getStartYear() > 0 else 0,
            da_yun=da_yun_list,
            before_start_xiao_yun=before_start_xiao_yun
        )

    @staticmethod
    def query_date(ctx: BaziContext, da_yun_list: List[DaYunData], date_str: str) -> FortuneQueryResult:
        try:
            y, m, d = map(int, date_str.split("-"))
        except (ValueError, AttributeError):
            raise ValueError("--date 格式必须为 YYYY-MM-DD")

        # 找所在大运
        matched_dy = None
        for dy in da_yun_list:
            if dy.start_year <= y < dy.start_year + 10:
                matched_dy = DaYunQueryData(gan_zhi=dy.gan_zhi, start_year=dy.start_year, start_age=dy.start_age)
                break

        # 流年/流月/流日 ganzhi 直接由 Solar 取
        solar = Solar.fromYmd(y, m, d)
        ec = solar.getLunar().getEightChar()
        if ctx.request.zi_shi_mode == ZiShiMode.NEXT_DAY:
            ec.setSect(1)
        else:
            ec.setSect(2)

        # 流年 xun 从 yun 结构获取
        birth_ec = ctx.solar.getLunar().getEightChar()
        if ctx.request.zi_shi_mode == ZiShiMode.NEXT_DAY:
            birth_ec.setSect(1)
        else:
            birth_ec.setSect(2)
        yun = birth_ec.getYun(ctx.request.gender)

        liu_nian_xun = ""
        for yun_dy in yun.getDaYun():
            for ln in yun_dy.getLiuNian():
                if ln.getYear() == y:
                    liu_nian_xun = ln.getXun()
                    break
            if liu_nian_xun:
                break

        return FortuneQueryResult(
            date=date_str,
            da_yun=matched_dy,
            liu_nian=LiuNianQueryData(year=y, gan_zhi=ec.getYear(), xun=liu_nian_xun),
            liu_yue=LiuYueQueryData(month=m, gan_zhi=ec.getMonth()),
            liu_ri=LiuRiQueryData(day=d, gan_zhi=ec.getDay()),
        )

class AuxiliaryExtractor:
    @staticmethod
    def extract(ctx: BaziContext) -> AuxiliaryChart:
        eight_char = ctx.solar.getLunar().getEightChar()
        return AuxiliaryChart(
            year_di_shi=eight_char.getYearDiShi(),
            month_di_shi=eight_char.getMonthDiShi(),
            day_di_shi=eight_char.getDayDiShi(),
            time_di_shi=eight_char.getTimeDiShi(),
            tai_yuan=eight_char.getTaiYuan(),
            tai_yuan_na_yin=eight_char.getTaiYuanNaYin(),
            ming_gong=eight_char.getMingGong(),
            ming_gong_na_yin=eight_char.getMingGongNaYin(),
            shen_gong=eight_char.getShenGong(),
            shen_gong_na_yin=eight_char.getShenGongNaYin()
        )
