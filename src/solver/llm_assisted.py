"""
Solver asistido por LLM que usa puntuaciones de relevancia y coherencia.
"""
from functools import lru_cache
from typing import Callable, Dict, List, Tuple

from ..llm.client import LLMClient
from ..problem import Fragment, SelectionProblem
from .baseline import ordered_knapsack_dp
from .reorder import (
    heuristic_reorder_with_coherence,
    solve_baseline_heuristic_reorder,
    solve_baseline_reorder,
    unordered_knapsack_dp_with_coherence,
)

REORDER_EXACT_LIMIT = 12


def compute_relevance_with_llm(
    problem: SelectionProblem,
    llm_client: LLMClient,
) -> List[float]:
    return [llm_client.score_fragment(fragment) for fragment in problem.fragments]


def ordered_knapsack_dp_with_coherence(
    fragments: List[Fragment],
    relevance_scores: List[float],
    max_duration: float,
    coherence_fn: Callable[[int, int], float],
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """DP con estado (índice, duración restante, último seleccionado).

    Al tomar el fragmento j se suma relevancia[j] + peso × coherencia(último, j).
    last_selected = -1 cuando aún no hay ningún fragmento en la selección.
    """
    n = len(fragments)

    @lru_cache(maxsize=None)
    def dp(index: int, remaining: float, last_selected: int) -> Tuple[float, Tuple[int, ...]]:
        if index == n:
            return 0.0, ()

        skip_score, skip_indices = dp(index + 1, remaining, last_selected)
        best_score, best_indices = skip_score, skip_indices

        duration = fragments[index].duration
        if duration <= remaining:
            take_score = relevance_scores[index]
            if last_selected >= 0:
                take_score += coherence_weight * coherence_fn(last_selected, index)
            future_score, future_indices = dp(
                index + 1, round(remaining - duration, 6), index
            )
            take_score += future_score
            take_indices = (index,) + future_indices
            if take_score > best_score:
                best_score, best_indices = take_score, take_indices

        return best_score, best_indices

    total_score, selected_indices = dp(0, round(max_duration, 6), -1)
    return list(selected_indices), total_score


def solve_with_llm_static(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """Enfoque estático (Paso B): coherencia solo entre pares consecutivos (i, i+1)."""
    relevance_scores = compute_relevance_with_llm(problem, llm_client)

    if not problem.fragments:
        return [], 0.0

    combined_scores: List[float] = []
    for i in range(len(problem.fragments)):
        coherence_bonus = 0.0
        if i + 1 < len(problem.fragments):
            coherence_bonus = llm_client.score_coherence(
                problem.fragments[i], problem.fragments[i + 1]
            )
        combined_scores.append(relevance_scores[i] + coherence_weight * coherence_bonus)

    return ordered_knapsack_dp(problem.fragments, combined_scores, problem.max_duration)


def solve_with_llm(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    relevance_scores = compute_relevance_with_llm(problem, llm_client)

    if not problem.fragments:
        return [], 0.0

    coherence_memo: Dict[Tuple[int, int], float] = {}

    def get_coherence(i: int, j: int) -> float:
        key = (i, j)
        if key not in coherence_memo:
            coherence_memo[key] = llm_client.score_coherence(
                problem.fragments[i], problem.fragments[j]
            )
        return coherence_memo[key]

    return ordered_knapsack_dp_with_coherence(
        problem.fragments,
        relevance_scores,
        problem.max_duration,
        get_coherence,
        coherence_weight,
    )


def solve_with_llm_reorder(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """Selección + reordenación: matriz de coherencia completa y DP con bitmask."""
    relevance_scores = compute_relevance_with_llm(problem, llm_client)

    if not problem.fragments:
        return [], 0.0

    coherence_memo: Dict[Tuple[int, int], float] = {}

    def get_coherence(i: int, j: int) -> float:
        key = (i, j)
        if key not in coherence_memo:
            coherence_memo[key] = llm_client.score_coherence(
                problem.fragments[i], problem.fragments[j]
            )
        return coherence_memo[key]

    return unordered_knapsack_dp_with_coherence(
        problem.fragments,
        relevance_scores,
        problem.max_duration,
        get_coherence,
        coherence_weight,
    )


def solve_with_llm_heuristic_reorder(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    """Selección + reordenación heurística para n > REORDER_EXACT_LIMIT."""
    relevance_scores = compute_relevance_with_llm(problem, llm_client)

    if not problem.fragments:
        return [], 0.0

    coherence_memo: Dict[Tuple[int, int], float] = {}

    def get_coherence(i: int, j: int) -> float:
        key = (i, j)
        if key not in coherence_memo:
            coherence_memo[key] = llm_client.score_coherence(
                problem.fragments[i], problem.fragments[j]
            )
        return coherence_memo[key]

    return heuristic_reorder_with_coherence(
        problem.fragments,
        relevance_scores,
        problem.max_duration,
        get_coherence,
        coherence_weight,
    )


def resolve_solver_mode(problem: SelectionProblem) -> str:
    """Devuelve 'exact_reorder' si n <= REORDER_EXACT_LIMIT, else 'heuristic_reorder'."""
    if len(problem.fragments) <= REORDER_EXACT_LIMIT:
        return "exact_reorder"
    return "heuristic_reorder"


def log_solver_mode(mode: str, problem: SelectionProblem) -> None:
    n = len(problem.fragments)
    if mode == "exact_reorder":
        print(f"Solver: exact_reorder (n={n})")
        return
    disordered = not problem.validate_order()
    suffix = ", input desordenado según start_time" if disordered else ""
    print(f"Solver: heuristic_reorder (n={n}{suffix})")


def solve(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float, str]:
    """Punto de entrada único LLM. Siempre devuelve orden de reproducción."""
    mode = resolve_solver_mode(problem)
    log_solver_mode(mode, problem)

    if mode == "exact_reorder":
        indices, score = solve_with_llm_reorder(problem, llm_client, coherence_weight)
        return indices, score, mode

    indices, score = solve_with_llm_heuristic_reorder(problem, llm_client, coherence_weight)
    return indices, score, mode


def solve_baseline(
    problem: SelectionProblem,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float, str]:
    """Punto de entrada único sin LLM. Mismo enrutado que solve()."""
    mode = resolve_solver_mode(problem)
    log_solver_mode(mode, problem)

    if mode == "exact_reorder":
        if not problem.fragments:
            return [], 0.0, mode
        relevance_scores = [1.0] * len(problem.fragments)
        indices, score = solve_baseline_reorder(
            problem.fragments,
            relevance_scores,
            problem.max_duration,
            coherence_weight,
        )
        return indices, score, mode

    if not problem.fragments:
        return [], 0.0, mode
    relevance_scores = [1.0] * len(problem.fragments)
    indices, score = solve_baseline_heuristic_reorder(
        problem.fragments,
        relevance_scores,
        problem.max_duration,
        coherence_weight,
    )
    return indices, score, mode
