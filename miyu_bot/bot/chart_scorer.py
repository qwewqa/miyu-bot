import functools
from typing import Dict, Tuple, Union, List, Optional

from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.score_calculator import ChartScoringData, get_chart_scoring_data
from d4dj_utils.master.chart_master import ChartMaster
from d4dj_utils.master.skill_master import SkillMaster


class ChartScorer:
    def __init__(self, chart_masters: Dict[int, ChartMaster]):
        self.chart_masters = chart_masters

    def score(
        self,
        chart: Union[ChartMaster, Chart],
        power: int,
        skills: List[SkillMaster],
        fever_score_up: float = 0.0,
        enable_fever: bool = True,
        passive_score_up: float = 0.0,
        auto_score_up: float = 0.0,
        disable_soflan: bool = False,
        autoplay: bool = False,
        accuracy: float = 1.0,
        enable_combo_bonus: bool = True,
    ) -> float:
        if isinstance(chart, Chart):
            scoring_data = get_chart_scoring_data(
                chart, [s.max_seconds for s in skills]
            )
        else:
            if self.get_chart(chart.id):
                scoring_data = self.get_scoring_data(
                    chart.id, tuple(s.max_seconds for s in skills)
                )
            else:
                return 0
        return scoring_data.score(
            power=power,
            skills=skills,
            fever_score_up=fever_score_up,
            passive_score_up=passive_score_up,
            auto_score_up=auto_score_up,
            enable_fever=enable_fever,
            disable_soflan=disable_soflan,
            autoplay=autoplay,
            accuracy=accuracy,
            combo_bonus_multiplier=enable_combo_bonus,
        )

    @functools.lru_cache(maxsize=None)
    def get_chart(self, cid: int, /) -> Optional[Chart]:
        try:
            return self.chart_masters[cid].load_chart_data()
        except FileNotFoundError:
            return None

    @functools.lru_cache(maxsize=32768)
    def get_scoring_data(
        self, cid: int, skill_durations: Tuple[float, ...]
    ) -> ChartScoringData:
        return get_chart_scoring_data(self.get_chart(cid), skill_durations)
