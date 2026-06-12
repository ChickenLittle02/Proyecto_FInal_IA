"""
Plantillas de prompts para evaluación micro (fragmentos/pares) y macro (resumen).
"""


def fragment_prompt(fragment_text: str) -> str:
    return (
        "Evalúa la relevancia de este fragmento para un resumen educativo. "
        "Devuelve un valor numérico entre 0.0 y 1.0.\n"
        f"Fragmento:\n{fragment_text.strip()}\n"
        "Respuesta esperada: un solo número."
    )


def coherence_prompt(first_fragment: str, second_fragment: str) -> str:
    return (
        "Evalúa la coherencia entre dos fragmentos consecutivos. "
        "Devuelve un valor numérico entre 0.0 y 1.0.\n"
        "Primer fragmento:\n"
        f"{first_fragment.strip()}\n\n"
        "Segundo fragmento:\n"
        f"{second_fragment.strip()}\n"
        "Respuesta esperada: un solo número."
    )


def summary_evaluation_prompt(summary_text: str, max_duration: float) -> str:
    """Prompt para evaluar relevancia, coherencia y calidad global de un resumen completo."""
    return (
        "Evalúa el siguiente resumen extractivo de un video educativo. "
        "Considera si los fragmentos seleccionados representan bien el contenido "
        f"y si el orden es coherente. La duración máxima permitida es {max_duration:.1f} segundos.\n\n"
        "Resumen:\n"
        f"{summary_text.strip()}\n\n"
        "Devuelve un objeto JSON con tres claves numéricas entre 0.0 y 1.0:\n"
        '- "relevance": qué tan relevante es el conjunto para un resumen educativo\n'
        '- "coherence": qué tan coherente es la secuencia de fragmentos\n'
        '- "overall": calidad global del resumen\n'
        "Respuesta esperada: solo el JSON, sin texto adicional."
    )
