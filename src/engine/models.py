from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from lunar_python import Solar


class Gender(int, Enum):
    FEMALE = 0
    MALE = 1

class CalendarType(str, Enum):
    SOLAR = "SOLAR"
    LUNAR = "LUNAR"

class TimeMode(str, Enum):
    TRUE_SOLAR = "TRUE_SOLAR"
    MEAN_SOLAR = "MEAN_SOLAR"

class MonthMode(str, Enum):
    SOLAR_TERM = "SOLAR_TERM"
    LUNAR_MONTH = "LUNAR_MONTH"

class ZiShiMode(str, Enum):
    LATE_ZI_IN_DAY = "LATE_ZI_IN_DAY"
    NEXT_DAY = "NEXT_DAY"


class BaziRequest(BaseModel):
    name: str = Field(..., min_length=1)
    gender: Gender
    calendar_type: CalendarType
    birth_datetime: str
    birth_location: str
    longitude: Optional[float] = None

    time_mode: TimeMode = TimeMode.TRUE_SOLAR
    month_mode: MonthMode = MonthMode.SOLAR_TERM
    zi_shi_mode: ZiShiMode = ZiShiMode.LATE_ZI_IN_DAY

    @field_validator("birth_datetime")
    @classmethod
    def validate_datetime(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            return v
        except ValueError:
            raise ValueError("日期格式必须为 YYYY-MM-DD HH:mm:ss")


class BaziContext(BaseModel):
    """预处理后的排盘上下文，贯穿所有提取与算法模块"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    solar: Solar
    longitude: float
    request: BaziRequest
