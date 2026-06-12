"""
Métricas estructurales y evaluación post-hoc con LLM para selecciones de fragmentos.
"""
from typing import Dict, List, Optional, Sequence, Tuple

from ..llm.client import LLMClient
from ..problem import SelectionProblem
from ..llm.scoring import build_relevance_scores


def total_source_duration(problem: SelectionProblem) -> float:
    return sum(fragment.duration for fragment in problem.fragments)


def structural_metrics(
    problem: SelectionProblem,
    selected_indices: Sequence[int],
    solver_score: float,
) -> Dict[str, float]:
    n_fragments = len(problem.fragments)
    n_selected = len(selected_indices)
    duration_used = problem.summary_duration(selected_indices)
    source_duration = total_source_duration(problem)

    return {
        "n_fragments": float(n_fragments),
        "n_selected": float(n_selected),
        "max_duration": problem.max_duration,
        "duration_used": duration_used,
        "duration_utilization": duration_used / problem.max_duration if problem.max_duration else 0.0,
        "fragment_coverage": n_selected / n_fragments if n_fragments else 0.0,
        "duration_coverage": duration_used / source_duration if source_duration else 0.0,
        "solver_score": solver_score,
    }


def evaluate_selection_with_llm(
    problem: SelectionProblem,
    selected_indices: Sequence[int],
    llm_client: LLMClient,
    relevance_scores: Optional[List[float]] = None,
    coherence_weight: float = 0.25,
) -> Dict[str, float]:
    if relevance_scores is None:
        relevance_scores = build_relevance_scores(problem, llm_client)

    pair_scores: Dict[Tuple[int, int], float] = {}
    if len(selected_indices) >= 2:
        for first, second in zip(selected_indices, selected_indices[1:]):
            pair_scores[(first, second)] = llm_client.score_coherence(
                problem.fragments[first],
                problem.fragments[second],
            )

    mean_relevance = (
        sum(relevance_scores[i] for i in selected_indices) / len(selected_indices)
        if selected_indices
        else 0.0
    )
    mean_coherence = (
        sum(pair_scores.values()) / len(pair_scores) if pair_scores else 0.0
    )
    objective = SelectionProblem.objective_score(
        relevance_scores,
        pair_scores,
        selected_indices,
        coherence_weight=coherence_weight,
    )

    return {
        "mean_relevance": mean_relevance,
        "mean_coherence": mean_coherence,
        "objective_score": objective,
    }


def build_result_row(
    instance_name: str,
    solver_name: str,
    selected_indices: Sequence[int],
    structural: Dict[str, float],
    llm_metrics: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    row: Dict[str, object] = {
        "instance": instance_name,
        "solver": solver_name,
        "selected_indices": list(selected_indices),
        **structural,
    }
    if llm_metrics:
        row.update(llm_metrics)
    else:
        row.update({
            "mean_relevance": "",
            "mean_coherence": "",
            "objective_score": "",
        })
    return row
