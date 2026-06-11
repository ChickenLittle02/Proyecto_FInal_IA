"""Valida que bench_static_vs_dynamic.json produce selecciones distintas (mock)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.problem import Fragment, SelectionProblem
from src.solver.llm_assisted import (
    solve,
    solve_baseline,
    solve_with_llm,
    solve_with_llm_reorder,
    solve_with_llm_static,
)
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


def test_bench_static_vs_dynamic_differs_with_mock() -> None:
    bench_path = root / "data" / "instances" / "bench_static_vs_dynamic.json"
    problem = load_instance_file(str(bench_path))

    # Patrón jump (test_llm_solver): estático prefiere [0,1]; dinámico salta a [0,2].
    mock = MockLLMClient(
        relevance=[5.0, 5.0, 5.0, 0.1, 0.1],
        coherence={
            (0, 1): 0.8,
            (1, 2): 0.5,
            (0, 2): 0.95,
        },
    )

    static_indices, _ = solve_with_llm_static(problem, mock, coherence_weight=0.25)
    dynamic_indices, _ = solve_with_llm(problem, mock, coherence_weight=0.25)

    assert static_indices != dynamic_indices, (
        f"Se esperaba selección distinta; estático={static_indices}, dinámico={dynamic_indices}"
    )


def test_bench_irrelevant_middle_skips_middle() -> None:
    bench_path = root / "data" / "instances" / "bench_irrelevant_middle.json"
    problem = load_instance_file(str(bench_path))

    mock = MockLLMClient(
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

    dynamic_indices, _ = solve_with_llm(problem, mock, coherence_weight=0.25)
    assert 2 not in dynamic_indices, f"El fragmento irrelevante (índice 2) no debería seleccionarse: {dynamic_indices}"


def test_solve_unified_disordered_reorders_narrative() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))

    mock = MockLLMClient(
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

    indices, _, mode = solve(problem, mock, coherence_weight=0.25)
    assert mode == "exact_reorder"
    assert 2 not in indices, f"El fragmento irrelevante (índice 2) no debería seleccionarse: {indices}"
    assert indices == [1, 4, 3, 0], f"Se esperaba orden narrativo [1, 4, 3, 0]; obtuvo {indices}"
    assert problem.is_valid_ordered_selection(indices)


def test_solve_unified_irrelevant_middle_skips_middle() -> None:
    bench_path = root / "data" / "instances" / "bench_irrelevant_middle.json"
    problem = load_instance_file(str(bench_path))

    mock = MockLLMClient(
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

    indices, _, mode = solve(problem, mock, coherence_weight=0.25)
    assert mode == "exact_reorder"
    assert 2 not in indices, f"El fragmento irrelevante (índice 2) no debería seleccionarse: {indices}"


def test_bench_disordered_reorders_narrative() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))

    # Coherencia por id original (MockLLMClient usa fragment.id - 1).
    mock = MockLLMClient(
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

    reorder_indices, _ = solve_with_llm_reorder(problem, mock, coherence_weight=0.25)
    ordered_indices, _ = solve_with_llm(problem, mock, coherence_weight=0.25)

    assert 2 not in reorder_indices, (
        f"El fragmento irrelevante (índice 2) no debería seleccionarse: {reorder_indices}"
    )
    assert reorder_indices == [1, 4, 3, 0], (
        f"Se esperaba orden narrativo [1, 4, 3, 0]; obtuvo {reorder_indices}"
    )
    assert problem.is_valid_ordered_selection(reorder_indices)
    assert ordered_indices != reorder_indices, (
        f"El solver ordenado no debería recuperar el orden narrativo: {ordered_indices}"
    )


def test_solve_heuristic_large_disordered() -> None:
    problem = build_large_disordered_problem()
    mock = build_large_disordered_mock()

    indices, _, mode = solve(problem, mock, coherence_weight=0.25)
    expected_order = [index for index in range(14, -1, -1) if index != 7]

    assert mode == "heuristic_reorder"
    assert len(problem.fragments) == 15
    assert 7 not in indices, f"El fragmento irrelevante (índice 7) no debería seleccionarse: {indices}"
    assert indices == expected_order, f"Se esperaba orden cronológico {expected_order}; obtuvo {indices}"
    assert problem.is_valid_ordered_selection(indices)

    baseline_indices, _, baseline_mode = solve_baseline(problem, coherence_weight=0.25)
    assert baseline_mode == "heuristic_reorder"
    assert problem.is_valid_ordered_selection(baseline_indices)
    assert len(baseline_indices) == 14


def main() -> None:
    test_bench_static_vs_dynamic_differs_with_mock()
    test_bench_irrelevant_middle_skips_middle()
    test_solve_unified_disordered_reorders_narrative()
    test_solve_unified_irrelevant_middle_skips_middle()
    test_solve_heuristic_large_disordered()
    test_bench_disordered_reorders_narrative()
    print("[ÉXITO] Instancias bench validadas con mock.")


if __name__ == "__main__":
    main()
