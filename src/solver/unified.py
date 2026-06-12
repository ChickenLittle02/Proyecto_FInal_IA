"""
Solver unificado: beam search para selección y ordenación de fragmentos.

No realiza llamadas al LLM; consume matrices precalculadas (relevance + coherence).
"""
from typing import List, Sequence, Tuple

from ..problem import Fragment, SelectionProblem

BeamCandidate = Tuple[List[int], float]


def score_path(
    order: Sequence[int],
    relevance: Sequence[float],
    coherence: Sequence[Sequence[float]],
    coherence_weight: float = 0.25,
) -> float:
    if not order:
        return 0.0
    total = sum(relevance[i] for i in order)
    for first, second in zip(order, order[1:]):
        total += coherence_weight * coherence[first][second]
    return total


def _register_top_candidate(
    candidates: List[BeamCandidate],
    order: Sequence[int],
    score: float,
    top_m: int,
) -> None:
    if not order or top_m <= 0:
        return
    order_list = list(order)
    for existing_order, _ in candidates:
        if existing_order == order_list:
            return
    candidates.append((order_list, score))
    candidates.sort(key=lambda item: item[1], reverse=True)
    del candidates[top_m:]


def beam_search_select_and_order(
    fragments: List[Fragment],
    relevance: Sequence[float],
    coherence: Sequence[Sequence[float]],
    max_duration: float,
    beam_width: int = 10,
    coherence_weight: float = 0.25,
    top_m: int = 1,
) -> List[BeamCandidate]:
    """Selecciona y ordena fragmentos; devuelve hasta top-M candidatos por score local."""
    n = len(fragments)
    if n == 0:
        return []

    effective_top_m = max(1, top_m)
    durations = [fragment.duration for fragment in fragments]
    capacity = max_duration

    # Estado: (orden parcial, score acumulado, duración usada)
    beam: List[Tuple[Tuple[int, ...], float, float]] = [(tuple(), 0.0, 0.0)]
    top_candidates: List[BeamCandidate] = []

    for _ in range(n):
        candidates: List[Tuple[Tuple[int, ...], float, float]] = []

        for order, score, used_duration in beam:
            _register_top_candidate(top_candidates, order, score, effective_top_m)

            used = set(order)
            last = order[-1] if order else None

            for j in range(n):
                if j in used:
                    continue
                next_duration = used_duration + durations[j]
                if next_duration > capacity + 1e-9:
                    continue

                rel_add = relevance[j]
                coh_add = (
                    coherence_weight * coherence[last][j] if last is not None else 0.0
                )
                new_order = order + (j,)
                new_score = score + rel_add + coh_add
                candidates.append((new_order, new_score, next_duration))

        if not candidates:
            break

        candidates.sort(key=lambda item: item[1], reverse=True)
        seen: set[Tuple[int, ...]] = set()
        next_beam: List[Tuple[Tuple[int, ...], float, float]] = []
        for order, score, used_duration in candidates:
            if order in seen:
                continue
            seen.add(order)
            next_beam.append((order, score, used_duration))
            if len(next_beam) >= beam_width:
                break
        beam = next_beam

    for order, score, _ in beam:
        _register_top_candidate(top_candidates, order, score, effective_top_m)

    return top_candidates


def unified_solve(
    problem: SelectionProblem,
    relevance: Sequence[float],
    coherence: Sequence[Sequence[float]],
    beam_width: int = 10,
    coherence_weight: float = 0.25,
    top_m: int = 1,
) -> List[BeamCandidate]:
    """Punto de entrada interno del solver combinatorio unificado."""
    return beam_search_select_and_order(
        problem.fragments,
        relevance,
        coherence,
        problem.max_duration,
        beam_width,
        coherence_weight,
        top_m,
    )
