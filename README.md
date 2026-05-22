# Proyecto Final IA - Selección y ordenación de fragmentos

Este repositorio contiene una base inicial para el proyecto final de IA sobre selección de fragmentos de video educativo.

## Estructura creada
- `src/problem.py` — definición formal del problema y representación de fragmentos.
- `src/instance.py` — carga y guardado de instancias en JSON.
- `src/solver/baseline.py` — solver clásico con selección ordenada y DP.
- `src/solver/llm_assisted.py` — solver asistido por LLM con puntuación de relevancia y coherencia.
- `src/llm/client.py` — wrapper de configuración de LLM.
- `src/llm/prompts.py` — prompts base para evaluación de fragmentos.
- `src/llm/cache.py` — caché local para respuestas de LLM.

## Primeros pasos (día 1)
1. Definir claramente la estructura de datos y el problema formal.
2. Completar la implementación del solver clásico.
3. Preparar datos de prueba pequeños en `data/instances/`.
4. Conectar la implementación LLM real en `src/llm/client.py`.

## Instancia de ejemplo
Se añadió `data/instances/example_instance.json` con una secuencia de 5 fragmentos de un video educativo. El ejemplo usa una duración máxima de `45.0` segundos, de modo que el solver debe seleccionar los fragmentos más relevantes y coherentes dentro del límite.

Para cargar la instancia y ejecutar un ejemplo rápido con el solver clásico:

```bash
python src/run_example.py
```

## Configuración mínima
- Python 3.10+
- Instalar dependencias con `pip install -r requirements.txt`

## Siguientes tareas
- Generar instancias sintéticas o reales.
- Evaluar la selección con un solver clásico.
- Añadir un wrapper real para llamada a un modelo LLM.
