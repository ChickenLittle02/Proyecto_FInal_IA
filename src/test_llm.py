"""Script de prueba para verificar la integración con el proveedor LLM configurado."""
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.llm.client import LLMClient, SummaryEvaluation
from src.problem import Fragment


FICTIONAL_SUMMARY = (
    "La inteligencia artificial está transformando la educación al personalizar el aprendizaje.\n\n"
    "Los modelos de lenguaje permiten generar explicaciones adaptadas al nivel del estudiante.\n\n"
    "Sin embargo, es necesario validar la calidad pedagógica de los contenidos generados."
)


def test_parse_summary_evaluation() -> None:
    """Parseo de respuestas macro sin llamadas a la API."""
    parsed_json = LLMClient._parse_summary_evaluation(
        '{"relevance": 0.85, "coherence": 0.72, "overall": 0.80}'
    )
    assert parsed_json == SummaryEvaluation(0.85, 0.72, 0.8)

    parsed_numbers = LLMClient._parse_summary_evaluation(
        "relevance: 0.9\n coherence: 0.6\n overall: 0.75"
    )
    assert parsed_numbers == SummaryEvaluation(0.9, 0.6, 0.75)

    parsed_single = LLMClient._parse_summary_evaluation("0.65")
    assert parsed_single == SummaryEvaluation(0.65, 0.65, 0.65)

    parsed_empty = LLMClient._parse_summary_evaluation("0.0")
    assert parsed_empty == SummaryEvaluation(0.0, 0.0, 0.0)


def main() -> None:
    print("=== Prueba de Integración con LLM API ===")
    test_parse_summary_evaluation()
    print("[OK] Parseo de evaluación macro (sin API)")

    try:
        client = LLMClient()
    except Exception as e:
        print(f"Error al inicializar el cliente: {e}")
        return

    print(f"Proveedor: {client.provider}")
    print(f"Modelo: {client.model}")
    print(f"API Key detectada: {'SÍ (oculta)' if client.api_key else 'NO'}")

    if not client.api_key:
        print(f"\n[ERROR] No se detectó {client.api_key_env_name} en el entorno o archivo .env")
        print("Por favor, crea un archivo '.env' en la raíz (copia .env.example).")
        return

    frag = Fragment(
        id="test",
        text="La inteligencia artificial es una tecnología disruptiva que está cambiando la educación.",
        duration=10.0,
        start_time=0.0,
        end_time=10.0,
    )

    print("\nEvaluando fragmento (primera llamada real, con delay de cortesía)...")
    start_time = time.time()
    try:
        score = client.score_fragment(frag)
        duration = time.time() - start_time
        print(f"Resultado score: {score}")
        print(f"Tiempo de respuesta: {round(duration, 2)}s")
    except Exception as e:
        print(f"Error en la llamada real: {e}")
        return

    print("\nEvaluando el mismo fragmento (segunda llamada, debería usar el caché)...")
    start_time = time.time()
    score_cached = client.score_fragment(frag)
    duration_cached = time.time() - start_time
    print(f"Resultado score: {score_cached}")
    print(f"Tiempo de respuesta: {round(duration_cached * 1000, 2)}ms")

    if score == score_cached:
        print(f"\n[ÉXITO] Conexión con {client.provider} y caché de fragmentos OK.")
    else:
        print("\n[ADVERTENCIA] Las puntuaciones de fragmento difieren, revisa el caché.")

    print("\nEvaluando resumen ficticio (primera llamada macro, con delay de cortesía)...")
    start_time = time.time()
    try:
        summary_eval = client.evaluate_summary(FICTIONAL_SUMMARY, max_duration=60.0)
        duration = time.time() - start_time
        print(
            f"Resultado macro: relevance={summary_eval.relevance}, "
            f"coherence={summary_eval.coherence}, overall={summary_eval.overall}"
        )
        print(f"Tiempo de respuesta: {round(duration, 2)}s")
    except Exception as e:
        print(f"Error en evaluación macro: {e}")
        return

    if summary_eval.overall == 0.0 and summary_eval.relevance == 0.0:
        print("\n[ADVERTENCIA] El LLM devolvió 0.0 en todas las métricas macro (posible fallo silencioso).")

    print("\nEvaluando el mismo resumen (segunda llamada macro, debería usar el caché)...")
    start_time = time.time()
    summary_cached = client.evaluate_summary(FICTIONAL_SUMMARY, max_duration=60.0)
    duration_cached = time.time() - start_time
    print(
        f"Resultado macro: relevance={summary_cached.relevance}, "
        f"coherence={summary_cached.coherence}, overall={summary_cached.overall}"
    )
    print(f"Tiempo de respuesta: {round(duration_cached * 1000, 2)}ms")

    if summary_eval == summary_cached:
        print(f"\n[ÉXITO] Evaluación macro y caché funcionando con {client.provider}.")
    else:
        print("\n[ADVERTENCIA] Las puntuaciones macro difieren entre llamadas.")


if __name__ == "__main__":
    main()
