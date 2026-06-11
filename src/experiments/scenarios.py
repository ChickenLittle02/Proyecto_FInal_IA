"""Metadatos de escenario por instancia para notas automáticas del informe."""
from typing import Dict, Optional

INSTANCE_SCENARIOS: Dict[str, str] = {
    "example_instance.json": (
        "Caso base sintético (5 fragmentos, max_duration=45). "
        "Comprueba selección relevante dentro del límite de duración."
    ),
    "example_instance_overlimit.json": (
        "Mismo contenido que example_instance con max_duration=30 (más estricto). "
        "Comprueba recorte cuando no caben todos los fragmentos."
    ),
    "bench_static_vs_dynamic.json": (
        "Escenario «salto»: coherencia alta entre (0,2) pero baja en el puente (0,1,2). "
        "Contrasta solver estático (vecinos fijos) vs dinámico (transiciones reales)."
    ),
    "bench_irrelevant_middle.json": (
        "Fragmento central irrelevante (música/anuncio, índice 2). "
        "Input en orden cronológico; debe omitirse el segmento sin contenido educativo."
    ),
    "bench_disordered.json": (
        "Mismos textos que bench_irrelevant_middle pero array permutado en el JSON. "
        "Valida reordenación automática hacia orden narrativo (Task E)."
    ),
}


def scenario_description(instance_name: str) -> str:
    return INSTANCE_SCENARIOS.get(
        instance_name,
        "Instancia de evaluación (sin descripción registrada).",
    )
