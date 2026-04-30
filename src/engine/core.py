from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.engine.models import BaziRequest
from src.engine.preprocessor import Preprocessor, BaziContext
from src.engine.extractor import (
    CoreExtractor, FortuneExtractor, AuxiliaryExtractor,
    CoreChart, FortuneData, AuxiliaryChart
)
from src.engine.algorithms.interactions import Interaction
from src.engine.algorithms.geju import GejuResult
from src.engine.algorithms.analysis import AnalysisResult
from src.engine.algorithms.stars import Star

class MonthCommandResult(BaseModel):
    current: str
    detail: str

class FiveElementsResult(BaseModel):
    scores: Dict[str, float]
    states: Dict[str, str]

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
    interactions: List[Interaction] = []
    geju: Optional[GejuResult] = None
    analysis: Optional[AnalysisResult] = None
    stars: List[Star] = []

class BaziEngine:
    def __init__(self):
        self.preprocessor = Preprocessor()

    def arrange(self, request: BaziRequest, query_date: Optional[str] = None) -> BaziResult:
        # 1. 预处理
        ctx = self.preprocessor.process(request)

        # 2. 提取数据
        core_chart = CoreExtractor.extract(ctx)
        fortune_data = FortuneExtractor.extract(ctx)
        if query_date:
            fortune_data.query = FortuneExtractor.query_date(ctx, fortune_data.da_yun, query_date)
        auxiliary_chart = AuxiliaryExtractor.extract(ctx)

        # 3. 深度分析 (Phase 3)
        from src.engine.algorithms.command import MonthCommandExtractor
        cmd_gan, cmd_detail = MonthCommandExtractor.get_command(ctx)
        month_command = MonthCommandResult(current=cmd_gan, detail=cmd_detail)

        from src.engine.algorithms.energy import EnergyModel
        energy_data = EnergyModel.calculate_scores(ctx)
        five_elements = FiveElementsResult(
            scores={k: v["score"] for k, v in energy_data.items()},
            states={k: v["state"] for k, v in energy_data.items()}
        )

        from src.engine.algorithms.interactions import InteractionDetector
        interactions = InteractionDetector.detect_all(ctx)
        InteractionDetector.validate_transformations(interactions, ctx)

        from src.engine.algorithms.geju import GejuAnalyzer
        geju = GejuAnalyzer.analyze(ctx, interactions, five_elements.scores)

        from src.engine.algorithms.analysis import AnalysisEngine
        analysis = AnalysisEngine.analyze(ctx, energy_data, geju)

        from src.engine.algorithms.stars import StarDetector
        stars = StarDetector.detect(ctx)

        import re
        zodiac_pattern = r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座"
        clean_solar = re.sub(zodiac_pattern, "", ctx.solar.toFullString())
        clean_lunar = re.sub(zodiac_pattern, "", ctx.solar.getLunar().toFullString())

        return BaziResult(
            request=request,
            birth_solar_datetime=clean_solar,
            birth_lunar_datetime=clean_lunar,
            core=core_chart,
            fortune=fortune_data,
            auxiliary=auxiliary_chart,
            month_command=month_command,
            five_elements=five_elements,
            interactions=interactions,
            geju=geju,
            analysis=analysis,
            stars=stars
        )
