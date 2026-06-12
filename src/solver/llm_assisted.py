"""
Punto de entrada del solver: precálculo cacheado + beam search unificado.

Política Fase 2: solo `baseline_beam` y `llm_beam` como modos ejecutables.
"""
from typing import List, Optional, Tuple

from ..llm.client import LLMClient, SummaryEvaluation
from ..llm.scoring import build_baseline_scores, build_llm_scores
from ..problem import SelectionProblem
from .unified import BeamCandidate, unified_solve

DEFAULT_BEAM_WIDTH = 10
DEFAULT_SUMMARY_REFINE_TOP_M = 3
SOLVER_MODE_LLM = "llm_beam"
SOLVER_MODE_BASELINE = "baseline_beam"


def log_solver_mode(mode: str, problem: SelectionProblem, beam_width: int = DEFAULT_BEAM_WIDTH) -> None:
    n = len(problem.fragments)
    print(f"Solver: {mode} (n={n}, beam={beam_width})")


def refine_with_summary_judge(
    candidates: List[BeamCandidate],
    problem: SelectionProblem,
    llm_client: LLMClient,
) -> Tuple[List[int], float, SummaryEvaluation]:
    """Evalúa cada candidato con el juez macro y elige el de mayor overall."""
    if not candidates:
        return [], 0.0, SummaryEvaluation(0.0, 0.0, 0.0)

    best_indices = candidates[0][0]
    best_local_score = candidates[0][1]
    best_eval = SummaryEvaluation(0.0, 0.0, 0.0)
    best_overall = -1.0

    for indices, local_score in candidates:
        summary_text = problem.summary_text(indices)
        evaluation = llm_client.evaluate_summary(summary_text, problem.max_duration)
        if evaluation.overall > best_overall:
            best_overall = evaluation.overall
            best_indices = indices
            best_local_score = local_score
            best_eval = evaluation

    return best_indices, best_local_score, best_eval


def solve(
    problem: SelectionProblem,
    llm_client: LLMClient,
    coherence_weight: float = 0.25,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    summary_refine_top_m: int = DEFAULT_SUMMARY_REFINE_TOP_M,
) -> Tuple[List[int], float, str, Optional[SummaryEvaluation]]:
    """Precalcula scores LLM, beam search top-M y refinamiento macro opcional."""
    if not problem.fragments:
        return [], 0.0, SOLVER_MODE_LLM, None

    log_solver_mode(SOLVER_MODE_LLM, problem, beam_width)
    scores = build_llm_scores(problem, llm_client)

    beam_top_m = max(summary_refine_top_m, 1) if summary_refine_top_m > 0 else 1
    candidates = unified_solve(
        problem,
        scores.relevance,
        scores.coherence,
        beam_width=beam_width,
        coherence_weight=coherence_weight,
        top_m=beam_top_m,
    )

    if summary_refine_top_m > 0:
        indices, score, summary_eval = refine_with_summary_judge(
            candidates, problem, llm_client
        )
        return indices, score, SOLVER_MODE_LLM, summary_eval

    indices, score = candidates[0] if candidates else ([], 0.0)
    return indices, score, SOLVER_MODE_LLM, None


def solve_baseline(
    problem: SelectionProblem,
    coherence_weight: float = 0.25,
    beam_width: int = DEFAULT_BEAM_WIDTH,
) -> Tuple[List[int], float, str]:
    """Beam search con relevancia uniforme y coherencia temporal (sin LLM)."""
    if not problem.fragments:
        return [], 0.0, SOLVER_MODE_BASELINE

    log_solver_mode(SOLVER_MODE_BASELINE, problem, beam_width)
    scores = build_baseline_scores(problem)
    candidates = unified_solve(
        problem,
        scores.relevance,
        scores.coherence,
        beam_width=beam_width,
        coherence_weight=coherence_weight,
        top_m=1,
    )
    indices, score = candidates[0] if candidates else ([], 0.0)
    return indices, score, SOLVER_MODE_BASELINE
