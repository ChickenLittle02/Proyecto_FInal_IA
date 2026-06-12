"""Prueba del pipeline beam search con mock (sin llamadas a la API)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.llm.client import SummaryEvaluation
from src.llm.scoring import build_llm_scores
from src.problem import Fragment, SelectionProblem
from src.solver.llm_assisted import (
    DEFAULT_SUMMARY_REFINE_TOP_M,
    refine_with_summary_judge,
    solve,
)
from src.solver.unified import unified_solve


class MockLLMClient:
    """Cliente simulado con puntuaciones fijas."""

    def __init__(
        self,
        relevance: list[float],
        coherence: dict[tuple[int, int], float],
        summary_overall: dict[str, float] | None = None,
    ):
        self.relevance = relevance
        self.coherence = coherence
        self.summary_overall = summary_overall or {}

    def score_fragment(self, fragment: Fragment) -> float:
        idx = int(fragment.id) - 1
        return self.relevance[idx]

    def score_coherence(self, first_fragment: Fragment, second_fragment: Fragment) -> float:
        i = int(first_fragment.id) - 1
        j = int(second_fragment.id) - 1
        return self.coherence.get((i, j), 0.0)

    def evaluate_summary(self, summary_text: str, max_duration: float) -> SummaryEvaluation:
        key = summary_text.strip()
        overall = self.summary_overall.get(key, 0.5)
        return SummaryEvaluation(relevance=overall, coherence=overall, overall=overall)


def build_jump_instance() -> SelectionProblem:
    """Instancia donde el beam elige [0, 2] saltando el fragmento puente."""
    fragments = [
        Fragment(id="1", text="A", duration=4.0, start_time=0.0, end_time=4.0),
        Fragment(id="2", text="B", duration=4.0, start_time=4.0, end_time=8.0),
        Fragment(id="3", text="C", duration=4.0, start_time=8.0, end_time=12.0),
    ]
    return SelectionProblem(fragments=fragments, max_duration=8.0)


def test_refine_prefers_summary_judge_over_local_score() -> None:
    """El juez macro puede elegir un candidato distinto al mejor score local."""
    problem = build_jump_instance()
    mock = MockLLMClient(
        relevance=[5.0, 5.0, 5.0],
        coherence={
            (0, 1): 0.8,
            (1, 2): 0.5,
            (0, 2): 0.95,
        },
        summary_overall={
            "A\n\nC": 0.4,
            "A\n\nB": 0.95,
        },
    )
    candidates = unified_solve(
        problem,
        mock.relevance,
        build_llm_scores(problem, mock).coherence,
        beam_width=10,
        top_m=2,
    )
    assert len(candidates) >= 2

    refined_indices, _, evaluation = refine_with_summary_judge(candidates, problem, mock)
    assert refined_indices == [0, 1]
    assert evaluation.overall == 0.95


def main() -> None:
    problem = build_jump_instance()
    coherence_weight = 0.25

    mock = MockLLMClient(
        relevance=[5.0, 5.0, 5.0],
        coherence={
            (0, 1): 0.8,
            (1, 2): 0.5,
            (0, 2): 0.95,
        },
    )

    scores = build_llm_scores(problem, mock)
    beam_candidates = unified_solve(
        problem,
        scores.relevance,
        scores.coherence,
        beam_width=10,
        coherence_weight=coherence_weight,
        top_m=1,
    )
    beam_indices, beam_score = beam_candidates[0]
    solve_indices, solve_score, mode, summary_eval = solve(
        problem,
        mock,
        coherence_weight,
        summary_refine_top_m=DEFAULT_SUMMARY_REFINE_TOP_M,
    )

    print("=== Prueba solver beam (mock, sin API) ===")
    print(f"Beam directo:  índices={beam_indices}, score={beam_score:.4f}")
    print(
        f"solve():       índices={solve_indices}, score={solve_score:.4f}, "
        f"mode={mode}, summary_overall={summary_eval.overall if summary_eval else None}"
    )

    assert beam_indices == [0, 2], f"Beam debería elegir [0,2], obtuvo {beam_indices}"
    assert solve_indices == beam_indices
    assert mode == "llm_beam"
    assert summary_eval is not None

    test_refine_prefers_summary_judge_over_local_score()

    print("\n[ÉXITO] Beam search elige la selección con mejor coherencia al saltar fragmentos.")


if __name__ == "__main__":
    main()
