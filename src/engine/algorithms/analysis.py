from typing import List, Dict, Optional
from pydantic import BaseModel
from src.engine.preprocessor import BaziContext
from src.engine.utils import Tracer
from src.engine.algorithms.energy import EnergyModel
from src.engine.algorithms.geju import GejuResult

class AnalysisResult(BaseModel):
    strength_level: str
    strength_score: float
    yong_shen: str
    xi_shen: str
    ji_shen: str
    chou_shen: str
    logic_type: str

class AnalysisEngine:
    """
    终极分析引擎：引入《渊海子平》结构化强弱判定
    """
    
    @staticmethod
    def analyze(ctx: BaziContext, energy_data: Dict[str, Dict], geju: GejuResult, tracer: Tracer = None) -> AnalysisResult:
        lunar = ctx.solar.getLunar()
        eight_char = lunar.getEightChar()
        day_gan = eight_char.getDayGan()
        day_elem = EnergyModel._gan_to_elem(day_gan)
        
        scores = {k: v["score"] for k, v in energy_data.items()}
        day_status = energy_data[day_elem]["season_status"] # 旺相休囚死
        
        # 1. 角色定义
        cycle = ["木", "火", "土", "金", "水"]
        idx = cycle.index(day_elem)
        sheng_me = cycle[(idx - 1) % 5] # 印
        me_sheng = cycle[(idx + 1) % 5] # 食伤
        ke_me = cycle[(idx - 2) % 5]    # 官杀
        me_ke = cycle[(idx + 2) % 5]    # 财
        
        # 2. 气势博弈 (Net Balance)
        support_score = scores[day_elem] + scores[sheng_me]
        drain_score = scores[me_sheng] + scores[me_ke] + scores[ke_me]
        total_score = sum(scores.values())
        support_ratio = support_score / total_score if total_score > 0 else 0
        
        # 3. 动态阈值判定
        threshold_strong = 0.50 # 略微降低强弱分界线
        if day_status in ["旺", "相"]:
            threshold_strong = 0.46
        elif day_status in ["死", "绝"]:
            threshold_strong = 0.55
            
        level = "中和"
        if support_ratio > 0.72: level = "极强"
        elif support_ratio > threshold_strong: level = "偏强"
        elif support_ratio < 0.28: level = "极弱"
        elif support_ratio < 0.44: level = "偏弱"
        
        # 4. 泄耗修正 (处理伤官重泄)
        # 证据：蒋介石己土生于戌月(旺)，但伤官庚金极旺泄身，实为身弱
        if scores[me_sheng] > support_score * 0.7:
            if level in ["中和", "偏强"]:
                old_level = level
                level = "偏弱"
                if tracer: tracer.record("强弱判定", f"检测到食伤[{me_sheng}]重泄，定性从[{old_level}]下调至[{level}]")

        if tracer:
            tracer.record("强弱判定", f"支持率:{support_ratio*100:.1f}%, 状态:{day_status}, 最终判定:{level}")

        # 5. 喜用神 (护格 > 调候 > 扶抑)
        yong, xi, ji, chou = "", "", "", ""
        logic = "扶抑平衡"
        
        if "强" in level:
            yong, xi, ji, chou = ke_me, me_ke, sheng_me, day_elem
        else:
            yong, xi, ji, chou = sheng_me, day_elem, ke_me, me_ke

        # 格局护卫优化
        if "伤官佩印" in geju.name or "杀印相生" in geju.name or "病药" in geju.status:
            logic = "病药护格"
            yong = sheng_me # 核心药方通常在印

        return AnalysisResult(
            strength_level=level,
            strength_score=round(support_ratio * 100, 2),
            yong_shen=yong, xi_shen=xi, ji_shen=ji, chou_shen=chou,
            logic_type=logic
        )
