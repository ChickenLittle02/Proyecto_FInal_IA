"""Fusiona varios CSV de experimentos en un único archivo."""
import argparse
import csv
from pathlib import Path
from typing import List, Optional, Sequence


DEFAULT_SOURCES = [
    "results/experiments.csv",
    "results/part04_overlimit.csv",
    "results/part05_static_vs_dynamic.csv",
    "results/part06_irrelevant_middle.csv",
]


def merge_csvs(sources: Sequence[Path], output_path: Path) -> int:
    rows: List[dict] = []
    fieldnames: Optional[List[str]] = None

    for source in sources:
        if not source.exists():
            print(f"FALTA: {source}")
            continue
        with source.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = reader.fieldnames
            rows.extend(list(reader))

    if not fieldnames:
        raise ValueError("No se encontró ningún CSV válido para fusionar.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Guardado {output_path} ({len(rows)} filas)")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusiona CSVs de experimentos.")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=DEFAULT_SOURCES,
        help="Rutas de CSV a fusionar (por defecto: suite bench parcial)",
    )
    parser.add_argument(
        "--output",
        default="results/experiments_bench.csv",
        help="CSV de salida (default: results/experiments_bench.csv)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent
    sources = [root / path for path in args.sources]
    output_path = root / args.output
    merge_csvs(sources, output_path)


if __name__ == "__main__":
    main()
