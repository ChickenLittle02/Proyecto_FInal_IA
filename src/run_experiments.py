"""Comparación sistemática baseline_beam vs llm_beam sobre instancias JSON."""
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
from src.experiments.notes import append_block_notes
from src.instance import load_instance_file
from src.llm.client import LLMClient, SummaryEvaluation
from src.llm.scoring import build_relevance_scores
from src.problem import SelectionProblem
from src.solver.llm_assisted import (
    DEFAULT_BEAM_WIDTH,
    DEFAULT_SUMMARY_REFINE_TOP_M,
    solve,
    solve_baseline,
)

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
    "summary_llm_score",
    "summary_llm_relevance",
    "summary_llm_coherence",
    "selected_indices",
]

LITE_PATTERNS = ["example_*.json", "bench_*.json"]
BENCH_PATTERNS = LITE_PATTERNS + ["mini_video_*.json"]

SOLVER_BASELINE = "baseline_beam"
SOLVER_LLM = "llm_beam"


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


def run_solver(
    solver_name: str,
    problem: SelectionProblem,
    llm_client: Optional[LLMClient],
    coherence_weight: float,
    beam_width: int,
    summary_refine_top_m: int,
) -> tuple[List[int], float, Optional[SummaryEvaluation]]:
    if solver_name == SOLVER_BASELINE:
        selected_indices, solver_score, _mode = solve_baseline(
            problem, coherence_weight, beam_width=beam_width
        )
        return selected_indices, solver_score, None
    if solver_name == SOLVER_LLM:
        if llm_client is None:
            raise ValueError("El solver llm_beam requiere un LLMClient configurado.")
        selected_indices, solver_score, _mode, summary_eval = solve(
            problem,
            llm_client,
            coherence_weight,
            beam_width=beam_width,
            summary_refine_top_m=summary_refine_top_m,
        )
        return selected_indices, solver_score, summary_eval
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
    summary_evaluation: Optional[SummaryEvaluation] = None,
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
    if summary_evaluation is not None:
        row["summary_llm_score"] = summary_evaluation.overall
        row["summary_llm_relevance"] = summary_evaluation.relevance
        row["summary_llm_coherence"] = summary_evaluation.coherence
    else:
        row["summary_llm_score"] = ""
        row["summary_llm_relevance"] = ""
        row["summary_llm_coherence"] = ""
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
        description="Ejecuta baseline_beam vs llm_beam y guarda métricas en CSV."
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
        help="Incluir solver llm_beam (precálculo LLM + beam search)",
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
        "--beam-width",
        type=int,
        default=DEFAULT_BEAM_WIDTH,
        help=f"Ancho del beam search (default: {DEFAULT_BEAM_WIDTH})",
    )
    parser.add_argument(
        "--summary-refine-top-m",
        type=int,
        default=DEFAULT_SUMMARY_REFINE_TOP_M,
        help=(
            "Candidatos top-M del beam a evaluar con juez macro en llm_beam "
            f"(default: {DEFAULT_SUMMARY_REFINE_TOP_M}; 0 desactiva refinamiento)"
        ),
    )
    parser.add_argument(
        "--output",
        default="results/experiments.csv",
        help="Ruta del CSV de salida (default: results/experiments.csv)",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="Ruta markdown donde anotar escenario, selecciones y métricas (append)",
    )
    parser.add_argument(
        "--block-label",
        default=None,
        help="Título del bloque en notas_experimentos.md (ej. 'Bloque 4 — overlimit')",
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

    solvers = [SOLVER_BASELINE]
    if args.llm:
        solvers.append(SOLVER_LLM)

    llm_client: Optional[LLMClient] = None
    needs_llm = SOLVER_LLM in solvers or args.evaluate
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
            relevance_scores = build_relevance_scores(problem, llm_client)

        for solver_name in solvers:
            print(f"  Ejecutando {solver_name}...")
            selected_indices, solver_score, summary_eval = run_solver(
                solver_name,
                problem,
                llm_client,
                args.coherence_weight,
                args.beam_width,
                args.summary_refine_top_m,
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
                summary_evaluation=summary_eval,
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

    if args.notes:
        notes_path = Path(args.notes)
        if not notes_path.is_absolute():
            notes_path = project_root / notes_path
        if not notes_path.exists():
            from src.experiments.notes import init_notes

            init_notes(notes_path, project_root, cache_cleared=False)
        instance_filter = instance_paths[0].name if len(instance_paths) == 1 else None
        append_block_notes(
            notes_path,
            output_path,
            block_label=args.block_label,
            instance_filter=instance_filter,
        )


if __name__ == "__main__":
    main()
