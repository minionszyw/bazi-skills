import json
import math
from src.engine.core import BaziEngine
from src.engine.models import BaziRequest, Gender, CalendarType, TimeMode, MonthMode, ZiShiMode
from src.engine.preprocessor import SolarTimeCalculator

def print_user_input(params):
    """打印模拟的用户输入参数"""
    print("\n" + "═"*75)
    print("  模拟用户输入 (8个核心参数)")
    print("─"*75)
    print(f"  1. 姓名 (name):          {params['name']}")
    print(f"  2. 性别 (gender):        {'男 (1)' if params['gender'] == Gender.MALE else '女 (0)'}")
    print(f"  3. 历法 (calendar_type):  {'公历 (SOLAR)' if params['calendar_type'] == CalendarType.SOLAR else '农历 (LUNAR)'}")
    print(f"  4. 时间 (birth_datetime): {params['birth_datetime']}")
    print(f"  5. 地点 (birth_location): {params['birth_location']}")
    print(f"  6. 模式 (time_mode):      {'真太阳时 (TRUE_SOLAR)' if params['time_mode'] == TimeMode.TRUE_SOLAR else '平太阳时 (MEAN_SOLAR)'}")
    print(f"  7. 月柱 (month_mode):     {'节气定月 (SOLAR_TERM)' if params['month_mode'] == MonthMode.SOLAR_TERM else '农历月定月 (LUNAR_MONTH)'}")
    print(f"  8. 子时 (zi_shi_mode):    {'晚子时不换日 (LATE_ZI)' if params['zi_shi_mode'] == ZiShiMode.LATE_ZI_IN_DAY else '23点换日 (NEXT_DAY)'}")
    print("═"*75 + "\n")

def print_engine_internals(res, longitude):
    """展示引擎内部计算过程"""
    print("  [引擎计算层详情 - 真太阳时校正]")
    print(f"  > 检索经度: {longitude}° (地名: {res.request.birth_location})")
    
    # 获取展示数据
    from lunar_python import Solar
    # 解析日期部分进行 EoT 计算展示
    date_str = res.birth_solar_datetime.split(' ')[0]
    y, m, d = map(int, date_str.split('-'))
    s = Solar.fromYmd(y, m, d)
    eot = SolarTimeCalculator.get_eot(s)
    lon_offset = (longitude - 120.0) * 4
    
    print(f"  > 均时差 (EoT): {eot:+.2f} 分钟")
    print(f"  > 经度修正: {lon_offset:+.2f} 分钟")
    print(f"  > 总计偏移: {eot + lon_offset:+.2f} 分钟")
    print(f"  > 标准新历 (UTC+8): {res.request.birth_datetime}")
    print(f"  > 校正后新历 (Solar): {res.birth_solar_datetime}")
    print(f"  > 校正后农历 (Lunar): {res.birth_lunar_datetime}")
    print("─"*75)

def print_bazi_chart(res):
    """模拟专业排盘软件的美化输出"""
    core = res.core
    fortune = res.fortune
    aux = res.auxiliary

    # 定义排版列
    cols = [core.year, core.month, core.day, core.time]
    
    print("  [命盘数据提取]")
    # 1. 十神(天干)
    print("  十神：", end="")
    for col in cols:
        print(f"{col.shi_shen_gan.center(12)}", end="")
    print()

    # 2. 天干
    print("  天干：", end="")
    for col in cols:
        print(f"{col.gan.center(14)}", end="")
    print()

    # 3. 地支
    print("  地支：", end="")
    for col in cols:
        print(f"{col.zhi.center(14)}", end="")
    print()

    # 4. 藏干
    print("  藏干：", end="")
    for col in cols:
        cg = "/".join(col.hide_gan)
        print(f"{cg.center(14)}", end="")
    print()

    # 5. 副星
    print("  副星：", end="")
    for col in cols:
        fx = "/".join(col.shi_shen_zhi)
        print(f"{fx.center(14)}", end="")
    print()

    # 6. 纳音
    print("  纳音：", end="")
    for col in cols:
        print(f"{col.na_yin.center(12)}", end="")
    print()

    # 7. 空亡
    print("  空亡：", end="")
    for col in cols:
        kw = "".join(col.xun_kong)
        print(f"{kw.center(14)}", end="")
    print()

    print("─"*75)
    print("  [辅助信息]")
    # 修正：展示节气名 + 时间
    print(f"  上一个节气：【{core.jie_qi.prev_name}】 {core.jie_qi.prev_jie}")
    print(f"  下一个节气：【{core.jie_qi.next_name}】 {core.jie_qi.next_jie}")
    print(f"  胎元：{aux.tai_yuan}({aux.tai_yuan_na_yin})  命宫：{aux.ming_gong}({aux.ming_gong_na_yin})  身宫：{aux.shen_gong}({aux.shen_gong_na_yin})")
    
    print("─"*75)
    print("  [运程流转]")
    print(f"  正式起运时刻：{fortune.start_solar} (新历)")
    
    print(f"  起运前小运：", end="")
    xy_list = [xy.gan_zhi for xy in fortune.before_start_xiao_yun]
    print(" -> ".join(xy_list))

    print("\n  前五步大运：")
    for dy in fortune.da_yun[:5]:
        print(f"  [{dy.gan_zhi}] {dy.start_year}年起 (岁数: {dy.start_age}) | 旬: {dy.xun}")
    
    print("─"*75)
    print("  [深度分析指标 (Phase 3)]")
    if res.month_command:
        print(f"  > 月令分司：{res.month_command.detail}")
    
    if res.geju:
        print(f"  > 格局判定：{res.geju.name} ({res.geju.type}) | 状态: {res.geju.status}")
        
    if res.analysis:
        a = res.analysis
        print(f"  > 日主强弱：{a.strength_level} (得分: {a.strength_score})")
        print(f"  > 喜用神：用神[{a.yong_shen}] 喜神[{a.xi_shen}] | 忌神[{a.ji_shen}] 仇神[{a.chou_shen}]")
        print(f"  > 推导逻辑：{a.logic_type}")
    
    if res.stars:
        print(f"  > 核心神煞：", end="")
        stars_str = [f"{s.name}({s.pos})" for s in res.stars]
        print(", ".join(stars_str))
    
    print("─"*75)
    for step in res.analysis_trace:
        val_str = f" | 变动: {step.value}" if step.value is not None else ""
        print(f"  * [{step.module}] {step.desc}{val_str}")
    
    print("═"*75 + "\n")

def run_demo():
    engine = BaziEngine()
    
    params = {
        "name": "张三",
        "gender": Gender.MALE,
        "calendar_type": CalendarType.LUNAR,
        "birth_datetime": "1993-08-04 05:30:00",
        "birth_location": "深圳市",
        "time_mode": TimeMode.TRUE_SOLAR,
        "month_mode": MonthMode.SOLAR_TERM,
        "zi_shi_mode": ZiShiMode.LATE_ZI_IN_DAY
    }
    
    print_user_input(params)

    request = BaziRequest(**params)
    result = engine.arrange(request)
    
    # 额外获取经度用于展示
    from src.engine.config import config
    longitude = config.get_longitude(params["birth_location"])

    print_engine_internals(result, longitude)
    print_bazi_chart(result)

if __name__ == "__main__":
    run_demo()