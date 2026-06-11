"""Ejemplo rápido de carga de instancia y selección clásica o asistida por LLM."""
import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.instance import load_instance_file
from src.llm.client import LLMClient
from src.solver.baseline import ordered_knapsack_dp
from src.solver.llm_assisted import solve_with_llm


def resolve_instance_path(args: argparse.Namespace, project_root: Path) -> Path:
    if args.instance:
        instance_path = Path(args.instance)
        if not instance_path.exists():
            alt_path = project_root / "data" / "instances" / instance_path.name
            if alt_path.exists():
                instance_path = alt_path
        return instance_path
    return project_root / "data" / "instances" / "example_instance.json"


def print_selection(problem, selected_indices: list[int], total_score: float, solver_name: str) -> None:
    print(f"\nSelección resultante ({solver_name}):")
    print(f"- índice(s): {selected_indices}")
    print(f"- duración total: {problem.summary_duration(selected_indices)}")
    print(f"- puntuación total: {total_score}")
    print("\nFragmentos seleccionados:")
    for idx in selected_indices:
        fragment = problem.fragments[idx]
        print(f"  {fragment.id}. {fragment.text} ({fragment.duration}s)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta el solver clásico o asistido por LLM sobre una instancia JSON."
    )
    parser.add_argument(
        "instance",
        nargs="?",
        help="Ruta o nombre del archivo de instancia (por defecto: example_instance.json)",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Usar el solver asistido por LLM (requiere API key en .env)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    instance_path = resolve_instance_path(args, project_root)

    if not instance_path.exists():
        print(f"Error: No se encontró el archivo de instancia en {instance_path}")
        sys.exit(1)

    problem = load_instance_file(str(instance_path))

    print(f"Instancia cargada: {instance_path.name}")
    print(f"- fragmentos: {len(problem.fragments)}")
    print(f"- duración máxima: {problem.max_duration}s")

    if args.llm:
        print("\nModo: solver asistido por LLM")
        try:
            llm_client = LLMClient()
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

        if not llm_client.api_key:
            print(f"Error: {llm_client.api_key_env_name} no está configurada. Copia .env.example a .env y añade tu clave.")
            sys.exit(1)

        print(f"- proveedor: {llm_client.provider}")
        print(f"- modelo: {llm_client.model}")
        selected_indices, total_score = solve_with_llm(problem, llm_client)
        print_selection(problem, selected_indices, total_score, "solver LLM")
    else:
        scores = [1.0 for _ in problem.fragments]
        selected_indices, total_score = ordered_knapsack_dp(
            problem.fragments, scores, problem.max_duration
        )
        print_selection(problem, selected_indices, total_score, "solver clásico")


if __name__ == "__main__":
    main()
