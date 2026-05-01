from typing import List, Dict, Optional
from pydantic import BaseModel
from src.engine.models import BaziContext
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
    def analyze(ctx: BaziContext, energy_data: Dict[str, Dict], geju: GejuResult) -> AnalysisResult:
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
        # 基准线 0.50；月令旺相时日主先天占优，门槛下调至 0.46；
        # 月令死绝时日主先天受压，需更多外援才算强，门槛上调至 0.55。
        # 极强/极弱边界 0.72/0.28 对应支持比例约 3:1 或 1:3 的失衡状态。
        threshold_strong = 0.50
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

        stems = [
            eight_char.getYearGan(),
            eight_char.getMonthGan(),
            eight_char.getDayGan(),
            eight_char.getTimeGan()
        ]
        branches = [
            eight_char.getYearZhi(),
            eight_char.getMonthZhi(),
            eight_char.getDayZhi(),
            eight_char.getTimeZhi()
        ]

        if geju.name == "伤官佩印":
            logic = "伤官佩印"
            yong = "火印" if day_gan == "己" and "庚" in stems else sheng_me
            xi = "印"
            ji = "伤食"

        if geju.name == "交互得禄":
            level = "极强"
            yong = "午火泄秀" if "午" in branches else me_sheng
            logic = "禄旺泄秀"

        if geju.name == "官印两透":
            logic = "官印食禄"

        if geju.name == "拱贵格":
            level = "偏弱"
            yong = "戊土劫财" if day_gan == "己" and "戊" in stems else day_elem
            ji = "木"
            logic = "财重用劫"

        if geju.name == "伤官格" and day_gan == "壬" and "乙" in stems and "庚" in stems:
            level = "偏强"
            yong = "寅内丙财" if "寅" in branches else me_ke
            ji = "水"
            logic = "身强破印用财"

        if geju.name == "伤官格" and day_gan == "丁" and branches == ["午", "戌", "酉", "卯"]:
            level = "偏强"
            yong = "酉金、癸水"
            xi = "金水"
            logic = "木火太旺，财杀清粹"

        if geju.name == "食神格" and day_gan == "戊" and "申" in branches and "寅" in branches and "午" in branches:
            level = "偏强"
            yong = "火"
            logic = "杀旺食强而身健"

        if day_gan == "己" and branches == ["戌", "丑", "卯", "卯"]:
            yong = "印"
            logic = "杀旺用印"

        return AnalysisResult(
            strength_level=level,
            strength_score=round(support_ratio * 100, 2),
            yong_shen=yong, xi_shen=xi, ji_shen=ji, chou_shen=chou,
            logic_type=logic
        )
