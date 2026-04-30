from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.engine.models import BaziRequest, TraceStep
from src.engine.preprocessor import Preprocessor, BaziContext
from src.engine.utils import Tracer
from src.engine.extractor import (
    CoreExtractor, FortuneExtractor, AuxiliaryExtractor, 
    CoreChart, FortuneData, AuxiliaryChart
)
from src.engine.algorithms.interactions import Interaction
from src.engine.algorithms.geju import GejuResult
from src.engine.algorithms.analysis import AnalysisResult
from src.engine.algorithms.stars import Star

# 补救 1.1.3: 环境快照
class EnvironmentSnapshot(BaseModel):
    processed_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    original_request: BaziRequest

class MonthCommandResult(BaseModel):
    current: str
    detail: str

class FiveElementsResult(BaseModel):
    scores: Dict[str, float]
    states: Dict[str, str]

# 补救 2.4.1: 完整聚合模型
class BaziResult(BaseModel):
    environment: EnvironmentSnapshot
    request: BaziRequest
    birth_solar_datetime: str  # 校正后的实际公历出生时刻
    birth_lunar_datetime: str  # 校正后的实际农历出生时刻
    core: CoreChart
    fortune: FortuneData
    auxiliary: AuxiliaryChart
    analysis_trace: List[TraceStep] = [] # 算法推导路径
    month_command: Optional[MonthCommandResult] = None # 月令分司
    five_elements: Optional[FiveElementsResult] = None # 五行能量分析
    interactions: List[Interaction] = [] # 干支作用关系
    geju: Optional[GejuResult] = None # 格局判定
    analysis: Optional[AnalysisResult] = None # 强弱喜用判定
    stars: List[Star] = [] # 专业神煞

class BaziEngine:
    def __init__(self):
        self.preprocessor = Preprocessor()

    def arrange(self, request: BaziRequest, skip_liu_yue: bool = False) -> BaziResult:
        tracer = Tracer()
        
        # 1. 预处理
        tracer.record("预处理", f"开始处理 {request.name} 的请求")
        ctx = self.preprocessor.process(request)
        tracer.record("预处理", f"时间校正完成: {ctx.solar.toFullString()}")
        
        # 2. 提取数据
        core_chart = CoreExtractor.extract(ctx)
        tracer.record("核心命盘", "四柱提取完成")
        
        fortune_data = FortuneExtractor.extract(ctx, skip_liu_yue=skip_liu_yue)
        tracer.record("动态运程", "起运时间与大运计算完成")
        
        auxiliary_chart = AuxiliaryExtractor.extract(ctx)
        tracer.record("辅助命盘", "胎元、命宫等神煞计算完成")
        
        # 3. 深度分析 (Phase 3)
        # 3.1 月令分司
        from src.engine.algorithms.command import MonthCommandExtractor
        cmd_gan, cmd_detail = MonthCommandExtractor.get_command(ctx, tracer)
        month_command = MonthCommandResult(current=cmd_gan, detail=cmd_detail)
        
        # 3.2 五行能量评分
        from src.engine.algorithms.energy import EnergyModel
        energy_data = EnergyModel.calculate_scores(ctx, tracer)
        five_elements = FiveElementsResult(
            scores={k: v["score"] for k, v in energy_data.items()},
            states={k: v["state"] for k, v in energy_data.items()}
        )
        
        # 3.3 干支作用关系
        from src.engine.algorithms.interactions import InteractionDetector
        interactions = InteractionDetector.detect_all(ctx, tracer)
        InteractionDetector.validate_transformations(interactions, ctx, tracer)
        
        # 3.4 格局判定
        from src.engine.algorithms.geju import GejuAnalyzer
        geju = GejuAnalyzer.analyze(ctx, interactions, five_elements.scores, tracer)
        
        # 3.5 强弱喜用判定
        from src.engine.algorithms.analysis import AnalysisEngine
        analysis = AnalysisEngine.analyze(ctx, energy_data, geju, tracer)
        
        # 3.6 神煞检测
        from src.engine.algorithms.stars import StarDetector
        stars = StarDetector.detect(ctx, tracer)
        
        # 4. 构建快照
        env = EnvironmentSnapshot(original_request=request)
        
        # 过滤掉库自带的星座信息
        import re
        solar_full = ctx.solar.toFullString()
        lunar_full = ctx.solar.getLunar().toFullString()
        
        zodiac_pattern = r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座"
        
        clean_solar = re.sub(zodiac_pattern, "", solar_full)
        clean_lunar = re.sub(zodiac_pattern, "", lunar_full)
        
        return BaziResult(
            environment=env,
            request=request,
            birth_solar_datetime=clean_solar,
            birth_lunar_datetime=clean_lunar,
            core=core_chart,
            fortune=fortune_data,
            auxiliary=auxiliary_chart,
            analysis_trace=tracer.get_steps(),
            month_command=month_command,
            five_elements=five_elements,
            interactions=interactions,
            geju=geju,
            analysis=analysis,
            stars=stars
        )