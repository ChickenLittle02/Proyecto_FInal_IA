"""
Solver clásico de selección ordenada de fragmentos usando programación dinámica.
"""
from functools import lru_cache
from typing import List, Tuple

from ..problem import Fragment


def ordered_knapsack_dp(
    fragments: List[Fragment],
    scores: List[float],
    max_duration: float,
) -> Tuple[List[int], float]:
    """Resuelve el problema de selección ordenada usando DP con capacidad continua."""
    n = len(fragments)

    @lru_cache(maxsize=None)
    def dp(index: int, remaining: float) -> Tuple[float, Tuple[int, ...]]:
        if index == n:
            return 0.0, ()

        skip_score, skip_indices = dp(index + 1, remaining)
        best_score, best_indices = skip_score, skip_indices

        duration = fragments[index].duration
        if duration <= remaining:
            take_score, take_indices = dp(index + 1, round(remaining - duration, 6))
            take_score += scores[index]
            take_indices = (index,) + take_indices
            if take_score > best_score:
                best_score, best_indices = take_score, take_indices

        return best_score, best_indices

    total_score, selected_indices = dp(0, round(max_duration, 6))
    return list(selected_indices), total_score


def greedy_by_score(
    fragments: List[Fragment],
    scores: List[float],
    max_duration: float,
) -> Tuple[List[int], float]:
    """Versión heurística para instancias más grandes."""
    indexed = sorted(
        enumerate(fragments),
        key=lambda item: scores[item[0]] / max(item[1].duration, 1e-6),
        reverse=True,
    )
    selected = []
    total_duration = 0.0
    total_score = 0.0
    for index, fragment in indexed:
        if total_duration + fragment.duration <= max_duration:
            selected.append(index)
            total_duration += fragment.duration
            total_score += scores[index]
    selected.sort()
    return selected, total_score
