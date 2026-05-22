"""
Plantillas básicas de prompts para evaluar fragmentos y coherencia.
"""
from typing import List


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
