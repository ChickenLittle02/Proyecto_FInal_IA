"""Comparación sistemática baseline vs solver LLM sobre instancias JSON."""
import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.experiments.metrics import (
    build_result_row,
    evaluate_selection_with_llm,
    structural_metrics,
)
from src.instance import load_instance_file
from src.llm.client import LLMClient
from src.problem import SelectionProblem
from src.solver.baseline import ordered_knapsack_dp
from src.solver.llm_assisted import (
    solve_with_llm,
    solve_with_llm_reorder,
    solve_with_llm_static,
)
from src.solver.reorder import solve_baseline_reorder

CSV_FIELDS = [
    "instance",
    "solver",
    "n_fragments",
    "n_selected",
    "max_duration",
    "duration_used",
    "duration_utilization",
    "fragment_coverage",
    "duration_coverage",
    "solver_score",
    "mean_relevance",
    "mean_coherence",
    "objective_score",
    "selected_indices",
]


LITE_PATTERNS = ["example_*.json", "bench_*.json"]
BENCH_PATTERNS = LITE_PATTERNS + ["mini_video_*.json"]


def _glob_instances(instances_dir: Path, patterns: Sequence[str]) -> List[Path]:
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(instances_dir.glob(pattern))
    return sorted(set(paths))


def resolve_instances(project_root: Path, patterns: Optional[Sequence[str]]) -> List[Path]:
    instances_dir = project_root / "data" / "instances"
    if patterns:
        paths: List[Path] = []
        for pattern in patterns:
            candidate = Path(pattern)
            if candidate.exists():
                paths.append(candidate)
                continue
            by_name = instances_dir / pattern
            if by_name.exists():
                paths.append(by_name)
                continue
            paths.extend(sorted(instances_dir.glob(pattern)))
        return sorted(set(paths))
    return sorted(instances_dir.glob("*.json"))


def resolve_lite_instances(project_root: Path) -> List[Path]:
    return _glob_instances(project_root / "data" / "instances", LITE_PATTERNS)


def resolve_bench_instances(project_root: Path) -> List[Path]:
    return _glob_instances(project_root / "data" / "instances", BENCH_PATTERNS)


def precompute_relevance_scores(
    problem: SelectionProblem,
    llm_client: LLMClient,
) -> List[float]:
    n_fragments = len(problem.fragments)
    scores: List[float] = []
    for index, fragment in enumerate(problem.fragments):
        print(f"    fragmento {index + 1}/{n_fragments}...", flush=True)
        scores.append(llm_client.score_fragment(fragment))
    return scores


def run_solver(
    solver_name: str,
    problem: SelectionProblem,
    llm_client: Optional[LLMClient],
    coherence_weight: float,
) -> tuple[List[int], float]:
    if solver_name == "baseline":
        scores = [1.0 for _ in problem.fragments]
        return ordered_knapsack_dp(problem.fragments, scores, problem.max_duration)
    if solver_name == "llm_dynamic":
        if llm_client is None:
            raise ValueError("El solver llm_dynamic requiere un LLMClient configurado.")
        return solve_with_llm(problem, llm_client, coherence_weight=coherence_weight)
    if solver_name == "llm_static":
        if llm_client is None:
            raise ValueError("El solver llm_static requiere un LLMClient configurado.")
        return solve_with_llm_static(problem, llm_client, coherence_weight=coherence_weight)
    if solver_name == "baseline_reorder":
        scores = [1.0 for _ in problem.fragments]
        return solve_baseline_reorder(
            problem.fragments, scores, problem.max_duration, coherence_weight
        )
    if solver_name == "llm_reorder":
        if llm_client is None:
            raise ValueError("El solver llm_reorder requiere un LLMClient configurado.")
        return solve_with_llm_reorder(problem, llm_client, coherence_weight=coherence_weight)
    raise ValueError(f"Solver desconocido: {solver_name}")


def experiment_row(
    instance_name: str,
    solver_name: str,
    problem: SelectionProblem,
    selected_indices: List[int],
    solver_score: float,
    llm_client: Optional[LLMClient],
    evaluate: bool,
    relevance_scores: Optional[List[float]],
    coherence_weight: float,
) -> Dict[str, object]:
    structural = structural_metrics(problem, selected_indices, solver_score)
    llm_metrics = None
    if evaluate and llm_client is not None:
        llm_metrics = evaluate_selection_with_llm(
            problem,
            selected_indices,
            llm_client,
            relevance_scores=relevance_scores,
            coherence_weight=coherence_weight,
        )
    row = build_result_row(instance_name, solver_name, selected_indices, structural, llm_metrics)
    row["selected_indices"] = str(row["selected_indices"])
    return row


def write_csv(rows: List[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta comparaciones baseline vs LLM y guarda métricas en CSV."
    )
    parser.add_argument(
        "--instances",
        nargs="*",
        help="Instancias a evaluar (nombre, ruta o glob). Por defecto: todas en data/instances/*.json",
    )
    parser.add_argument(
        "--suite",
        choices=["lite", "bench"],
        help=(
            "Suite predefinida: lite = example_*.json + bench_*.json (~5 min, recomendada); "
            "bench = lite + mini_video_*.json (pesada, cientos de llamadas LLM)"
        ),
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Incluir solver LLM dinámico (Paso C)",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Incluir solver LLM estático (Paso B) para comparación",
    )
    parser.add_argument(
        "--reorder",
        action="store_true",
        help="Incluir solvers con reordenación (baseline_reorder + llm_reorder)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluar cada selección post-hoc con LLM (relevancia, coherencia, objective_score)",
    )
    parser.add_argument(
        "--coherence-weight",
        type=float,
        default=0.25,
        help="Peso de coherencia en solver y evaluación (default: 0.25)",
    )
    parser.add_argument(
        "--output",
        default="results/experiments.csv",
        help="Ruta del CSV de salida (default: results/experiments.csv)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    if args.suite == "lite":
        instance_paths = resolve_lite_instances(project_root)
    elif args.suite == "bench":
        instance_paths = resolve_bench_instances(project_root)
    else:
        instance_paths = resolve_instances(project_root, args.instances)
    if not instance_paths:
        print("Error: no se encontraron instancias para evaluar.")
        sys.exit(1)

    solvers = ["baseline"]
    if args.llm:
        solvers.append("llm_dynamic")
    if args.static:
        solvers.append("llm_static")
    if args.reorder:
        solvers.append("baseline_reorder")
        if args.llm:
            solvers.append("llm_reorder")

    llm_client: Optional[LLMClient] = None
    needs_llm = any(name.startswith("llm") for name in solvers) or args.evaluate
    if needs_llm:
        llm_client = LLMClient()
        if not llm_client.api_key:
            print(f"Error: {llm_client.api_key_env_name} no configurada. Copia .env.example a .env.")
            sys.exit(1)

    rows: List[Dict[str, object]] = []
    for instance_path in instance_paths:
        problem = load_instance_file(str(instance_path))
        instance_name = instance_path.name
        print(f"\n=== {instance_name} ({len(problem.fragments)} fragmentos) ===", flush=True)

        relevance_scores: Optional[List[float]] = None
        if args.evaluate and llm_client is not None:
            print("  Precomputando relevancia LLM para evaluación post-hoc...")
            relevance_scores = precompute_relevance_scores(problem, llm_client)

        for solver_name in solvers:
            print(f"  Ejecutando {solver_name}...")
            selected_indices, solver_score = run_solver(
                solver_name, problem, llm_client, args.coherence_weight
            )
            row = experiment_row(
                instance_name,
                solver_name,
                problem,
                selected_indices,
                solver_score,
                llm_client,
                args.evaluate,
                relevance_scores,
                args.coherence_weight,
            )
            rows.append(row)
            print(
                f"    -> selección={row['selected_indices']}, "
                f"duración={row['duration_used']}, score={row['solver_score']}"
            )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    write_csv(rows, output_path)
    print(f"\nResultados guardados en {output_path} ({len(rows)} filas)")


if __name__ == "__main__":
    main()
