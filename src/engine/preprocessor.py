import math
from lunar_python import Solar, Lunar
from datetime import datetime
from src.engine.models import CalendarType, BaziRequest, TimeMode, BaziContext


class CalendarConverter:
    @staticmethod
    def to_solar(date_str: str, calendar_type: CalendarType) -> Solar:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        if calendar_type == CalendarType.SOLAR:
            return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        else:
            lunar = Lunar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            return lunar.getSolar()


class DSTCorrector:
    # 中国夏令时区间 (1986-1991)
    DST_RANGES = [
        ("1986-05-04 00:00:00", "1986-09-14 23:59:59"),
        ("1987-04-12 00:00:00", "1987-09-13 23:59:59"),
        ("1988-04-10 00:00:00", "1988-09-11 23:59:59"),
        ("1989-04-16 00:00:00", "1989-09-17 23:59:59"),
        ("1990-04-15 00:00:00", "1990-09-16 23:59:59"),
        ("1991-04-14 00:00:00", "1991-09-15 23:59:59"),
    ]

    @classmethod
    def check_and_correct(cls, solar: Solar) -> Solar:
        dt_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d} " \
                 f"{solar.getHour():02d}:{solar.getMinute():02d}:{solar.getSecond():02d}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

        for start_str, end_str in cls.DST_RANGES:
            start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            end   = datetime.strptime(end_str,   "%Y-%m-%d %H:%M:%S")
            if start <= dt <= end:
                corrected_dt = datetime.fromtimestamp(dt.timestamp() - 3600)
                return Solar.fromYmdHms(
                    corrected_dt.year, corrected_dt.month, corrected_dt.day,
                    corrected_dt.hour, corrected_dt.minute, corrected_dt.second
                )
        return solar


class SolarTimeCalculator:
    @staticmethod
    def get_eot(solar: Solar) -> float:
        """计算均时差 (分钟)。公式: EoT = 9.87·sin2B − 7.67·sin(B+78.7°)"""
        dt_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d}"
        n = datetime.strptime(dt_str, "%Y-%m-%d").timetuple().tm_yday
        b_rad = math.radians(360 * (n - 81) / 365)
        return 9.87 * math.sin(2 * b_rad) - 7.67 * math.sin(b_rad + math.radians(78.7))

    @staticmethod
    def get_true_solar_time(solar: Solar, longitude: float) -> Solar:
        """平太阳时 → 真太阳时。经度基准: 东经 120°（中国标准时）"""
        total_offset_minutes = (longitude - 120.0) * 4 + SolarTimeCalculator.get_eot(solar)
        dt_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d} " \
                 f"{solar.getHour():02d}:{solar.getMinute():02d}:{solar.getSecond():02d}"
        corrected_dt = datetime.fromtimestamp(
            datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").timestamp() + total_offset_minutes * 60
        )
        return Solar.fromYmdHms(
            corrected_dt.year, corrected_dt.month, corrected_dt.day,
            corrected_dt.hour, corrected_dt.minute, corrected_dt.second
        )


class Preprocessor:
    def __init__(self, config_obj=None):
        from src.engine.config import config as default_config
        self.config = config_obj or default_config

    def process(self, request: BaziRequest) -> BaziContext:
        solar = CalendarConverter.to_solar(request.birth_datetime, request.calendar_type)
        solar = DSTCorrector.check_and_correct(solar)

        longitude = request.longitude if request.longitude is not None \
            else self.config.get_longitude(request.birth_location)

        if request.time_mode == TimeMode.TRUE_SOLAR:
            solar = SolarTimeCalculator.get_true_solar_time(solar, longitude)

        return BaziContext(solar=solar, longitude=longitude, request=request)
