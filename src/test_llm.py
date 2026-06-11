"""Script de prueba para verificar la integración con el proveedor LLM configurado."""
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.llm.client import LLMClient
from src.problem import Fragment


def main() -> None:
    print("=== Prueba de Integración con LLM API ===")
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

    # Crear un fragmento ficticio
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
        print(f"\n[ÉXITO] ¡Conexión con {client.provider} y caché funcionando correctamente!")
    else:
        print("\n[ADVERTENCIA] Las puntuaciones difieren, revisa el funcionamiento del caché.")


if __name__ == "__main__":
    main()
