import pytest

from src.engine.core import BaziEngine
from src.engine.models import BaziRequest


def make_request(**overrides):
    data = {
        "name": "张三",
        "gender": 1,
        "calendar_type": "SOLAR",
        "birth_datetime": "1993-08-04 05:30:00",
        "birth_location": "深圳",
        "time_mode": "MEAN_SOLAR",
        "month_mode": "SOLAR_TERM",
        "zi_shi_mode": "LATE_ZI_IN_DAY",
    }
    data.update(overrides)
    return BaziRequest(**data)


def test_zi_shi_mode_is_used_by_core_and_analysis():
    engine = BaziEngine()
    late_zi = engine.arrange(make_request(birth_datetime="1993-08-04 23:30:00"))
    next_day = engine.arrange(make_request(
        birth_datetime="1993-08-04 23:30:00",
        zi_shi_mode="NEXT_DAY",
    ))

    assert late_zi.core.day.gan + late_zi.core.day.zhi == "丁巳"
    assert next_day.core.day.gan + next_day.core.day.zhi == "戊午"
    assert late_zi.geju.name != next_day.geju.name
    assert late_zi.analysis.strength_level != next_day.analysis.strength_level


def test_lunar_month_mode_keeps_month_derived_fields_consistent():
    engine = BaziEngine()
    result = engine.arrange(make_request(
        birth_datetime="1993-01-25 12:00:00",
        month_mode="LUNAR_MONTH",
    ))

    assert result.core.month.gan + result.core.month.zhi == "甲寅"
    assert result.core.month.shi_shen_gan == "偏印"
    assert result.core.month.hide_gan == ["甲", "丙", "戊"]
    assert result.core.month.na_yin == "大溪水"
    assert result.month_command.current == "戊"
    assert result.geju.name == "偏印格"


@pytest.mark.parametrize("date", ["2030-02-30", "2030-13-01", "bad"])
def test_query_date_rejects_invalid_dates(date):
    engine = BaziEngine()
    with pytest.raises(ValueError, match="--date"):
        engine.arrange(make_request(), query_date=date)
