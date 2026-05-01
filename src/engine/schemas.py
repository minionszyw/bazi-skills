from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.engine.models import BaziRequest
from src.engine.algorithms.interactions import Interaction
from src.engine.algorithms.geju import GejuResult
from src.engine.algorithms.analysis import AnalysisResult
from src.engine.algorithms.stars import Star


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
    prev_name: str
    prev_jie: str
    next_name: str
    next_jie: str

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
    xiao_yun: List[XiaoYunData] = Field(default_factory=list)

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
    before_start_xiao_yun: List[XiaoYunData] = Field(default_factory=list)
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

# --- 算法分析结果 ---
class MonthCommandResult(BaseModel):
    current: str
    detail: str

class FiveElementsResult(BaseModel):
    scores: Dict[str, float]
    states: Dict[str, str]

# --- 顶层输出模型 ---
class BaziResult(BaseModel):
    processed_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    request: BaziRequest
    birth_solar_datetime: str
    birth_lunar_datetime: str
    core: CoreChart
    fortune: FortuneData
    auxiliary: AuxiliaryChart
    month_command: Optional[MonthCommandResult] = None
    five_elements: Optional[FiveElementsResult] = None
    interactions: List[Interaction] = Field(default_factory=list)
    geju: Optional[GejuResult] = None
    analysis: Optional[AnalysisResult] = None
    stars: List[Star] = Field(default_factory=list)
