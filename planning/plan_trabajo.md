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

### Fase 1 (completada) — MVP algorítmico + LLM micro
- [x] dataset / instancias
- [x] implementación algorítmica + versión asistida por LLM (DP con coherencia dinámica — Paso C)
- [x] configuración de LLM reproducible (`.env.example`, cliente Gemini/Groq, validación con `test_llm.py`)
- [x] análisis experimental (Paso D: suite lite, CSV, gráficos en `results/`)
- [x] ejecución manual bloque a bloque (`execute.md`, bloques 3–8 + fusión + Fase 8)
- [x] Task E: solver unificado con enrutado n≤12 / n>12 (`planning/walkthroughE.md`)

### Fase 2 (actual) — Algoritmo único + LLM evalúa resúmenes
Refactorizar hacia **un solo pipeline** que, para cualquier n, reciba fragmentos de video educativo y devuelva un subconjunto ordenado bajo `max_duration`, usando el LLM para evaluar **relevancia y coherencia de los resúmenes generados** (no solo de fragmentos sueltos).

**Entregables Fase 2:**
- [x] `src/solver/unified.py` — **único** solver de producción (beam search) para todo n
- [x] `src/llm/scoring.py` — precálculo cacheado relevance + coherence
- [x] `src/llm/prompts.py` + `LLMClient.evaluate_summary()` — evaluación macro del resumen
- [x] `solve()` / `solve_baseline()` → beam search (con / sin scores LLM); sin bifurcaciones ni modos alternativos
- [x] **Limpieza:** eliminar o aislar fuera de producción todo solver legacy (DP, heurística, `--static`, flags `--reorder`, etc.)
- [/] **Documentación única:** README, `execute.md`, informe §2–4 describen **solo** el pipeline beam search
- [x] Tests de regresión (bench disordered, irrelevant_middle; n=15 mock; ablation `beam_width` → F5)
- [/] Experimentos de escalado (duraciones 5/10/15/20 min, caché completo) — dur_5min ✅
- [/] informe técnico actualizado (`informe/estructura_informe.md` como guía narrativa)
- [/] instrucciones de ejecución finales (un solo flujo CLI)

**Principio de diseño:** el LLM **no elige índices**; el algoritmo combina y ordena; el LLM **puntúa** (micro: fragmentos/pares cacheados; macro: texto del resumen candidato).

**Política de código y documentación (obligatoria):** al cerrar Fase 2, **solo debe quedar beam search** como algoritmo ejecutable. Ningún otro solver implementado (DP ordenado, DP bitmask, heurística 2 fases, greedy, `--static`, enrutado n≤12/n>12, etc.) puede permanecer en rutas de producción, CLI, README, `execute.md` ni informe como opción de ejecución. Ver **§ Política: solo beam search** al final de este documento.

Ver **§ Fase 2 — Refactor arquitectónico** al final de este documento.

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
  - [x] evaluar relevancia y coherencia del **resumen completo** → **Fase 2, Día 7A (F3)**
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
  - [x] Bench disordered / irrelevant_middle con solver unificado (`run_example.py --llm`)
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
- [x] Documentar en informe: contraste *subsecuencia fija* vs *reordenación* y cuándo cada uno aplica → `informe/informe_tecnico.md` §2–5

### Task E — Solver unificado (reordenar automáticamente) → `planning/taskE.md`

**Problema:** hoy el usuario debe activar `--reorder` o llamar `solve_with_llm_reorder` a mano. El enunciado exige seleccionar **y** ordenar sin que el usuario defina si el input viene permutado.

**Por qué no DP exacto siempre:** complejidad O(2ⁿ). Con n=50 son ~10¹⁵ estados — inviable. La solución no es “no reordenar en videos grandes”, sino **cambiar de algoritmo según n**:

| n | Estrategia | Reordena |
|---|---|---|
| ≤ 12 | DP bitmask exacto (`solve_with_llm_reorder`) | Sí, óptimo |
| > 12 | Heurística 2 fases (subconjunto + orden greedy/2-opt) | Sí, aproximado |

- [x] **Prompt 1** — `solve()` + `solve_baseline()` + enrutado n≤12 + `run_example.py` + tests disordered sin flags
- [x] **Prompt 2** — heurística n>12 + `run_experiments.py` unificado + test n=15
- [x] **Prompt 3** — README, walkthroughE, Bloque 6b, cierre Task E en plan e informe

**Estado:** Task E completada. Enrutado automático en `solve()` / `solve_baseline()`; ver `planning/walkthroughE.md`.

> **Superseded by Fase 2:** el enrutado n≤12/n>12 se reemplazará por beam search unificado. El DP exacto pasa a módulo de referencia (`exact.py`), no a producción.

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
- [x] Ejecución manual por bloques (`execute.md`): Bloques 3–6b, fusión (Fase 7), tabla/gráfico (Fase 8)
- [x] `informe/notas_experimentos.md` generado automáticamente (15 filas, Groq)
- [ ] suite completa con `mini_video_*` (opcional, no recomendada)
- [x] Recoger métricas estructurales y post-hoc
- [x] `results/experiments.csv` (example_instance)
- [x] `results/experiments_bench.csv` (suite lite, 15 filas)
- [x] `results/summary_bench.md`, `results/comparison_bench.png`
- [x] `prepare_mini_instances.py`, instancias `bench_*`, `mini_video_*` generadas
- [x] Documentación en `walkthroughD.md` (origen, corte, uso, limitaciones)

## Día 6 — Refactor: algoritmo unificado (Fase 2, bloque A)

> Sustituye el enrutado n≤12/n>12 por un **único algoritmo de búsqueda** que escala a videos reales. Ver `planning/taskF.md` (crear al implementar).

### 6A — Capa semántica: precálculo cacheado
- [x] **`ScoreMatrix`** (nuevo módulo o en `src/llm/scoring.py`):
  - [x] `build_relevance_scores(problem, llm_client)` → vector n
  - [x] `build_coherence_matrix(problem, llm_client)` → matriz n×n (pares dirigidos)
  - [x] Reutilizar caché `.llm_cache.json`; log de progreso `fragmento i/n`, `par i,j`
- [x] Tests unitarios con mock: matriz simétrica en memo, sin llamadas duplicadas

### 6B — Capa combinatoria: `src/solver/unified.py`
- [x] **`beam_search_select_and_order(fragments, relevance, coherence, max_duration, beam_width)`**:
  - Estado: `(orden_parcial, duración_usada)`
  - Expansión: añadir cualquier fragmento no usado que quepa
  - Score local: `Σ relevancia + w·Σ coherencia(pares consecutivos)` (sin API en el bucle)
  - Devuelve `(indices_ordenados, score_local)`
- [x] Parámetro `beam_width` (default 10); documentar trade-off calidad/tiempo
- [x] **`unified_solve(problem, relevance, coherence, max_duration, beam_width)`** — punto de entrada interno

### 6C — Integración en `solve()` / `solve_baseline()`
- [x] `solve()`: precalcular scores LLM → `unified_solve()` top-M → `refine_with_summary_judge()`
- [x] `solve_baseline()`: mismo beam search con relevancia uniforme + coherencia temporal (`build_temporal_coherence_fn`)
- [x] Eliminar de producción: `REORDER_EXACT_LIMIT`, `resolve_solver_mode`, `exact_reorder` / `heuristic_reorder`, `solve_with_llm_static`, `solve_with_llm`, `solve_with_llm_reorder`, `solve_with_llm_heuristic_reorder`
- [x] Actualizar `run_example.py` y `run_experiments.py`: **solo** `baseline_beam` vs `llm_beam`; quitar `--static`, `--reorder` y cualquier flag de solver alternativo
- [x] Tests de regresión:
  - [x] `bench_disordered.json` — orden narrativo correcto
  - [x] `bench_irrelevant_middle.json` — omite índice irrelevante
  - [x] n=15 mock (`test_bench_instances.py`) — pasa con beam search

### 6D — Limpieza de código legacy (obligatoria)
- [x] **Eliminar o mover a `tests/legacy/`** (no importable desde producción):
  - [x] `src/solver/baseline.py` — DP ordenado / greedy
  - [x] `src/solver/reorder.py` — DP bitmask + heurística 2 fases
  - [x] Funciones DP en `src/solver/llm_assisted.py` (`ordered_knapsack_dp_with_coherence`, etc.)
- [x] Dejar **un solo módulo combinatorio:** `src/solver/unified.py` (+ thin wrapper en `llm_assisted.py` si conviene)
- [x] Actualizar imports en tests: mocks contra beam; sin dependencias de solvers borrados
- [x] Verificar `python src/run_example.py` y `python src/run_experiments.py --suite lite` sin rutas legacy

## Día 7 — LLM evalúa resúmenes + experimentos (Fase 2, bloque B)

### 7A — Evaluación macro del resumen (alineación con enunciado)
- [x] **`summary_evaluation_prompt(summary_text, max_duration)`** en `src/llm/prompts.py`:
  - Devuelve: `relevance`, `coherence`, `overall` ∈ [0, 1] (JSON o tres números)
- [x] **`LLMClient.evaluate_summary(summary_text, max_duration)`** en `client.py`
- [x] **`refine_with_summary_judge(candidates, llm_client)`**:
  - Top-M candidatos del beam (M=3–5) → evaluar resumen completo → elegir mejor `overall`
- [x] Integrar en `solve()` como paso final opcional (`--summary-refine-top-m`; default M=3)
- [x] Métrica nueva en CSV: `summary_llm_score`, `summary_llm_relevance`, `summary_llm_coherence`
- [x] Test `test_llm.py` ampliado: evaluar texto de resumen ficticio

### 7B — Experimentos de validación
- [x] Generar instancias por duración desde `video_2.json`:
  - `dur_5min` (n=12), `dur_10min` (n=23), `dur_15min` (n=34), `dur_20min` (n=47)
  - Script: `prepare_mini_instances.py --target-minutes` + `--source-video`
- [/] Corrida 1: poblar caché completo (baseline + unified + `--evaluate`) — `dur_5min` ✅; dur_10/15/20 pendiente
- [ ] Corrida 2: verificar re-ejecución instantánea (caché)
- [ ] Ablation: `beam_width` ∈ {3, 5, 10} en n=5 y n=23
- [ ] Comparativa: **baseline beam** (sin LLM) vs **llm beam** (+ juez macro) — tabla en `results/unified_scaling.csv`
- [ ] Actualizar `informe/notas_experimentos.md` y `results/summary_*.md`
- [ ] Reescribir `execute.md` con **un solo flujo** (beam baseline + beam LLM); marcar bloques Task E como obsoletos

### 7C — Documentación e informe
- [/] Informe siguiendo `informe/estructura_informe.md`:
  1. [x] descripción del problema → §1
  2. [ ] modelado formal (+ lógica difusa / agente percibe-decide si aplica)
  3. [ ] descripción de dataset (`prepare_dataset.py`, cortes por duración)
  4. [ ] **rediseño algoritmo unificado** → reemplazar §2–3 antiguos (beam + evaluación de resumen)
  5. [ ] **rol del LLM dual** (micro guía + macro juez) → §4
  6. [ ] metodología experimental (ablation beam, escalado duración) → §5
  7. [ ] resultados unified vs baseline → §6
  8. [ ] limitaciones (aproximación vs óptimo; coste n² precálculo) → §7
- [ ] README: sección «Arquitectura unificada»; **solo beam search**; sin mencionar DP/heurística como opciones ejecutables
- [ ] Informe: § algoritmos — describir beam search; mencionar solvers legacy **solo** en «trabajo previo» o eliminarlos del informe final
- [ ] `planning/walkthroughF.md` — walkthrough del refactor
- [ ] Ejemplos de salida con `Solver: unified_beam (n=..., beam=10)`

## Día 8 — Revisión final y cierre
- [ ] Probar todo de punta a punta:
  - [ ] carga de datos
  - [ ] solver base (unified, sin LLM)
  - [ ] solver LLM (precálculo + beam + evaluación resumen)
  - [ ] generación de resultados / CSV
- [ ] Revisar que:
  - [ ] el código sea reproducible
  - [ ] el informe explique que el LLM evalúa **resúmenes generados**
  - [ ] caché completo evite llamadas redundantes en re-ejecuciones
  - [ ] tests mock + al menos 1 instancia real pasen
- [ ] Empaquetar entrega:
  - [ ] `src/`
  - [ ] `data/`
  - [ ] `README.md`
  - [ ] `informe/`
  - [ ] `requirements.txt`
  - [x] `.env.example`

---

## Enfoque recomendado para la entrega
- Entregar código con **un solo algoritmo combinatorio:** beam search (`solve` / `solve_baseline`)
- **No** entregar rutas ejecutables para DP, heurística 2 fases, greedy ni variantes `--static`
- Entregar dataset / instancias (sintéticas + cortes por duración de `video_2`)
- Entregar instrucciones de ejecución (`README.md`, `execute.md`) con **un único pipeline**
- Entregar configuración de LLM (`.env.example`, caché documentada)
- Entregar informe técnico alineado con `informe/estructura_informe.md`

## Puntos clave para la nota
- El LLM evalúa **coherencia y relevancia de resúmenes generados** (evaluación macro) y aporta scores locales (micro) que guían la búsqueda.
- El **algoritmo clásico** es **beam search** combinatorio; el LLM no sustituye la optimización.
- Documentar contraste: `baseline beam` (scores proxy) vs `llm beam` (scores semánticos) y `score local` vs `evaluación de resumen`.
- Un solo flujo: fragmentos → precálculo → beam search → juez macro → resumen ordenado bajo límite temporal, cualquier n.
- `bench_disordered.json` demuestra selección **y** reordenación cuando el input llega permutado.

---

## Fase 2 — Refactor arquitectónico (detalle)

### Por qué cambiar

| Aspecto | Estado actual (Task E) | Objetivo Fase 2 |
|---|---|---|
| Algoritmos | DP exacto (n≤12) + heurística 2 fases (n>12) | **Beam search único** para todo n |
| Rol del LLM | Puntúa fragmentos y pares durante el DP | Puntúa resúmenes **completos** + matriz cacheada guía la búsqueda |
| API | `REORDER_EXACT_LIMIT`, modos `exact_reorder` / `heuristic_reorder` | `solve()` siempre → `unified_beam` |
| Enunciado | Parcial («evalúa pares») | Alineado («evalúa resúmenes generados») |

### Arquitectura objetivo

```
Entrada: fragmentos + max_duration
    │
    ▼
[Precálculo LLM cacheado]  relevance[n] + coherence[n×n]
    │
    ▼
[Beam search unificado]    selecciona + ordena (sin API en el bucle)
    │
    ▼
[Top-M candidatos]
    │
    ▼
[LLM evaluate_summary]     juez macro del texto del resumen
    │
    ▼
Salida: índices ordenados + métricas
```

### Orden de implementación (prompts para agente)

| # | Task | Archivos principales | Criterio de done |
|---|---|---|---|
| **F1** | Beam search + score matrix | `src/solver/unified.py`, `src/llm/scoring.py` | Tests n=5 pasan; bench_disordered OK |
| **F2** | Redirigir `solve()` + limpieza legacy | `llm_assisted.py`, eliminar `baseline.py`/`reorder.py` | Solo beam en CLI y tests de producción |
| **F3** | Evaluación de resumen | `src/llm/prompts.py`, `client.py` | `evaluate_summary()` + test |
| **F4** | Refinamiento top-M | `unified.py` o `llm_assisted.py` | Mejor candidato por `overall` LLM ✅ |
| **F5** | Experimentos + CSV | `run_experiments.py`, `metrics.py`, `execute.md` | `results/unified_scaling.csv`; docs sin solvers viejos |
| **F6** | Informe + README | `informe/`, `README.md` | Solo beam search documentado como algoritmo |

### Qué conservar del código actual

- `src/problem.py`, `src/instance.py`, dataset, caché, `run_experiments.py` (adaptados a beam)
- Suite lite como **regresión** con beam (baseline vs llm)
- Resultados históricos Task E en `results/` como referencia, no como pipeline activo

### Qué eliminar del código y la documentación (obligatorio)

- ❌ `src/solver/baseline.py`, `src/solver/reorder.py` y cualquier DP/heurística importable desde producción
- ❌ Flags CLI: `--static`, `--reorder`, modos `exact_reorder` / `heuristic_reorder`
- ❌ Referencias en README / `execute.md` / informe a «DP exacto», «heurística 2 fases», «knapsack ordenado» como **opciones de ejecución**
- ❌ Tres solvers en experimentos (`baseline` knapsack, `llm_static`, `llm_dynamic`) → sustituir por **dos filas:** `baseline_beam`, `llm_beam`

### Qué no hacer

- ❌ Que el LLM devuelva directamente la lista de índices (algoritmo trivial)
- ❌ Mantener dos algoritmos combinatorios en producción (DP + beam, heurística + beam, etc.)
- ❌ Dejar solvers legacy en `src/solver/` «por si acaso» accesibles desde `run_experiments.py`
- ❌ Ejecutar suite completa `video_*.json` sin caché poblada

---

## Política: solo beam search

Al terminar Fase 2, el repositorio debe cumplir:

| Ámbito | Permitido | Prohibido |
|---|---|---|
| **Algoritmo combinatorio** | Beam search (`unified.py`) | DP, greedy, SA, AG, heurística 2 fases |
| **Variantes de ejecución** | `baseline_beam` (scores proxy) y `llm_beam` (scores LLM + juez macro) | `--static`, `--reorder`, enrutado por n |
| **LLM en optimización** | Precálculo cacheado + juez macro final | Llamadas LLM dentro del bucle de búsqueda |
| **Documentación** | Un pipeline: precálculo → beam → top-M → evaluate_summary | Bloques execute.md con solvers Task E |
| **Informe** | Beam search como algoritmo entregado; contraste baseline vs LLM | Presentar DP/heurística como alternativas activas |
| **Tests** | Regresión sobre bench con beam; mocks sin API | Tests que importen solvers legacy desde `src/solver/` |

**Criterio de aceptación:** un revisor externo que lea README + `execute.md` + ejecute `run_example.py` / `run_experiments.py` solo encuentra **beam search** como método de selección y ordenación.

### Referencias internas

- Diseño previo Task E: `planning/taskE.md`, `planning/walkthroughE.md`
- Experimentos lite: `execute.md`, `planning/walkthroughD.md`
- Estructura informe narrativo: `informe/estructura_informe.md`
- Resultados baseline actuales: `results/experiments_bench.csv`, `informe/notas_experimentos.md`