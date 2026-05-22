"""
Solver asistido por LLM que usa puntuaciones de relevancia y coherencia.
"""
from typing import Dict, List, Optional, Tuple

from ..llm.client import LLMClient
from ..problem import SelectionProblem
from .baseline import ordered_knapsack_dp


def compute_scores_with_llm(
    problem: SelectionProblem,
    llm_client: LLMClient,
) -> Tuple[List[float], Dict[Tuple[int, int], float]]:
    relevance_scores: List[float] = []
    coherence_scores: Dict[Tuple[int, int], float] = {}

    for idx, fragment in enumerate(problem.fragments):
        relevance_scores.append(llm_client.score_fragment(fragment))

    for i in range(len(problem.fragments) - 1):
        coherence_scores[(i, i + 1)] = llm_client.score_coherence(
            problem.fragments[i], problem.fragments[i + 1]
        )

    return relevance_scores, coherence_scores


def solve_with_llm(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
) -> Tuple[List[int], float]:
    relevance_scores, coherence_scores = compute_scores_with_llm(problem, llm_client)

    if not problem.fragments:
        return [], 0.0

    combined_scores: List[float] = []
    for i in range(len(problem.fragments)):
        coherence_bonus = coherence_scores.get((i, i + 1), 0.0)
        combined_scores.append(relevance_scores[i] + coherence_weight * coherence_bonus)

    return ordered_knapsack_dp(problem.fragments, combined_scores, problem.max_duration)
