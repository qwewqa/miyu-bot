import logging
import math
import re
import timeit
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional

import pykakasi


class FuzzyFilteredMap:
    def __init__(self, filter_function=None, matcher=None, additive_only_filter=True):
        self.filter = filter_function or (lambda n: True)
        self.matcher = matcher or FuzzyMatcher()
        self._map = {}
        self.length_cutoff = 0
        self.logger = logging.getLogger(__name__)
        self._stale = True
        self.additive_only_filter = additive_only_filter

    @property
    def filtered_items(self):
        if not self.additive_only_filter:
            return [(k, v) for k, v in self._map.items() if self.filter(v)]
        if self._needs_update:
            self._update_items()
        return self._filtered_items

    @property
    def _needs_update(self):
        return self._stale or any(self.filter(v) for k, v in self._filtered_out_items)

    def _update_items(self):
        self._filtered_items = [(k, v) for k, v in self._map.items() if self.filter(v)]
        self._filtered_out_items = [
            (k, v) for k, v in self._map.items() if not self.filter(v)
        ]
        self._stale = False

    def values(self):
        return FuzzyDictValuesView(self)

    def has_exact(self, key):
        return romanize(key) in self._map

    def __delitem__(self, key):
        k = romanize(key)
        del self._map[k]
        self._stale = True

    def __setitem__(self, key, value):
        key = romanize(key)
        self._map[key] = value
        new_cutoff = math.ceil(len(key) * 1.1)
        if new_cutoff > self.length_cutoff:
            self.length_cutoff = new_cutoff
            self.matcher.set_max_length(new_cutoff)
        self._stale = True

    def __getitem__(self, key):
        start_time = timeit.default_timer()
        key = romanize(key)
        if len(key) > self.length_cutoff:
            self.logger.debug(f'Rejected key "{key}" due to length.')
            return None
        try:
            matcher = self.matcher
            result = min(
                (
                    (score, v)
                    for score, v in (
                        (matcher.score(key, k), v) for k, v in self.filtered_items
                    )
                    if score <= 0
                ),
                key=lambda v: v[0],
            )[1]
            self.logger.info(
                f'Found key "{key}" in time {timeit.default_timer() - start_time}.'
            )
            return result
        except ValueError:
            self.logger.info(
                f'Found no results for key "{key}" in time {timeit.default_timer() - start_time}.'
            )
            return None

    def get_sorted(self, key: str):
        start_time = timeit.default_timer()
        if len(key) > self.length_cutoff:
            self.logger.debug(f'Rejected key "{key}" due to length.')
            return []
        key = romanize(key)
        values = [
            v
            for score, v in sorted(
                ((self.matcher.score(key, k), v) for k, v in self.filtered_items),
                key=lambda v: v[0],
            )
            if score <= 0
        ]
        seen_ids = set()
        unique = []
        for value in values:
            if id(value) in seen_ids:
                continue
            unique.append(value)
            seen_ids.add(id(value))
        self.logger.info(
            f'Searched key "{key}" in time {timeit.default_timer() - start_time}.'
        )
        return unique


class FuzzyDictValuesView:
    def __init__(self, source: FuzzyFilteredMap):
        self._map = source

    def __contains__(self, item):
        return item in self._map._map.values() and self._map.filter(item)

    def __iter__(self):
        seen_ids = set()
        for _, value in self._map.filtered_items:
            value_id = id(value)
            if value_id not in seen_ids:
                seen_ids.add(value_id)
                yield value


@dataclass
class FuzzyMatchConfig:
    base_score: float = 0.0
    insertion_weight: float = 0.001
    deletion_weight: float = 1.0
    default_substitution_weight: float = 1.0
    match_weight: float = -0.2
    special_substitution_weights: Dict[Tuple[str, str], float] = field(
        default_factory=lambda: {
            ("v", "b"): 0.0,
            ("l", "r"): 0.0,
            ("c", "k"): 0.0,
            ("y", "i"): 0.4,
        }
    )
    word_match_weight: float = -0.2
    whole_match_weight: float = -0.25
    acronym_match_weight: float = -0.25


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

    def score(self, source: str, target: str, threshold=0.0):
        if not target:
            return 1

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
        whole_match_weight = config.whole_match_weight
        acronym_match_weight = config.acronym_match_weight

        if not a:
            a = [[0] * (l_tgt + 1) for _ in range(l_src + 1)]

            for i in range(l_src + 1):
                a[i][0] = i

            for i in range(l_tgt + 1):
                a[0][i] = i * insertion_weight

        words = target.split()
        word_bonus = min(
            word_match_weight
            * max(sum(a == b for a, b in zip(source, w)) for w in words),
            word_match_weight
            * max(
                sum(a == b for a, b in zip(source, w[0] + strip_vowels(w[1:])))
                for w in words
            ),
            whole_match_weight
            * sum(a == b for a, b in zip(strip_spaces(source), strip_spaces(target))),
            acronym_match_weight
            * sum(a == b for a, b in zip(source, "".join(w[0] for w in words))),
        )

        threshold -= word_bonus + base_score

        for i_src in range(1, l_src + 1):
            for i_tgt in range(1, l_tgt + 1):
                a[i_src][i_tgt] = min(
                    a[i_src - 1][i_tgt - 1]
                    + (
                        (
                            special_substitution_weights.get(
                                (source[i_src - 1], target[i_tgt - 1]),
                                default_substitution_weight,
                            )
                        )
                        if source[i_src - 1] != target[i_tgt - 1]
                        else match_weight
                    ),
                    a[i_src - 1][i_tgt] + deletion_weight,
                    a[i_src][i_tgt - 1] + insertion_weight,
                )

            # there are l_scr - i_src source chars remaining
            # each match removes the insertion weight then adds the match weight
            # this is the max difference that can make
            max_additional_score = (l_src - i_src) * (match_weight - insertion_weight)
            if (a[i_src][l_tgt] + max_additional_score) > threshold and (
                a[i_src][l_tgt - 1] + max_additional_score
            ) > threshold:
                return 1

        return a[l_src][l_tgt] + word_bonus + base_score


def strip_spaces(s):
    return re.sub(" ", "", s)


def strip_vowels(s):
    return re.sub("[aeoiu]", "", s)


_kks = pykakasi.kakasi()

def normalize(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def romanize(s: str) -> str:
    s = str(s)
    s = normalize(s)
    s = re.sub("['・]", "", s)
    s = re.sub("[A-Za-z]+", lambda ele: f" {ele[0]} ", s)
    s = re.sub("[0-9]+", lambda ele: f" {ele[0]} ", s)
    s = " ".join(c["hepburn"].strip().lower() for c in _kks.convert(s))
    s = re.sub(r"[^a-zA-Z0-9_ ]+", "", s)
    return " ".join(s.split())
