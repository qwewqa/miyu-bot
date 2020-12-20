import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

import pykakasi


class FuzzyMap:
    def __init__(self, filter=lambda: True, matcher=None):
        self.filter = filter or (lambda n: True)
        self.matcher = matcher or FuzzyMatcher()
        self._values = {}
        self.max_length = 0
        self.logger = logging.getLogger(__name__)

    def values(self):
        return (v for v in self._values.values() if self.filter(v))

    def __delitem__(self, key):
        k = romanize(key)
        self._values.__delitem__(k)

    def __setitem__(self, key, value):
        k = romanize(key)
        self._values[k] = value
        self.max_length = len(k)

    def __getitem__(self, key):
        if len(key) > self.max_length * 1.1:
            self.logger.debug(f'Rejected key "{key}" due to length.')
            return None
        key = romanize(key)
        result = min((k for k, v in self._values.items() if self.filter(v)), key=lambda k: self.matcher.score(key, k))
        if self.matcher.score(key, result) > 0:
            return None
        return self._values[result]


@dataclass
class FuzzyMatchConfig:
    base_score: float = 0.0
    insertion_weight: float = 0.001
    deletion_weight: float = 1.0
    default_substitution_weight: float = 1.0
    match_weight: float = -0.2
    special_substitution_weights: Dict[Tuple[str, str], float] = field(default_factory=lambda: {
        ('v', 'b'): 0.0,
        ('l', 'r'): 0.0,
    })
    word_match_weight: float = -0.2
    acronym_match_weight: float = -0.3


class FuzzyMatcher:
    def __init__(self, config: FuzzyMatchConfig = None):
        self.config = config or FuzzyMatchConfig()

    def score(self, source: str, target: str):
        l_src = len(source)
        l_tgt = len(target)
        a: List[List[float]] = [[0] * (l_tgt + 1) for _ in range(l_src + 1)]

        for i in range(l_src + 1):
            a[i][0] = i

        for i in range(l_tgt + 1):
            a[0][i] = i * self.config.insertion_weight

        def strip_vowels(s):
            return re.sub('[aeoiu]', '', s)

        words = target.split()
        word_bonus = min(self.config.word_match_weight * max(sum(a == b for a, b in zip(source, w)) for w in words),
                         self.config.word_match_weight * max(sum(a == b for a, b in
                                                                 zip(source, w[0] + strip_vowels(w[1:]))) for w in
                                                             words),
                         self.config.acronym_match_weight * sum(
                             a == b for a, b in zip(source, ''.join(w[0] for w in words))))

        def sub_weight_at(n, m):
            if source[n - 1] != target[m - 1]:
                return self.config.special_substitution_weights.get(
                    (source[n - 1], target[m - 1]),
                    self.config.default_substitution_weight
                )
            else:
                return self.config.match_weight

        for i_src in range(1, l_src + 1):
            for i_tgt in range(1, l_tgt + 1):
                a[i_src][i_tgt] = min(a[i_src - 1][i_tgt - 1] + sub_weight_at(i_src, i_tgt),
                                      a[i_src - 1][i_tgt] + self.config.deletion_weight,
                                      a[i_src][i_tgt - 1] + self.config.insertion_weight)

                # there are l_scr - i_src source chars remaining
                # each match removes the insertion weight then adds the match weight
                # (l_src - i_src) * (self.config.match_weight - self.config.insertion_weight)
                # is the max difference that can make
                max_additional_score = ((l_src - i_src) * (self.config.match_weight - self.config.insertion_weight) +
                                        word_bonus + self.config.base_score)
                if i_tgt == l_tgt and (
                        a[i_src][i_tgt] + max_additional_score) > 0 and \
                        (a[i_src][i_tgt - 1] + max_additional_score) > 0:
                    return 1

        return a[l_src][l_tgt] + word_bonus + self.config.base_score


def romanize(s: str) -> str:
    kks = pykakasi.kakasi()
    s = re.sub('[\']', '', s)
    s = re.sub('[・]', ' ', s)
    s = re.sub('[A-Za-z]+', lambda ele: f' {ele[0]} ', s)
    s = re.sub('[0-9]+', lambda ele: f' {ele[0]} ', s)
    s = ' '.join(c['hepburn'].strip().lower() for c in kks.convert(s))
    s = re.sub(r'[^a-zA-Z0-9_ ]+', '', s)
    return ' '.join(s.split())
