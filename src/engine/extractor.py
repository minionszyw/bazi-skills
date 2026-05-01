import re
from typing import List
from lunar_python import Solar
from src.engine.models import ZiShiMode, BaziContext
from src.engine.chart import get_effective_eight_char
from src.engine.schemas import (
    Column, JieQiContext, CoreChart,
    XiaoYunData, DaYunData, FortuneData,
    DaYunQueryData, LiuNianQueryData, LiuYueQueryData, LiuRiQueryData, FortuneQueryResult,
    AuxiliaryChart,
)

_ZODIAC_RE = re.compile(r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座")


class CoreExtractor:
    @staticmethod
    def extract(ctx: BaziContext) -> CoreChart:
        lunar = ctx.solar.getLunar()
        eight_char = get_effective_eight_char(ctx)

        y, m, d, t = eight_char.getYear(), eight_char.getMonth(), eight_char.getDay(), eight_char.getTime()

        def _strip(s): return _ZODIAC_RE.sub("", s)

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
                prev_jie=_strip(lunar.getPrevJie().getSolar().toFullString()),
                next_name=lunar.getNextJie().getName(),
                next_jie=_strip(lunar.getNextJie().getSolar().toFullString()),
            )
        )


class FortuneExtractor:
    @staticmethod
    def extract(ctx: BaziContext, include_xiao_yun: bool = False) -> FortuneData:
        lunar = ctx.solar.getLunar()
        eight_char = get_effective_eight_char(ctx)

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
            start_solar=_ZODIAC_RE.sub("", yun.getStartSolar().toFullString()),
            start_age=da_yun_list[0].start_age if da_yun_list else 0,
            da_yun=da_yun_list,
            before_start_xiao_yun=before_start_xiao_yun
        )

    @staticmethod
    def query_date(ctx: BaziContext, da_yun_list: List[DaYunData], date_str: str) -> FortuneQueryResult:
        from datetime import datetime
        try:
            y, m, d = map(int, date_str.split("-"))
            datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, AttributeError) as e:
            raise ValueError("--date 必须是真实日期，格式为 YYYY-MM-DD") from e

        matched_dy = None
        for dy in da_yun_list:
            if dy.start_year <= y < dy.start_year + 10:
                matched_dy = DaYunQueryData(gan_zhi=dy.gan_zhi, start_year=dy.start_year, start_age=dy.start_age)
                break

        solar = Solar.fromYmd(y, m, d)
        ec = solar.getLunar().getEightChar()
        if ctx.request.zi_shi_mode == ZiShiMode.NEXT_DAY:
            ec.setSect(1)
        else:
            ec.setSect(2)

        birth_ec = get_effective_eight_char(ctx)
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
        eight_char = get_effective_eight_char(ctx)
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
