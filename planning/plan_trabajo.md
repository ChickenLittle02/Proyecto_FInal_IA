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
- [x] dataset / instancias
- [x] implementación algorítmica + versión asistida por LLM (DP con coherencia dinámica — Paso C)
- [x] configuración de LLM reproducible (`.env.example`, cliente Gemini, validación con `test_llm.py`)
- [/] análisis experimental (Paso D: suite bench, CSV, gráficos en `results/`)
- [ ] informe técnico
- [ ] instrucciones de ejecución

---

## Día 1 — Definición y diseño
- [x] Definir el problema formal:
  - [x] variables: fragmentos `s_i`, longitud `l_i`, selección `x_i \in {0,1}`
  - [x] restricción: suma de longitudes ≤ límite
  - [x] objetivo: maximizar relevancia + coherencia del resumen
  - [x] orden preservado según el video original
- [x] Decidir el modelo algorítmico:
  - [x] variante de **DP / knapsack con orden** para seleccionar fragmentos
  - [x] o “subset selection con penalty de transición”
- [x] Anotar claramente qué hace el algoritmo clásico vs el LLM
- [x] Escribir un esquema de la estructura del proyecto:
  - [x] `src/problem.py`, `src/instance.py`, `src/solver/baseline.py`, `src/solver/llm_assisted.py`, `src/llm/`

## Día 2 — Dataset e instancias
- [x] Recolectar o generar dataset:
  - [x] Usar 2–3 videos reales (Procesados los subtítulos `.srt` de las 4 carpetas de videos reales y segmentados en archivos JSON en `data/instances/video_*.json`)
  - [x] Extraer fragmentos cortos + transcripciones
  - [x] Crear instancias en JSON con: texto, duración, posición (start_time, end_time)
- [x] Crear instancias de prueba razonables:
  - [x] videos de 5-10 fragmentos (`example_instance.json`)
  - [x] casos con segmentos muy relevantes y segmentos irrelevantes
- [x] Crear instancia bench con fragmentos **deliberadamente desordenados** en el JSON:
  - [x] `data/instances/bench_disordered.json` — mismos textos que `bench_irrelevant_middle.json`, array permutado (conclusión en posición 0, introducción en 1)
  - [x] conservar `start_time` / `end_time` correctos en cada fragmento
  - [x] `max_duration=35.0` — caben los 4 fragmentos narrativos (8+10+9+8) omitiendo el irrelevante
  - [x] test mock en `src/test_bench_instances.py`: verifica orden `[1, 4, 3, 0]` y omisión del índice 2
- [x] Implementar loader de datos:
  - [x] `data/instances/`
  - [x] función para leer fragmentos y longitudes (`src/instance.py`)
- [ ] Guardar el proceso de generación en el informe (Se documentará en el informe final)

## Día 3 — LLM + prompts + caché
- [x] Elegir proveedor / modo de desarrollo:
  - [x] local (Ollama) o API (OpenAI / Anthropic / Gemini) -> Elegido **Gemini** (`src/llm/client.py`)
  - [x] Integrar el cliente real del proveedor elegido (`_invoke_model` llama a `google-generativeai`)
- [x] Crear wrapper de LLM:
  - [x] env var para modelo y API key (`GEMINI_API_KEY`, `LLM_MODEL`, `LLM_PROVIDER`)
  - [x] `src/llm/client.py` (llamada real a Gemini + parseo con regex)
  - [x] `src/llm/prompts.py` (Prompts base definidos)
  - [x] `src/llm/cache.py` (Caché local en disco implementada)
- [/] Diseñar prompts claros para:
  - [x] puntuar relevancia de cada fragmento
  - [x] puntuar coherencia entre dos fragmentos consecutivos
  - [ ] evaluar la coherencia final del resumen (opcional / refinar)
- [x] Implementar caché de respuestas para no gastar tokens en cada iteración
- [x] Validar integración end-to-end:
  - [x] Script de prueba `src/test_llm.py` (score real: 0.95 con `gemini-2.5-flash`)
  - [x] Llamadas reales devuelven puntuaciones distintas de `0.0`
  - [x] Crear `.env.example`

## Día 4 — Algoritmos y primera integración
- [x] Implementar algoritmo base sin LLM (ej. DP y greedy en `src/solver/baseline.py`)
- [x] Implementar solver real:
  - [x] DP exacto / knapsack con orden (`src/solver/baseline.py`)
- [x] Implementar solver asistido por LLM:
  - [x] usar scores de relevancia LLM para cada fragmento
  - [x] coherencia dinámica en el DP (`ordered_knapsack_dp_with_coherence`, estado `(index, remaining, last_selected)`)
  - [x] prueba mock sin API (`src/test_llm_solver.py`)
- [/] Probar flujo completo en las instancias reales y sintéticas creadas con el LLM real activo
  - [x] Instancia sintética (`python src/run_example.py --llm`)
  - [x] Suite lite sintética (`--suite lite` en `run_experiments.py`)
  - [ ] Instancias `mini_video_*` / `video_*.json` completas — no ejecutadas (coste API); mini generados con `prepare_mini_instances.py`

### Extensión — Selección **con** reordenación (implementada)

**Modo orden fijo:** el DP (`ordered_knapsack_dp`, `ordered_knapsack_dp_with_coherence`) solo elige *incluir u omitir* en la posición del array de entrada. La salida es siempre una **subsecuencia** del orden del JSON.

**Modo reordenación:** `unordered_knapsack_dp_with_coherence` + `solve_with_llm_reorder` eligen subconjunto y permutación; validado con `bench_disordered.json`.

**Problema formal ampliado:** dado un conjunto de fragmentos (posiblemente desordenados en el input), elegir un subconjunto *y* una **permutación** π tal que:
- ∑ duración(π) ≤ límite
- se maximiza relevancia + coherencia entre pares **consecutivos en π** (no en el array original)

**Enfoque recomendado (exacto para n pequeño, n ≤ 12 en bench):**

1. **Matriz de coherencia:** precalcular `coherence[i][j]` para todo par (i, j) vía LLM (caché en `.llm_cache.json`); O(n²) llamadas, aceptable en instancias bench.
2. **DP con máscara de bits:** estado `(mask, last, remaining)` donde `mask` indica qué fragmentos ya están en el resumen y `last` es el último añadido. Transición: añadir `j ∉ mask` si cabe en duración. Complejidad O(2ⁿ · n · capacidad) — viable para los bench de 5 fragmentos.
3. **Salida:** lista ordenada de índices `[j₁, j₂, …, jₖ]` (no necesariamente creciente).
4. **Validación:** nueva función `is_valid_ordered_selection(order)` en `problem.py` (comprueba duración y que no haya índices repetidos; **no** exige `sorted(order)`).
5. **Solver baseline sin LLM:** misma DP con matriz de coherencia uniforme o heurística (p. ej. coherencia = −|start_time_i − start_time_j| como proxy temporal).
6. **Integración LLM:** `solve_with_llm_reorder()` en `src/solver/llm_assisted.py`, reutilizando `score_fragment` y `score_coherence(i, j)` para cualquier par.

**Alternativa más simple (no óptima):** dos fases — (1) knapsack sin orden para elegir subconjunto; (2) TSP / inserción greedy sobre el subconjunto usando la matriz de coherencia. Más rápida, peor calidad; útil como baseline heurístico.

**Tareas:**

- [x] Implementar `unordered_knapsack_dp_with_coherence` (DP con bitmask) en `src/solver/reorder.py`
- [x] Implementar `solve_with_llm_reorder` en `src/solver/llm_assisted.py`
- [x] Añadir `is_valid_ordered_selection` en `src/problem.py` (`is_valid_selection` sin cambios — subsecuencia)
- [x] Crear `bench_disordered.json` (ver Día 2)
- [x] Añadir tests mock: orden de salida narrativamente correcto pese al input permutado
- [x] Añadir bloque de experimentos en README / `run_experiments.py` (`--reorder`, Bloque 6b)
- [ ] Documentar en informe: contraste *subsecuencia fija* vs *reordenación* y cuándo cada uno aplica

## Día 5 — Experimentos y análisis

### Qué se hizo con los videos de prueba

1. **Videos completos** (`video_*.json`): generados en Día 2 desde subtítulos SRT; 25–50 fragmentos; baseline evaluado en CSV global; **sin corrida LLM** (demasiado costoso).

2. **Mini-resúmenes** (`mini_video_*.json`): script `prepare_mini_instances.py` extrae los **10 primeros fragmentos** de cada video y recalcula `max_duration` al 25 % de ese subconjunto. Archivos generados y listos; **no ejecutados con LLM** en esta fase (la suite `--suite bench` los incluiría y superaría cientos de llamadas API).

3. **Casos sencillos sintéticos** (5 fragmentos): `example_*`, `bench_*`. Son la base cuantitativa del informe. Comando recomendado:

   ```bash
   python src/run_experiments.py --suite lite --llm --static --evaluate \
     --output results/experiments_bench.csv
   ```

4. **Suite `--suite bench` (lite + mini_video)**: documentada pero **no ejecutada** — casos demasiado grandes para el plan/tiempo disponible.

- [x] Ejecutar comparaciones en instancias **lite** (sintéticas)
- [x] baseline vs LLM-asistido con `--evaluate`
- [x] estático vs dinámico (`bench_static_vs_dynamic.json`)
- [ ] suite completa con `mini_video_*` (opcional, no recomendada)
- [x] Recoger métricas estructurales y post-hoc
- [x] `results/experiments.csv` (example_instance)
- [x] `results/experiments_bench.csv` (suite lite)
- [x] `prepare_mini_instances.py`, instancias `bench_*`, `mini_video_*` generadas
- [x] Documentación en `walkthroughD.md` (origen, corte, uso, limitaciones)

## Día 6 — Documentación e informe
- [ ] Escribir informe técnico con estas secciones:
  1. descripción del problema
  2. modelado formal (con referencias a los capítulos de `temas-simulacion.pdf` si aplica, como lógica difusa para grados de relevancia, etc.)
  3. descripción de dataset utilizado
  4. diseño del algoritmo
  5. rol del LLM
  6. metodología experimental
  7. resultados y análisis
  8. limitaciones y mejoras (contraste subsecuencia fija vs reordenación con `bench_disordered.json`)
- [ ] Redactar README / `instructions.md` final con instrucciones detalladas de ejecución
- [x] Incluir `requirements.txt` (`google-generativeai`, `python-dotenv`)
- [x] Crear `.env.example`
- [ ] Ejemplos de salida

## Día 7 — Revisión final y cierre
- [ ] Probar todo de punta a punta:
  - [ ] carga de datos
  - [ ] solver base
  - [ ] solver LLM
  - [ ] generación de resultados
- [ ] Revisar que:
  - [ ] el código sea reproducible
  - [ ] el informe explique el rol del LLM claramente
  - [ ] el sistema NO dependa de llamadas LLM innecesarias (verificar funcionamiento de caché)
- [ ] Ajustar detalles finales
- [ ] Empaquetar entrega:
  - [ ] `src/`
  - [ ] `data/`
  - [ ] `README.md`
  - [ ] `informe/`
  - [ ] `requirements.txt`
  - [x] `.env.example`

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
- Con la extensión de reordenación + `bench_disordered.json`, demuestra que el sistema no solo elige fragmentos sino que **reconstruye un orden lógico** cuando el input llega permutado.