import functools
from typing import Dict, Tuple, Union, List, Optional

from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.score_calculator import ChartScoringData, get_chart_scoring_data
from d4dj_utils.master.chart_master import ChartMaster
from d4dj_utils.master.skill_master import SkillMaster


class ChartScorer:
    def __init__(self, chart_masters: Dict[int, ChartMaster]):
        self.chart_masters = chart_masters

    def __call__(self, *args, **kwargs):
        return self.score(*args, **kwargs)

    def score(
        self,
        chart: Union[ChartMaster, Chart],
        power: int,
        skills: List[SkillMaster],
        fever_multiplier: float = 1.0,
        enable_fever: bool = True,
        accuracy: float = 1.0,
        disable_soflan: bool = False,
        autoplay: bool = False,
        enable_combo_bonus: bool = True,
    ) -> float:
        if isinstance(chart, Chart):
            scoring_data = get_chart_scoring_data(
                chart, [s.max_seconds for s in skills], fever_multiplier
            )
        else:
            if self.get_chart(chart.id):
                scoring_data = self.get_scoring_data(
                    chart.id, tuple(s.max_seconds for s in skills), fever_multiplier
                )
            else:
                return 0
        return scoring_data.score(
            power=power,
            skills=skills,
            enable_fever=enable_fever,
            accuracy=accuracy,
            disable_soflan=disable_soflan,
            autoplay=autoplay,
            enable_combo_bonus=enable_combo_bonus,
        )

    @functools.lru_cache(maxsize=None)
    def get_chart(self, cid: int, /) -> Optional[Chart]:
        try:
            return self.chart_masters[cid].load_chart_data()
        except FileNotFoundError:
            return None

    @functools.lru_cache(maxsize=32768)
    def get_scoring_data(
        self, cid: int, skill_durations: Tuple[float, ...], fever_multiplier: float
    ) -> ChartScoringData:
        return get_chart_scoring_data(
            self.get_chart(cid), skill_durations, fever_multiplier
        )
