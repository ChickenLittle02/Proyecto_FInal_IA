"""
Ejecuta la suite lite completa (Bloques 3–8) con notas automáticas para el informe.

Al inicio elimina `.llm_cache.json` para forzar llamadas LLM frescas.
Tras cada bloque actualiza `informe/notas_experimentos.md`.
Al final fusiona CSVs, genera summary_bench.md + gráfico y cierra con resumen Fase 8.
"""
import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from dotenv import load_dotenv

from src.experiments.merge_results import merge_csvs
from src.experiments.notes import (
    DEFAULT_NOTES_PATH,
    append_final_summary,
    clear_llm_cache,
    init_notes,
)
from src.experiments.summarize import load_csv, write_chart, write_markdown_table

load_dotenv(root / ".env")


@dataclass(frozen=True)
class LiteBlock:
    number: int
    label: str
    instance: str
    output: str


LITE_BLOCKS: Sequence[LiteBlock] = (
    LiteBlock(3, "Bloque 3 — example_instance", "example_instance.json", "results/experiments.csv"),
    LiteBlock(4, "Bloque 4 — example_instance_overlimit", "example_instance_overlimit.json", "results/part04_overlimit.csv"),
    LiteBlock(5, "Bloque 5 — bench_static_vs_dynamic", "bench_static_vs_dynamic.json", "results/part05_static_vs_dynamic.csv"),
    LiteBlock(6, "Bloque 6 — bench_irrelevant_middle", "bench_irrelevant_middle.json", "results/part06_irrelevant_middle.csv"),
    LiteBlock(6, "Bloque 6b — bench_disordered", "bench_disordered.json", "results/part06b_disordered.csv"),
)

DEFAULT_BENCH_CSV = "results/experiments_bench.csv"
DEFAULT_SUMMARY_MD = "results/summary_bench.md"
DEFAULT_CHART = "results/comparison_bench.png"


def _run_block(block: LiteBlock, notes_path: Path) -> None:
    cmd = [
        sys.executable,
        str(root / "src" / "run_experiments.py"),
        "--instances",
        block.instance,
        "--llm",
        "--static",
        "--evaluate",
        "--output",
        block.output,
        "--notes",
        str(notes_path.relative_to(root)),
        "--block-label",
        block.label,
    ]

    print(f"\n{'=' * 60}")
    print(f"Ejecutando {block.label}")
    print(f"{'=' * 60}")
    subprocess.run(cmd, cwd=root, check=True)


def run_preflight(skip_tests: bool) -> None:
    if skip_tests:
        print("Validación preflight omitida (--skip-tests).")
        return
    print("Fase 0 — validación mock (test_bench_instances.py)...")
    subprocess.run(
        [sys.executable, str(root / "src" / "test_bench_instances.py")],
        cwd=root,
        check=True,
    )


def run_lite_suite(
    *,
    blocks: Sequence[LiteBlock],
    notes_path: Path,
    bench_csv: Path,
    summary_md: Path,
    chart_path: Path,
    skip_tests: bool,
    keep_cache: bool,
) -> None:
    if not keep_cache:
        cleared = clear_llm_cache(root)
        print(
            "Caché LLM eliminada (.llm_cache.json)."
            if cleared
            else "No había caché LLM previa."
        )
    else:
        print("Caché LLM conservada (--keep-cache).")

    init_notes(notes_path, root, cache_cleared=not keep_cache)
    run_preflight(skip_tests)

    for block in blocks:
        _run_block(block, notes_path)

    print(f"\n{'=' * 60}")
    print("Fase 7 — fusionar CSVs")
    print(f"{'=' * 60}")
    sources = [root / block.output for block in LITE_BLOCKS]
    row_count = merge_csvs(sources, bench_csv)

    print(f"\n{'=' * 60}")
    print("Fase 8 — tabla y gráfico")
    print(f"{'=' * 60}")
    rows = load_csv(bench_csv)
    write_markdown_table(rows, summary_md, bench_csv.name)
    print(f"Tabla guardada en {summary_md}")
    if write_chart(rows, chart_path):
        print(f"Gráfico guardado en {chart_path}")

    append_final_summary(notes_path, bench_csv, summary_md, chart_path, row_count)
    print(f"\nSuite lite completada. Notas en {notes_path}")


def resolve_blocks(
    only_block: Optional[int],
    from_block: Optional[int],
) -> List[LiteBlock]:
    selected = list(LITE_BLOCKS)
    if only_block is not None:
        selected = [block for block in LITE_BLOCKS if block.number == only_block]
        if not selected:
            raise ValueError(f"No hay bloque con número {only_block}.")
    elif from_block is not None:
        selected = [block for block in LITE_BLOCKS if block.number >= from_block]
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suite lite con caché limpia, notas automáticas y artefactos para el informe."
    )
    parser.add_argument(
        "--block",
        type=int,
        default=None,
        help="Ejecutar solo bloques con este número (6 incluye 6 y 6b)",
    )
    parser.add_argument(
        "--from-block",
        type=int,
        default=None,
        help="Ejecutar desde este bloque hasta el final (ej. --from-block 4)",
    )
    parser.add_argument(
        "--notes",
        default=DEFAULT_NOTES_PATH,
        help=f"Markdown de notas (default: {DEFAULT_NOTES_PATH})",
    )
    parser.add_argument(
        "--output-csv",
        default=DEFAULT_BENCH_CSV,
        help=f"CSV fusionado final (default: {DEFAULT_BENCH_CSV})",
    )
    parser.add_argument(
        "--summary",
        default=DEFAULT_SUMMARY_MD,
        help=f"Tabla markdown (default: {DEFAULT_SUMMARY_MD})",
    )
    parser.add_argument(
        "--chart",
        default=DEFAULT_CHART,
        help=f"Gráfico PNG (default: {DEFAULT_CHART})",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="No borrar .llm_cache.json al inicio",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Omitir test_bench_instances.py antes de los bloques LLM",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Solo ejecutar bloques y notas; no fusionar ni generar resumen final",
    )
    args = parser.parse_args()

    notes_path = root / args.notes
    bench_csv = root / args.output_csv
    summary_md = root / args.summary
    chart_path = root / args.chart
    blocks = resolve_blocks(args.block, args.from_block)
    full_suite = len(blocks) == len(LITE_BLOCKS) and args.block is None and args.from_block is None

    if full_suite and not args.no_merge:
        run_lite_suite(
            blocks=blocks,
            notes_path=notes_path,
            bench_csv=bench_csv,
            summary_md=summary_md,
            chart_path=chart_path,
            skip_tests=args.skip_tests,
            keep_cache=args.keep_cache,
        )
        return

    if not args.keep_cache and (full_suite or (blocks and blocks[0].number == LITE_BLOCKS[0].number)):
        cleared = clear_llm_cache(root)
        print("Caché LLM eliminada (.llm_cache.json)." if cleared else "No había caché LLM previa.")
        init_notes(notes_path, root, cache_cleared=cleared)
    elif not notes_path.exists():
        init_notes(notes_path, root, cache_cleared=False)

    run_preflight(args.skip_tests)
    for block in blocks:
        _run_block(block, notes_path)

    if args.no_merge:
        return

    print("\nFusionando CSVs disponibles...")
    sources = [root / block.output for block in LITE_BLOCKS if (root / block.output).exists()]
    row_count = merge_csvs(sources, bench_csv)
    rows = load_csv(bench_csv)
    write_markdown_table(rows, summary_md, bench_csv.name)
    print(f"Tabla guardada en {summary_md}")
    if write_chart(rows, chart_path):
        print(f"Gráfico guardado en {chart_path}")
    append_final_summary(notes_path, bench_csv, summary_md, chart_path, row_count)


if __name__ == "__main__":
    main()
