"""Valida que bench_static_vs_dynamic.json produce selecciones distintas (mock)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.solver.llm_assisted import solve_with_llm, solve_with_llm_reorder, solve_with_llm_static
from src.test_llm_solver import MockLLMClient


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


def main() -> None:
    test_bench_static_vs_dynamic_differs_with_mock()
    test_bench_irrelevant_middle_skips_middle()
    test_bench_disordered_reorders_narrative()
    print("[ÉXITO] Instancias bench validadas con mock.")


if __name__ == "__main__":
    main()
