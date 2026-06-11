"""Genera tabla markdown y gráfico de comparación desde results/experiments.csv."""
import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

SUMMARY_COLUMNS = [
    "instance",
    "solver",
    "n_selected",
    "duration_utilization",
    "solver_score",
    "mean_relevance",
    "mean_coherence",
    "objective_score",
]


def load_csv(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def format_cell(value: str, decimals: int = 3) -> str:
    if value in ("", None):
        return "—"
    try:
        number = float(value)
        if number == int(number) and abs(number) >= 1:
            return str(int(number)) if number == int(number) else f"{number:.{decimals}f}"
        return f"{number:.{decimals}f}"
    except ValueError:
        return value


def write_markdown_table(
    rows: List[Dict[str, str]],
    output_path: Path,
    source_name: str,
) -> None:
    header = "| " + " | ".join(SUMMARY_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in SUMMARY_COLUMNS) + " |"
    body_lines = []
    for row in rows:
        cells = [format_cell(row.get(col, "")) for col in SUMMARY_COLUMNS]
        body_lines.append("| " + " | ".join(cells) + " |")

    content = "\n".join([
        "# Resumen de experimentos",
        "",
        f"Fuente: `{output_path.parent.name}/{source_name}`",
        "",
        header,
        separator,
        *body_lines,
        "",
    ])
    output_path.write_text(content, encoding="utf-8")


def write_chart(rows: List[Dict[str, str]], output_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no instalado; se omite el gráfico PNG.")
        return False

    llm_rows = [r for r in rows if r.get("objective_score")]
    if not llm_rows:
        print("No hay filas con objective_score; se omite el gráfico.")
        return False

    labels: List[str] = []
    objectives: List[float] = []
    for row in llm_rows:
        labels.append(f"{row['instance']}\n{row['solver']}")
        objectives.append(float(row["objective_score"]))

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.35)))
    bars = ax.barh(labels, objectives, color="#4C72B0")
    ax.set_xlabel("objective_score (evaluación post-hoc LLM)")
    ax.set_title("Comparación baseline vs solvers LLM")
    ax.set_xlim(0, max(objectives) * 1.1 if objectives else 1.0)
    for bar, value in zip(bars, objectives):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume experimentos CSV en tabla y gráfico.")
    parser.add_argument(
        "--input",
        default="results/experiments.csv",
        help="CSV de entrada (default: results/experiments.csv)",
    )
    parser.add_argument(
        "--markdown",
        default="results/summary.md",
        help="Salida markdown (default: results/summary.md)",
    )
    parser.add_argument(
        "--chart",
        default="results/comparison.png",
        help="Salida gráfico PNG (default: results/comparison.png)",
    )
    args = parser.parse_args()

    csv_path = Path(args.input)
    if not csv_path.is_absolute():
        csv_path = root / csv_path
    if not csv_path.exists():
        print(f"Error: no existe {csv_path}")
        sys.exit(1)

    rows = load_csv(csv_path)
    md_path = root / args.markdown if not Path(args.markdown).is_absolute() else Path(args.markdown)
    chart_path = root / args.chart if not Path(args.chart).is_absolute() else Path(args.chart)

    write_markdown_table(rows, md_path, csv_path.name)
    print(f"Tabla guardada en {md_path}")

    if write_chart(rows, chart_path):
        print(f"Gráfico guardado en {chart_path}")


if __name__ == "__main__":
    main()
