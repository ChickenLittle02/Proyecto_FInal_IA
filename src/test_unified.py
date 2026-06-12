"""Tests del pipeline unificado: scoring + beam search (Fase 2, F1)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.llm.scoring import (
    build_baseline_scores,
    build_coherence_matrix,
    build_llm_scores,
)
from src.problem import Fragment, SelectionProblem
from src.solver.unified import beam_search_select_and_order, unified_solve
from src.test_llm_solver import MockLLMClient


def _bench_disordered_mock() -> MockLLMClient:
    return MockLLMClient(
        relevance=[0.9, 0.95, 0.1, 0.9, 0.85],
        coherence={
            (0, 1): 0.8,
            (1, 2): 0.3,
            (2, 3): 0.2,
            (3, 4): 0.85,
            (0, 2): 0.1,
            (1, 3): 0.75,
            (0, 4): 0.5,
        },
    )


def test_build_llm_scores_uses_cache_without_duplicate_calls() -> None:
    problem = SelectionProblem(
        fragments=[
            Fragment(id="1", text="A", duration=1.0, start_time=0.0, end_time=1.0),
            Fragment(id="2", text="B", duration=1.0, start_time=1.0, end_time=2.0),
        ],
        max_duration=2.0,
    )
    mock = MockLLMClient(
        relevance=[0.5, 0.7],
        coherence={(0, 1): 0.6, (1, 0): 0.4},
    )

    first = build_llm_scores(problem, mock)
    second = build_llm_scores(problem, mock)

    assert first.relevance == [0.5, 0.7]
    assert first.coherence[0][1] == 0.6
    assert first.coherence[1][0] == 0.4
    assert first.coherence[0][0] == 0.0
    assert second.relevance == first.relevance
    assert second.coherence == first.coherence


def test_beam_bench_disordered_reorders_narrative() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))
    mock = _bench_disordered_mock()
    scores = build_llm_scores(problem, mock)

    indices, score = unified_solve(problem, scores.relevance, scores.coherence, beam_width=10)[0]

    assert 2 not in indices, f"Fragmento irrelevante (2) no debería seleccionarse: {indices}"
    assert indices == [1, 4, 3, 0], f"Se esperaba [1, 4, 3, 0]; obtuvo {indices}"
    assert problem.is_valid_ordered_selection(indices)
    assert score > 0.0


def test_beam_bench_irrelevant_middle_skips_middle() -> None:
    bench_path = root / "data" / "instances" / "bench_irrelevant_middle.json"
    problem = load_instance_file(str(bench_path))
    mock = _bench_disordered_mock()
    scores = build_llm_scores(problem, mock)

    indices, _ = unified_solve(problem, scores.relevance, scores.coherence, beam_width=10)[0]
    assert 2 not in indices, f"Fragmento irrelevante (2) no debería seleccionarse: {indices}"


def test_beam_large_disordered_n15_skips_irrelevant() -> None:
    """n=15: valida omisión del irrelevante; orden exacto se refina en F2."""
    n = 15
    fragments_chrono = [
        Fragment(
            id=str(index + 1),
            text=f"segmento {index + 1}",
            duration=5.0,
            start_time=float(index * 10),
            end_time=float((index + 1) * 10),
        )
        for index in range(n)
    ]
    permutation = list(reversed(range(n)))
    fragments = [fragments_chrono[index] for index in permutation]
    problem = SelectionProblem(fragments=fragments, max_duration=70.0)

    relevance = [0.9] * n
    relevance[7] = 0.1
    coherence: dict[tuple[int, int], float] = {}
    for first in range(n):
        for second in range(n):
            if first < second:
                coherence[(first, second)] = 0.9
            elif first > second:
                coherence[(first, second)] = 0.1

    mock = MockLLMClient(relevance=relevance, coherence=coherence)
    matrix = build_coherence_matrix(problem, mock)

    indices, _ = unified_solve(problem, relevance, matrix, beam_width=10)[0]

    assert 7 not in indices
    assert len(indices) == 14
    assert problem.is_valid_ordered_selection(indices)


def test_baseline_scores_and_beam() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))
    scores = build_baseline_scores(problem)

    indices, _ = unified_solve(problem, scores.relevance, scores.coherence, beam_width=10)[0]
    assert problem.is_valid_ordered_selection(indices)
    assert len(indices) >= 1


def test_beam_top_m_returns_distinct_candidates() -> None:
    problem = SelectionProblem(
        fragments=[
            Fragment(id="1", text="A", duration=4.0, start_time=0.0, end_time=4.0),
            Fragment(id="2", text="B", duration=4.0, start_time=4.0, end_time=8.0),
            Fragment(id="3", text="C", duration=4.0, start_time=8.0, end_time=12.0),
        ],
        max_duration=8.0,
    )
    relevance = [5.0, 5.0, 5.0]
    coherence = [
        [0.0, 0.8, 0.95],
        [0.0, 0.0, 0.5],
        [0.0, 0.0, 0.0],
    ]

    candidates = beam_search_select_and_order(
        problem.fragments,
        relevance,
        coherence,
        problem.max_duration,
        beam_width=10,
        top_m=3,
    )

    orders = [order for order, _ in candidates]
    assert len(candidates) >= 2
    assert all(len(order) >= 1 for order in orders)
    assert len({tuple(order) for order in orders}) == len(orders)


def main() -> None:
    test_build_llm_scores_uses_cache_without_duplicate_calls()
    test_beam_bench_disordered_reorders_narrative()
    test_beam_bench_irrelevant_middle_skips_middle()
    test_beam_large_disordered_n15_skips_irrelevant()
    test_baseline_scores_and_beam()
    test_beam_top_m_returns_distinct_candidates()
    print("[ÉXITO] Pipeline unificado (scoring + beam) validado con mock.")


if __name__ == "__main__":
    main()
