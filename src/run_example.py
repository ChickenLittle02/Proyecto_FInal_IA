"""Ejemplo rápido de carga de instancia y selección clásica."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.solver.baseline import ordered_knapsack_dp


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    instance_path = root / "data" / "instances" / "example_instance.json"
    problem = load_instance_file(str(instance_path))

    print("Instancia cargada:")
    print(f"- fragmentos: {len(problem.fragments)}")
    print(f"- duración máxima: {problem.max_duration}")

    scores = [1.0 for _ in problem.fragments]
    selected_indices, total_score = ordered_knapsack_dp(problem.fragments, scores, problem.max_duration)

    print("\nSelección resultante (solver clásico):")
    print(f"- índice(s): {selected_indices}")
    print(f"- duración total: {problem.summary_duration(selected_indices)}")
    print(f"- puntuación total: {total_score}")
    print("\nFragmentos seleccionados:")
    for idx in selected_indices:
        fragment = problem.fragments[idx]
        print(f"  {fragment.id}. {fragment.text} ({fragment.duration}s)")


if __name__ == "__main__":
    main()
