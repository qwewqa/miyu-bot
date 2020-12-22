import logging
import math
import re
import timeit
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Iterable

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
        self.max_length = max(self.max_length, math.ceil(len(k) * 1.1))
        self.matcher.set_max_length(self.max_length)

    def __getitem__(self, key):
        start_time = timeit.default_timer()
        if len(key) > self.max_length:
            self.logger.debug(f'Rejected key "{key}" due to length.')
            return None
        key = romanize(key)
        result = self.matcher.closest_match(key, (k for k, v in self._values.items() if self.filter(v)))
        if not result:
            return None
        self.logger.info(f'Found key "{key}" in time {timeit.default_timer() - start_time}.')
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
        self.array: Optional[List[List[float]]] = None

    def set_max_length(self, length: int):
        if not length:
            self.array = None
        else:
            self.array = [[0] * (length + 1) for _ in range(length + 1)]

        for i in range(length + 1):
            self.array[i][0] = i * self.config.deletion_weight
            self.array[0][i] = i * self.config.insertion_weight

    def closest_match(self, source: str, targets: Iterable[str]) -> Optional[str]:
        threshold = 0
        closest = None
        for target in targets:
            score = self.score(source, target, threshold)
            if score <= 0:
                threshold = score
                closest = target
        return closest

    def score(self, source: str, target: str, threshold=0.0):
        # target must not be empty

        l_src = len(source)
        l_tgt = len(target)

        a = self.array

        config = self.config
        base_score = config.base_score
        insertion_weight = config.insertion_weight
        deletion_weight = config.deletion_weight
        default_substitution_weight = config.default_substitution_weight
        match_weight = config.match_weight
        special_substitution_weights = config.special_substitution_weights
        word_match_weight = config.word_match_weight
        acronym_match_weight = config.acronym_match_weight

        if not a:
            a = [[0] * (l_tgt + 1) for _ in range(l_src + 1)]

            for i in range(l_src + 1):
                a[i][0] = i

            for i in range(l_tgt + 1):
                a[0][i] = i * insertion_weight

        def strip_vowels(s):
            return re.sub('[aeoiu]', '', s)

        words = target.split()
        word_bonus = min(word_match_weight * max(sum(a == b for a, b in zip(source, w)) for w in words),
                         word_match_weight * max(sum(a == b for a, b in
                                                     zip(source, w[0] + strip_vowels(w[1:]))) for w in
                                                 words),
                         acronym_match_weight * sum(
                             a == b for a, b in zip(source, ''.join(w[0] for w in words))))

        threshold -= word_bonus + base_score

        for i_src in range(1, l_src + 1):
            for i_tgt in range(1, l_tgt + 1):
                a[i_src][i_tgt] = min(a[i_src - 1][i_tgt - 1] + ((special_substitution_weights.get(
                    (source[i_src - 1], target[i_tgt - 1]),
                    default_substitution_weight
                )) if source[i_src - 1] != target[i_tgt - 1] else match_weight),
                                      a[i_src - 1][i_tgt] + deletion_weight,
                                      a[i_src][i_tgt - 1] + insertion_weight)

            # there are l_scr - i_src source chars remaining
            # each match removes the insertion weight then adds the match weight
            # this is the max difference that can make
            max_additional_score = (l_src - i_src) * (match_weight - insertion_weight)
            if ((a[i_src][l_tgt] + max_additional_score) > threshold and
                    (a[i_src][l_tgt - 1] + max_additional_score) > threshold):
                return 1

        return a[l_src][l_tgt] + word_bonus + base_score


def romanize(s: str) -> str:
    kks = pykakasi.kakasi()
    s = re.sub('[\']', '', s)
    s = re.sub('[・]', ' ', s)
    s = re.sub('[A-Za-z]+', lambda ele: f' {ele[0]} ', s)
    s = re.sub('[0-9]+', lambda ele: f' {ele[0]} ', s)
    s = ' '.join(c['hepburn'].strip().lower() for c in kks.convert(s))
    s = re.sub(r'[^a-zA-Z0-9_ ]+', '', s)
    return ' '.join(s.split())
