"""Generación automática de notas cualitativas para el informe."""
import ast
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .scenarios import scenario_description

DEFAULT_NOTES_PATH = "informe/notas_experimentos.md"
LLM_CACHE_FILENAME = ".llm_cache.json"


def clear_llm_cache(project_root: Path) -> bool:
    cache_path = project_root / LLM_CACHE_FILENAME
    if cache_path.exists():
        cache_path.unlink()
        return True
    return False


def _parse_indices(raw: object) -> List[int]:
    if raw in ("", None):
        return []
    if isinstance(raw, list):
        return [int(value) for value in raw]
    text = str(raw).strip()
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [int(value) for value in parsed]
    except (SyntaxError, ValueError, TypeError):
        pass
    return []


def _format_float(value: object, decimals: int = 3) -> str:
    if value in ("", None):
        return "—"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def _row_by_solver(rows: Sequence[Dict[str, str]], instance_name: str) -> Dict[str, Dict[str, str]]:
    grouped: Dict[str, Dict[str, str]] = {}
    for row in rows:
        if row.get("instance") != instance_name:
            continue
        grouped[row.get("solver", "")] = row
    return grouped


def infer_qualitative_phrase(instance_name: str, by_solver: Dict[str, Dict[str, str]]) -> str:
    baseline = _parse_indices(by_solver.get("baseline", {}).get("selected_indices"))
    dynamic = _parse_indices(by_solver.get("llm_dynamic", {}).get("selected_indices"))
    static = _parse_indices(by_solver.get("llm_static", {}).get("selected_indices"))

    parts: List[str] = []

    if dynamic and 2 not in dynamic and instance_name in {
        "bench_irrelevant_middle.json",
        "bench_disordered.json",
    }:
        parts.append("Omite el fragmento irrelevante (índice 2).")

    if instance_name == "bench_disordered.json" and dynamic:
        if dynamic != sorted(dynamic):
            parts.append("Reordena el input permutado hacia un orden narrativo coherente.")
        elif dynamic == sorted(dynamic):
            parts.append("Selecciona fragmentos pero mantiene orden cronológico por índice.")

    if instance_name == "bench_static_vs_dynamic.json" and static and dynamic:
        if static != dynamic:
            parts.append(
                "El solver dinámico produce una selección distinta al estático "
                "(coherencia evaluada sobre saltos, no solo vecinos consecutivos)."
            )
        else:
            parts.append("Estático y dinámico coinciden en esta corrida.")

    if baseline and dynamic:
        if set(baseline) != set(dynamic):
            omitted = sorted(set(baseline) - set(dynamic))
            added = sorted(set(dynamic) - set(baseline))
            if omitted and not added:
                parts.append(
                    f"El LLM dinámico recorta la selección del baseline "
                    f"(omite índices {omitted})."
                )
            elif added and not omitted:
                parts.append(
                    f"El LLM dinámico incluye fragmentos que el baseline no selecciona "
                    f"(añade índices {added})."
                )
            else:
                parts.append("La selección del LLM dinámico difiere del baseline.")
        elif baseline != dynamic:
            parts.append("Mismo subconjunto que el baseline pero en distinto orden de reproducción.")
        elif len(dynamic) < len(baseline):
            parts.append("Selecciona menos fragmentos que el baseline dentro del límite.")
        elif not parts:
            parts.append("Coincide con la selección del baseline en esta corrida.")

    if instance_name == "example_instance_overlimit.json" and dynamic and baseline:
        if len(dynamic) < len(baseline):
            parts.append(
                "Con límite estricto, el LLM prioriza fragmentos más relevantes "
                "frente al baseline que llena duración con scores uniformes."
            )

    if not parts:
        parts.append("Revisar selected_indices y métricas en la tabla del bloque.")

    return " ".join(parts)


def format_block_section(
    instance_name: str,
    by_solver: Dict[str, Dict[str, str]],
    block_label: Optional[str] = None,
) -> str:
    baseline_row = by_solver.get("baseline", {})
    dynamic_row = by_solver.get("llm_dynamic", {})
    static_row = by_solver.get("llm_static", {})

    baseline_indices = baseline_row.get("selected_indices", "—")
    dynamic_indices = dynamic_row.get("selected_indices", "—")
    static_indices = static_row.get("selected_indices", "—")

    lines = []
    if block_label:
        lines.append(f"## {block_label}")
    else:
        lines.append(f"## {instance_name}")
    lines.append("")
    lines.append(f"**Instancia:** `{instance_name}`")
    lines.append("")
    lines.append(f"**Escenario:** {scenario_description(instance_name)}")
    lines.append("")
    lines.append("**Selección (`selected_indices`):**")
    lines.append("")
    lines.append(f"- baseline: `{baseline_indices}`")
    lines.append(f"- llm_dynamic: `{dynamic_indices}`")
    if static_row:
        lines.append(f"- llm_static: `{static_indices}`")
    lines.append("")
    lines.append(f"**Observación cualitativa:** {infer_qualitative_phrase(instance_name, by_solver)}")
    lines.append("")
    lines.append("**Métricas clave:**")
    lines.append("")
    lines.append("| solver | objective_score | duration_utilization |")
    lines.append("| --- | --- | --- |")

    for solver_name in ("baseline", "llm_dynamic", "llm_static"):
        row = by_solver.get(solver_name)
        if not row:
            continue
        lines.append(
            f"| {solver_name} | "
            f"{_format_float(row.get('objective_score'))} | "
            f"{_format_float(row.get('duration_utilization'))} |"
        )

    lines.append("")
    return "\n".join(lines)


def init_notes(notes_path: Path, project_root: Path, *, cache_cleared: bool) -> None:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cache_line = (
        "Caché LLM (`.llm_cache.json`) **eliminada** al inicio de la suite."
        if cache_cleared
        else "Caché LLM conservada (no se solicitó limpieza)."
    )

    content = "\n".join([
        "# Notas de experimentos — suite lite",
        "",
        f"Generado automáticamente: {timestamp}",
        "",
        f"- Proveedor: `{provider}`",
        f"- Modelo: `{model}`",
        f"- {cache_line}",
        "",
        "Cada bloque registra escenario, selecciones, observación cualitativa y métricas "
        "para la sección *Resultados y análisis* del informe.",
        "",
    ])
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(content, encoding="utf-8")


def append_block_notes(
    notes_path: Path,
    csv_path: Path,
    block_label: Optional[str] = None,
    instance_filter: Optional[str] = None,
) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el CSV del bloque: {csv_path}")

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    instances = sorted({row["instance"] for row in rows if row.get("instance")})
    if instance_filter:
        instances = [name for name in instances if name == instance_filter]

    if not instances:
        raise ValueError(f"El CSV {csv_path} no contiene filas de instancia.")

    sections: List[str] = []
    for instance_name in instances:
        by_solver = _row_by_solver(rows, instance_name)
        label = block_label if len(instances) == 1 else None
        if block_label and len(instances) == 1:
            label = block_label
        elif block_label and len(instances) > 1:
            label = f"{block_label} — {instance_name}"
        sections.append(format_block_section(instance_name, by_solver, label))

    existing = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    notes_path.write_text(existing + "\n".join(sections) + "\n", encoding="utf-8")
    print(f"Notas actualizadas en {notes_path} ({len(instances)} instancia(s)).")


def append_final_summary(
    notes_path: Path,
    bench_csv: Path,
    summary_md: Path,
    chart_path: Path,
    total_rows: int,
) -> None:
    section = "\n".join([
        "## Resumen final — Fase 8",
        "",
        "Artefactos generados para el informe:",
        "",
        f"- CSV fusionado: `{bench_csv.as_posix()}` ({total_rows} filas)",
        f"- Tabla resumen: `{summary_md.as_posix()}`",
        f"- Gráfico: `{chart_path.as_posix()}`" if chart_path.exists() else "- Gráfico: no generado (matplotlib ausente o sin datos)",
        "",
        "Sección del informe sugerida: **Resultados y análisis** — usar las observaciones "
        "cualitativas de cada bloque junto con la tabla y el gráfico anteriores.",
        "",
    ])
    existing = notes_path.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"
    notes_path.write_text(existing + section, encoding="utf-8")
    print(f"Resumen final añadido a {notes_path}.")
