"""Prueba del solver LLM con mock (sin llamadas a la API)."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.problem import Fragment, SelectionProblem
from src.solver.llm_assisted import solve_with_llm, solve_with_llm_static


class MockLLMClient:
    """Cliente simulado con puntuaciones fijas para demostrar static vs dynamic."""

    def __init__(self, relevance: list[float], coherence: dict[tuple[int, int], float]):
        self.relevance = relevance
        self.coherence = coherence

    def score_fragment(self, fragment: Fragment) -> float:
        idx = int(fragment.id) - 1
        return self.relevance[idx]

    def score_coherence(self, first_fragment: Fragment, second_fragment: Fragment) -> float:
        i = int(first_fragment.id) - 1
        j = int(second_fragment.id) - 1
        return self.coherence.get((i, j), 0.0)


def build_jump_instance() -> SelectionProblem:
    """Instancia donde el enfoque estático y el dinámico eligen distinto."""
    fragments = [
        Fragment(id="1", text="A", duration=4.0, start_time=0.0, end_time=4.0),
        Fragment(id="2", text="B", duration=4.0, start_time=4.0, end_time=8.0),
        Fragment(id="3", text="C", duration=4.0, start_time=8.0, end_time=12.0),
    ]
    return SelectionProblem(fragments=fragments, max_duration=8.0)


def main() -> None:
    problem = build_jump_instance()
    coherence_weight = 0.25

    # coh(0,1) alta infla el score estático de f0 y f1 → prefiere [0,1];
    # coh(0,2) alta y coh(1,2) baja → el DP dinámico prefiere [0,2].
    mock = MockLLMClient(
        relevance=[5.0, 5.0, 5.0],
        coherence={
            (0, 1): 0.8,
            (1, 2): 0.5,
            (0, 2): 0.95,
        },
    )

    static_indices, static_score = solve_with_llm_static(problem, mock, coherence_weight)
    dynamic_indices, dynamic_score = solve_with_llm(problem, mock, coherence_weight)

    print("=== Prueba solver LLM (mock, sin API) ===")
    print(f"Enfoque estático:  índices={static_indices}, score={static_score:.4f}")
    print(f"Enfoque dinámico:  índices={dynamic_indices}, score={dynamic_score:.4f}")

    assert static_indices == [0, 1], f"Estático debería elegir [0,1], obtuvo {static_indices}"
    assert dynamic_indices == [0, 2], f"Dinámico debería elegir [0,2], obtuvo {dynamic_indices}"
    assert static_indices != dynamic_indices, "Las selecciones deben diferir cuando hay saltos"

    print("\n[ÉXITO] El DP dinámico elige distinto al estático en presencia de saltos.")


if __name__ == "__main__":
    main()
