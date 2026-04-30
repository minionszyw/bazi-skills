from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Gender(int, Enum):
    FEMALE = 0
    MALE = 1

class CalendarType(str, Enum):
    SOLAR = "SOLAR"
    LUNAR = "LUNAR"

class TimeMode(str, Enum):
    TRUE_SOLAR = "TRUE_SOLAR"  # 真太阳时
    MEAN_SOLAR = "MEAN_SOLAR"  # 平太阳时

class MonthMode(str, Enum):
    SOLAR_TERM = "SOLAR_TERM"      # 节气定月 (Exact)
    LUNAR_MONTH = "LUNAR_MONTH"    # 农历月定月

class ZiShiMode(str, Enum):
    LATE_ZI_IN_DAY = "LATE_ZI_IN_DAY"  # 晚子时不换日 (Sect 2)
    NEXT_DAY = "NEXT_DAY"              # 23点换日 (Sect 1)

class TraceStep(BaseModel):
    module: str      # 模块名 (如: 月令分司, 五行评分)
    desc: str        # 推导描述
    value: Optional[float] = None # 涉及的数值变动 (可选)

class BaziRequest(BaseModel):
    name: str = Field(..., min_length=1)
    gender: Gender
    calendar_type: CalendarType
    birth_datetime: str  # 格式: YYYY-MM-DD HH:mm:ss
    birth_location: str
    longitude: Optional[float] = None # 显式经度
    latitude: Optional[float] = None  # 显式纬度
    
    # 算法开关
    time_mode: TimeMode = TimeMode.TRUE_SOLAR
    month_mode: MonthMode = MonthMode.SOLAR_TERM
    zi_shi_mode: ZiShiMode = ZiShiMode.LATE_ZI_IN_DAY

    @validator("birth_datetime")
    def validate_datetime(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            return v
        except ValueError:
            raise ValueError("日期格式必须为 YYYY-MM-DD HH:mm:ss")
