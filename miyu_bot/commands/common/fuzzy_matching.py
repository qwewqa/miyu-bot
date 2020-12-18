import logging
import re
from typing import Tuple

import pykakasi


class FuzzyMatcher:
    def __init__(self, filter, threshold: float = 1):
        self.filter = filter or (lambda n: True)
        self.threshold = threshold
        self.values = {}
        self.max_length = 0
        self.logger = logging.getLogger(__name__)

    def __setitem__(self, key, value):
        k = romanize(key)
        self.values[k] = value
        self.max_length = len(k[0])

    def __getitem__(self, key):
        if len(key) > self.max_length * 1.1:
            self.logger.debug(f'Rejected key "{key}" due to length.')
            return None
        key, _ = romanize(key)
        result = min((k for k, v in self.values.items() if self.filter(v)),
                     key=lambda v: fuzzy_match_score(key, *v, threshold=self.threshold))
        if fuzzy_match_score(key, *result, threshold=self.threshold) > self.threshold:
            return None
        return self.values[result]


_insertion_weight = 0.001
_deletion_weight = 1
_substitution_weight = 1


def fuzzy_match_score(source: str, target: str, words, threshold: float) -> float:
    m = len(source)
    n = len(target)
    a = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        a[i][0] = i

    for i in range(n + 1):
        a[0][i] = i * _insertion_weight

    def strip_vowels(s):
        return re.sub('[aeoiu]', '', s)

    word_match_bonus = 0.1 * max(max(sum(a == b for a, b in zip(source, w)) for w in words),
                                 max(sum(a == b for a, b in
                                         zip(source[0] + strip_vowels(source[1:]), w[0] + strip_vowels(w[1:]))) for w in
                                     words),
                                 sum(a == b for a, b in zip(source, ''.join(w[0] for w in words))))

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            a[i][j] = min(a[i - 1][j - 1] + _substitution_weight if source[i - 1] != target[j - 1] else a[i - 1][j - 1],
                          a[i - 1][j] + _deletion_weight,
                          a[i][j - 1] + _insertion_weight)
            if j == n and (a[i][j] - (m - i) * _insertion_weight - word_match_bonus) > threshold:
                return 9999

    return a[m][n] - word_match_bonus


def romanize(s: str) -> Tuple[str, Tuple[str]]:
    kks = pykakasi.kakasi()
    s = re.sub('[\']', '', s)
    s = re.sub('[A-Za-z]+', lambda ele: f' {ele[0]} ', s)
    s = ' '.join(c['hepburn'].strip().lower() for c in kks.convert(s))
    s = re.sub(r'[^a-zA-Z0-9_ ]+', '', s)
    words = tuple(s.split())
    return ''.join(words), words
