import math
from lunar_python import Solar, Lunar
from datetime import datetime
from pydantic import BaseModel
from src.engine.models import CalendarType, BaziRequest, TimeMode

class CalendarConverter:
    @staticmethod
    def to_solar(date_str: str, calendar_type: CalendarType) -> Solar:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        if calendar_type == CalendarType.SOLAR:
            return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        else:
            # 农历转公历
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
            end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
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
        """计算均时差 (分钟)"""
        # N 为一年中的第几天
        dt_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        n = dt.timetuple().tm_yday
        
        b_deg = 360 * (n - 81) / 365
        b_rad = math.radians(b_deg)
        
        # EoT = 9.87*sin(2B) - 7.67*sin(B+78.7)
        eot = 9.87 * math.sin(2 * b_rad) - 7.67 * math.sin(b_rad + math.radians(78.7))
        return eot

    @staticmethod
    def get_true_solar_time(solar: Solar, longitude: float) -> Solar:
        """将平太阳时转换为真太阳时"""
        eot = SolarTimeCalculator.get_eot(solar)
        # 经度修正: (经度 - 120) * 4 分钟
        lon_offset = (longitude - 120.0) * 4
        
        total_offset_minutes = lon_offset + eot
        
        # 转换时间
        dt_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d} " \
                 f"{solar.getHour():02d}:{solar.getMinute():02d}:{solar.getSecond():02d}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        
        corrected_dt = datetime.fromtimestamp(dt.timestamp() + total_offset_minutes * 60)
        return Solar.fromYmdHms(
            corrected_dt.year, corrected_dt.month, corrected_dt.day,
            corrected_dt.hour, corrected_dt.minute, corrected_dt.second
        )

class BaziContext(BaseModel):
    solar: Solar
    longitude: float
    request: BaziRequest

    class Config:
        arbitrary_types_allowed = True

class Preprocessor:
    def __init__(self, config_obj=None):
        from src.engine.config import config as default_config
        self.config = config_obj or default_config

    def process(self, request: BaziRequest) -> BaziContext:
        # 1. 历法标准化 -> 获取公历 Solar
        solar = CalendarConverter.to_solar(request.birth_datetime, request.calendar_type)
        
        # 2. 夏令时校正
        solar = DSTCorrector.check_and_correct(solar)
        
        # 3. 经度获取
        if request.longitude is not None:
            longitude = request.longitude
        else:
            longitude = self.config.get_longitude(request.birth_location)
        
        # 4. 真太阳时校正 (如果模式开启)
        if request.time_mode == TimeMode.TRUE_SOLAR:
            solar = SolarTimeCalculator.get_true_solar_time(solar, longitude)
            
        return BaziContext(
            solar=solar,
            longitude=longitude,
            request=request
        )