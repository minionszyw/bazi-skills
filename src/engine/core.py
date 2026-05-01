import re
from typing import Optional
from src.engine.models import BaziRequest
from src.engine.preprocessor import Preprocessor
from src.engine.extractor import CoreExtractor, FortuneExtractor, AuxiliaryExtractor
from src.engine.schemas import (
    BaziResult, MonthCommandResult, FiveElementsResult,
    CoreChart, FortuneData, AuxiliaryChart,
)
from src.engine.algorithms.command import MonthCommandExtractor
from src.engine.algorithms.energy import EnergyModel
from src.engine.algorithms.interactions import InteractionDetector
from src.engine.algorithms.geju import GejuAnalyzer
from src.engine.algorithms.analysis import AnalysisEngine
from src.engine.algorithms.stars import StarDetector

_ZODIAC_RE = re.compile(r"\s(白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼)座")


class BaziEngine:
    def __init__(self):
        self.preprocessor = Preprocessor()

    def arrange(self, request: BaziRequest, query_date: Optional[str] = None, include_xiao_yun: bool = False) -> BaziResult:
        ctx = self.preprocessor.process(request)

        core_chart   = CoreExtractor.extract(ctx)
        fortune_data = FortuneExtractor.extract(ctx, include_xiao_yun=include_xiao_yun)
        if query_date:
            fortune_data.query = FortuneExtractor.query_date(ctx, fortune_data.da_yun, query_date)
        auxiliary_chart = AuxiliaryExtractor.extract(ctx)

        cmd_gan, cmd_detail = MonthCommandExtractor.get_command(ctx)
        month_command = MonthCommandResult(current=cmd_gan, detail=cmd_detail)

        energy_data  = EnergyModel.calculate_scores(ctx)
        five_elements = FiveElementsResult(
            scores={k: v["score"] for k, v in energy_data.items()},
            states={k: v["state"] for k, v in energy_data.items()}
        )

        interactions = InteractionDetector.detect_all(ctx)
        InteractionDetector.validate_transformations(interactions, ctx)

        geju     = GejuAnalyzer.analyze(ctx, interactions, five_elements.scores)
        analysis = AnalysisEngine.analyze(ctx, energy_data, geju)
        stars    = StarDetector.detect(ctx)

        return BaziResult(
            request=request,
            birth_solar_datetime=_ZODIAC_RE.sub("", ctx.solar.toFullString()),
            birth_lunar_datetime=_ZODIAC_RE.sub("", ctx.solar.getLunar().toFullString()),
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
