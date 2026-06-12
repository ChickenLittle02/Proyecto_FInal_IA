"""Valida instancias bench con el pipeline beam search (Fase 2)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.problem import Fragment, SelectionProblem
from src.solver.llm_assisted import SOLVER_MODE_BASELINE, SOLVER_MODE_LLM, solve, solve_baseline
from src.test_llm_solver import MockLLMClient


def build_large_disordered_problem() -> SelectionProblem:
    """15 fragmentos permutados; id 8 irrelevante; orden lógico por start_time."""
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
    return SelectionProblem(fragments=fragments, max_duration=70.0)


def build_large_disordered_mock() -> MockLLMClient:
    n = 15
    relevance = [0.9] * n
    relevance[7] = 0.1
    coherence: dict[tuple[int, int], float] = {}
    for first in range(n):
        for second in range(n):
            if first < second:
                coherence[(first, second)] = 0.9
            elif first > second:
                coherence[(first, second)] = 0.1
    return MockLLMClient(relevance=relevance, coherence=coherence)


def _bench_mock() -> MockLLMClient:
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


def test_solve_disordered_reorders_narrative() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))
    mock = _bench_mock()

    indices, _, mode, _summary_eval = solve(problem, mock, coherence_weight=0.25)
    assert mode == SOLVER_MODE_LLM
    assert 2 not in indices, f"El fragmento irrelevante (índice 2) no debería seleccionarse: {indices}"
    assert indices == [1, 4, 3, 0], f"Se esperaba orden narrativo [1, 4, 3, 0]; obtuvo {indices}"
    assert problem.is_valid_ordered_selection(indices)


def test_solve_irrelevant_middle_skips_middle() -> None:
    bench_path = root / "data" / "instances" / "bench_irrelevant_middle.json"
    problem = load_instance_file(str(bench_path))
    mock = _bench_mock()

    indices, _, mode, _summary_eval = solve(problem, mock, coherence_weight=0.25)
    assert mode == SOLVER_MODE_LLM
    assert 2 not in indices, f"El fragmento irrelevante (índice 2) no debería seleccionarse: {indices}"


def test_solve_large_disordered_skips_irrelevant() -> None:
    problem = build_large_disordered_problem()
    mock = build_large_disordered_mock()

    indices, _, mode, _summary_eval = solve(problem, mock, coherence_weight=0.25)

    assert mode == SOLVER_MODE_LLM
    assert len(problem.fragments) == 15
    assert 7 not in indices, f"El fragmento irrelevante (índice 7) no debería seleccionarse: {indices}"
    assert len(indices) == 14
    assert problem.is_valid_ordered_selection(indices)

    baseline_indices, _, baseline_mode = solve_baseline(problem, coherence_weight=0.25)
    assert baseline_mode == SOLVER_MODE_BASELINE
    assert problem.is_valid_ordered_selection(baseline_indices)
    assert len(baseline_indices) == 14


def main() -> None:
    test_solve_disordered_reorders_narrative()
    test_solve_irrelevant_middle_skips_middle()
    test_solve_large_disordered_skips_irrelevant()
    print("[ÉXITO] Instancias bench validadas con beam search (mock).")


if __name__ == "__main__":
    main()
