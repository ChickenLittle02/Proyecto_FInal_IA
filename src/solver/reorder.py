"""
DP con máscara de bits para selección y reordenación de fragmentos.

A diferencia del knapsack ordenado (subsecuencia del array de entrada), este solver
elige un subconjunto y una permutación que maximiza relevancia + coherencia entre
pares consecutivos en el orden de salida.
"""
from functools import lru_cache
from typing import Callable, List, Tuple

from ..problem import Fragment


def unordered_knapsack_dp_with_coherence(
    fragments: List[Fragment],
    relevance_scores: List[float],
    max_duration: float,
    coherence_fn: Callable[[int, int], float],
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """DP exacto con estado (mask, last, remaining).

    mask: bitmask de fragmentos ya incluidos en el resumen.
    last: índice del último fragmento añadido (-1 si vacío).
    remaining: duración disponible.

    Complejidad O(2^n · n · capacidad); viable para n <= 12.
    Devuelve el orden de reproducción (no necesariamente índices crecientes).
    """
    n = len(fragments)
    if n == 0:
        return [], 0.0

    durations = [fragment.duration for fragment in fragments]
    capacity = round(max_duration, 6)

    @lru_cache(maxsize=None)
    def dp(mask: int, last: int, remaining: float) -> Tuple[float, Tuple[int, ...]]:
        best_score = 0.0
        best_path: Tuple[int, ...] = ()

        for j in range(n):
            if mask & (1 << j):
                continue
            duration = durations[j]
            if duration > remaining:
                continue

            take_score = relevance_scores[j]
            if last >= 0:
                take_score += coherence_weight * coherence_fn(last, j)

            future_score, future_path = dp(
                mask | (1 << j),
                j,
                round(remaining - duration, 6),
            )
            total_score = take_score + future_score
            candidate_path = (j,) + future_path

            if total_score > best_score:
                best_score, best_path = total_score, candidate_path

        return best_score, best_path

    total_score, order = dp(0, -1, capacity)
    return list(order), total_score


def build_temporal_coherence_fn(
    fragments: List[Fragment],
) -> Callable[[int, int], float]:
    """Proxy de coherencia sin LLM: favorece pares en orden cronológico del video."""

    def coherence(i: int, j: int) -> float:
        delta = fragments[j].start_time - fragments[i].start_time
        if delta > 0:
            return max(0.0, 1.0 - delta / 40.0)
        return 0.1

    return coherence


def solve_baseline_reorder(
    fragments: List[Fragment],
    relevance_scores: List[float],
    max_duration: float,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """Baseline con reordenación usando coherencia temporal (start_time)."""
    coherence_fn = build_temporal_coherence_fn(fragments)
    return unordered_knapsack_dp_with_coherence(
        fragments,
        relevance_scores,
        max_duration,
        coherence_fn,
        coherence_weight,
    )
