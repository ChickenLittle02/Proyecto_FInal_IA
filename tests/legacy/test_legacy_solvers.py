"""Tests de solvers legacy (Task E): DP, heurística, estático vs dinámico."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.problem import Fragment, SelectionProblem
from src.test_llm_solver import MockLLMClient
from tests.legacy.baseline import ordered_knapsack_dp
from tests.legacy.reorder import unordered_knapsack_dp_with_coherence


def solve_with_llm_static_legacy(
    problem: SelectionProblem,
    mock: MockLLMClient,
    coherence_weight: float = 0.25,
) -> tuple[list[int], float]:
    relevance = [mock.score_fragment(f) for f in problem.fragments]
    combined: list[float] = []
    for i in range(len(problem.fragments)):
        bonus = 0.0
        if i + 1 < len(problem.fragments):
            bonus = mock.score_coherence(problem.fragments[i], problem.fragments[i + 1])
        combined.append(relevance[i] + coherence_weight * bonus)
    return ordered_knapsack_dp(problem.fragments, combined, problem.max_duration)


def solve_with_llm_legacy(
    problem: SelectionProblem,
    mock: MockLLMClient,
    coherence_weight: float = 0.25,
) -> tuple[list[int], float]:
    from functools import lru_cache

    relevance = [mock.score_fragment(f) for f in problem.fragments]
    memo: dict[tuple[int, int], float] = {}

    def get_coherence(i: int, j: int) -> float:
        key = (i, j)
        if key not in memo:
            memo[key] = mock.score_coherence(problem.fragments[i], problem.fragments[j])
        return memo[key]

    n = len(problem.fragments)

    @lru_cache(maxsize=None)
    def dp(index: int, remaining: float, last_selected: int) -> tuple[float, tuple[int, ...]]:
        if index == n:
            return 0.0, ()
        skip_score, skip_indices = dp(index + 1, remaining, last_selected)
        best_score, best_indices = skip_score, skip_indices
        duration = problem.fragments[index].duration
        if duration <= remaining:
            take_score = relevance[index]
            if last_selected >= 0:
                take_score += coherence_weight * get_coherence(last_selected, index)
            future_score, future_indices = dp(index + 1, round(remaining - duration, 6), index)
            take_score += future_score
            take_indices = (index,) + future_indices
            if take_score > best_score:
                best_score, best_indices = take_score, take_indices
        return best_score, best_indices

    total_score, selected = dp(0, round(problem.max_duration, 6), -1)
    return list(selected), total_score


def solve_with_llm_reorder_legacy(
    problem: SelectionProblem,
    mock: MockLLMClient,
    coherence_weight: float = 0.25,
) -> tuple[list[int], float]:
    relevance = [mock.score_fragment(f) for f in problem.fragments]
    memo: dict[tuple[int, int], float] = {}

    def get_coherence(i: int, j: int) -> float:
        key = (i, j)
        if key not in memo:
            memo[key] = mock.score_coherence(problem.fragments[i], problem.fragments[j])
        return memo[key]

    return unordered_knapsack_dp_with_coherence(
        problem.fragments,
        relevance,
        problem.max_duration,
        get_coherence,
        coherence_weight,
    )


def test_bench_static_vs_dynamic_differs_with_mock() -> None:
    bench_path = root / "data" / "instances" / "bench_static_vs_dynamic.json"
    problem = load_instance_file(str(bench_path))
    mock = MockLLMClient(
        relevance=[5.0, 5.0, 5.0, 0.1, 0.1],
        coherence={(0, 1): 0.8, (1, 2): 0.5, (0, 2): 0.95},
    )
    static_indices, _ = solve_with_llm_static_legacy(problem, mock)
    dynamic_indices, _ = solve_with_llm_legacy(problem, mock)
    assert static_indices != dynamic_indices


def test_bench_disordered_reorders_narrative_legacy_dp() -> None:
    bench_path = root / "data" / "instances" / "bench_disordered.json"
    problem = load_instance_file(str(bench_path))
    mock = MockLLMClient(
        relevance=[0.9, 0.95, 0.1, 0.9, 0.85],
        coherence={
            (0, 1): 0.8, (1, 2): 0.3, (2, 3): 0.2, (3, 4): 0.85,
            (0, 2): 0.1, (1, 3): 0.75, (0, 4): 0.5,
        },
    )
    reorder_indices, _ = solve_with_llm_reorder_legacy(problem, mock)
    ordered_indices, _ = solve_with_llm_legacy(problem, mock)
    assert 2 not in reorder_indices
    assert reorder_indices == [1, 4, 3, 0]
    assert ordered_indices != reorder_indices


def main() -> None:
    test_bench_static_vs_dynamic_differs_with_mock()
    test_bench_disordered_reorders_narrative_legacy_dp()
    print("[ÉXITO] Tests legacy (Task E) validados.")


if __name__ == "__main__":
    main()
