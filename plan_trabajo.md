# Plan de trabajo - Proyecto Final IA (Tema 2)

## Contexto clave
- Tema escogido: **Construcción de resúmenes como selección óptima de segmentos**
- El sistema debe recibir fragmentos de video educativo con transcripciones.
- El objetivo es seleccionar y ordenar un subconjunto de fragmentos que represente bien el contenido bajo una longitud límite.
- El LLM debe evaluar **coherencia** y **relevancia**, y el sistema debe incluir un componente algorítmico real.
- Tener en cuenta los capítulos 1-6 de `temas-simulacion.pdf` cuando aporten al proyecto:
  - capítulo 1: modelar el sistema, sus entradas/salidas y el ambiente de decisión.
  - capítulo 2: si generas datos sintéticos, usar distribuciones y procesos aleatorios para crear instancias variadas.
  - capítulo 3: aplicar ideas de simulación de eventos discretos para estructurar la evaluación secuencial de fragmentos.
  - capítulo 4: usar análisis estadístico para comparar variantes y documentar resultados.
  - capítulo 5: usar lógica difusa para modelar grados de relevancia/coherencia y justificar una evaluación no-binaria.
  - capítulo 6: describir el sistema como un agente que percibe fragmentos y decide la selección y ordenación.

## Objetivo del plan
Terminar el sistema completo en una semana con:
- dataset / instancias
- implementación algorítmica + versión asistida por LLM
- configuración de LLM reproducible
- análisis experimental
- informe técnico
- instrucciones de ejecución

---

## Día 1 — Definición y diseño
- Definir el problema formal:
  - variables: fragmentos `s_i`, longitud `l_i`, selección `x_i \in {0,1}`
  - restricción: suma de longitudes ≤ límite
  - objetivo: maximizar relevancia + coherencia del resumen
  - orden preservado según el video original
- Decidir el modelo algorítmico:
  - variante de **DP / knapsack con orden** para seleccionar fragmentos
  - o “subset selection con penalty de transición”
- Anotar claramente:
  - qué hace el algoritmo clásico
  - qué hace el LLM
- Escribir un esquema de la estructura del proyecto:
  - `src/problem.py`, `src/instance.py`, `src/solver/baseline.py`, `src/solver/llm_assisted.py`, `src/llm/`

## Día 2 — Dataset e instancias
- Recolectar o generar dataset:
  - usar 2–3 videos educativos reales
  - extraer fragmentos cortos + transcripciones
  - crear instancias en JSON/CSV con: texto, duración, posición
- Crear instancias de prueba razonables:
  - videos de 5-10 fragmentos
  - casos con segmentos muy relevantes y segmentos irrelevantes
- Implementar loader de datos:
  - `data/instances/`
  - función para leer fragmentos y longitudes
- Guardar el proceso de generación en el informe

## Día 3 — LLM + prompts + caché
- Elegir proveedor / modo de desarrollo:
  - local (Ollama, Llama 3) o API (OpenAI / Anthropic / Gemini)
- Crear wrapper de LLM:
  - env var para modelo y API key
  - `src/llm/client.py`
  - `src/llm/prompts.py`
  - `src/llm/cache.py`
- Diseñar prompts claros para:
  - puntuar relevancia de cada fragmento
  - puntuar coherencia entre dos fragmentos consecutivos
  - evaluar la coherencia final del resumen
- Implementar caché de respuestas para no gastar tokens en cada iteración

## Día 4 — Algoritmos y primera integración
- Implementar algoritmo base sin LLM:
  - por ejemplo, selección por TF-IDF / frecuencia de palabras clave
  - orden preservado, largo máximo
- Implementar solver real:
  - DP exacto / knapsack con orden
  - si el tiempo permite, una versión heurística
- Implementar solver asistido por LLM:
  - usar scores de relevancia LLM para cada fragmento
  - usar score de transición para ordenar / validar
  - opcional: usar LLM para generar una lista de candidatos clave
- Probar flujo completo en 2-3 instancias

## Día 5 — Experimentos y análisis
- Ejecutar comparaciones:
  - baseline sin LLM vs. LLM-asistido
  - distintas formas de usar al LLM (relevancia solo / relevancia+coherencia)
  - posiblemente distintos prompts
- Recoger métricas:
  - longitud usada
  - cobertura de contenido
  - coherencia estimada por LLM
  - comparaciones cualitativas
- Guardar resultados en CSV y tablas
- Generar al menos un gráfico simple o tabla de comparación

## Día 6 — Documentación e informe
- Escribir informe técnico con estas secciones:
  1. descripción del problema
  2. modelado formal
  3. descripción de dataset utilizado
  4. diseño del algoritmo
  5. rol del LLM
  6. metodología experimental
  7. resultados y análisis
  8. limitaciones y mejoras
- Redactar README / `instructions.md`:
  - cómo instalar
  - cómo configurar LLM
  - cómo ejecutar experimentos
- Incluir:
  - `requirements.txt`
  - `.env.example`
  - ejemplos de salida

## Día 7 — Revisión final y cierre
- Probar todo de punta a punta:
  - carga de datos
  - solver base
  - solver LLM
  - generación de resultados
- Revisar que:
  - el código sea reproducible
  - el informe explique el rol del LLM claramente
  - el sistema NO dependa de llamadas LLM innecesarias
- Ajustar detalles finales
- Empaquetar entrega:
  - `src/`
  - `data/`
  - `README.md`
  - `informe/`
  - `requirements.txt`
  - `.env.example`

---

## Enfoque recomendado para la entrega
- Entregar código fuente completo
- Entregar dataset / instancias
- Entregar instrucciones de ejecución
- Entregar configuración de LLM
- Entregar informe técnico

## Puntos clave para la nota
- Usa el LLM como **evaluador de coherencia** y **relevancia**, no como generador único.
- Mantén un solver clásico visible: por ejemplo, DP + selección ordenada.
- Documenta bien el contraste: `sin LLM` vs `con LLM` y `relevancia` vs `coherencia`.
- Explica por qué tu sistema cumple el requisito del tema 2: seleccionar y ordenar fragmentos.