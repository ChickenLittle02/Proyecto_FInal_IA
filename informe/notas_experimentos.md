# Notas de experimentos — suite lite

Generado automáticamente: 2026-06-11 20:37 UTC

- Proveedor: `groq`
- Modelo: `llama-3.3-70b-versatile`
- Caché LLM (`.llm_cache.json`) **eliminada** al inicio de la suite.

Cada bloque registra escenario, selecciones, observación cualitativa y métricas para la sección *Resultados y análisis* del informe.
## Bloque 3 — example_instance

**Instancia:** `example_instance.json`

**Escenario:** Caso base sintético (5 fragmentos, max_duration=45). Comprueba selección relevante dentro del límite de duración.

**Selección (`selected_indices`):**

- baseline: `[0, 1, 2, 3, 4]`
- llm_dynamic: `[0, 2, 1, 3, 4]`
- llm_static: `[0, 1, 2, 3, 4]`

**Observación cualitativa:** Mismo subconjunto que el baseline pero en distinto orden de reproducción.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline | 3.425 | 1.000 |
| llm_dynamic | 3.625 | 1.000 |
| llm_static | 3.425 | 1.000 |

## Bloque 4 — example_instance_overlimit

**Instancia:** `example_instance_overlimit.json`

**Escenario:** Mismo contenido que example_instance con max_duration=30 (más estricto). Comprueba recorte cuando no caben todos los fragmentos.

**Selección (`selected_indices`):**

- baseline: `[2, 3, 4]`
- llm_dynamic: `[0, 2, 1]`
- llm_static: `[0, 2, 4]`

**Observación cualitativa:** La selección del LLM dinámico difiere del baseline.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline | 1.975 | 0.900 |
| llm_dynamic | 2.325 | 0.900 |
| llm_static | 2.200 | 0.933 |

## Bloque 5 — bench_static_vs_dynamic

**Instancia:** `bench_static_vs_dynamic.json`

**Escenario:** Escenario «salto»: coherencia alta entre (0,2) pero baja en el puente (0,1,2). Contrasta solver estático (vecinos fijos) vs dinámico (transiciones reales).

**Selección (`selected_indices`):**

- baseline: `[0, 1]`
- llm_dynamic: `[0, 2]`
- llm_static: `[0, 2]`

**Observación cualitativa:** Estático y dinámico coinciden en esta corrida. La selección del LLM dinámico difiere del baseline.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline | 1.025 | 1.000 |
| llm_dynamic | 1.550 | 1.000 |
| llm_static | 1.550 | 1.000 |

## Bloque 6 — bench_irrelevant_middle

**Instancia:** `bench_irrelevant_middle.json`

**Escenario:** Fragmento central irrelevante (música/anuncio, índice 2). Input en orden cronológico; debe omitirse el segmento sin contenido educativo.

**Selección (`selected_indices`):**

- baseline: `[0]`
- llm_dynamic: `[1]`
- llm_static: `[0]`

**Observación cualitativa:** Omite el fragmento irrelevante (índice 2). La selección del LLM dinámico difiere del baseline.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline | 0.600 | 0.744 |
| llm_dynamic | 0.675 | 0.930 |
| llm_static | 0.600 | 0.744 |

## Bloque 6b — bench_disordered

**Instancia:** `bench_disordered.json`

**Escenario:** Mismos textos que bench_irrelevant_middle pero array permutado en el JSON. Valida reordenación automática hacia orden narrativo (Task E).

**Selección (`selected_indices`):**

- baseline: `[1, 4, 2, 3]`
- llm_dynamic: `[1, 4, 0, 3]`
- llm_static: `[0, 1, 3, 4]`

**Observación cualitativa:** Omite el fragmento irrelevante (índice 2). Reordena el input permutado hacia un orden narrativo coherente. La selección del LLM dinámico difiere del baseline.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline | 2.125 | 1.000 |
| llm_dynamic | 3.175 | 1.000 |
| llm_static | 3.000 | 1.000 |

## Resumen final — Fase 8

Artefactos generados para el informe:

- CSV fusionado: `results/experiments_bench.csv` (15 filas)
- Tabla resumen: `results/summary_bench.md`
- Gráfico: `results/comparison_bench.png`

Sección del informe sugerida: **Resultados y análisis** — redactada en `informe/informe_tecnico.md` §6.

Contexto del problema, algoritmos testeados y distinción por tamaño: `informe/informe_tecnico.md` §1–5.
## Suite lite — beam Fase 2 — bench_disordered.json

**Instancia:** `bench_disordered.json`

**Escenario:** Mismos textos que bench_irrelevant_middle pero array permutado en el JSON. Valida reordenación automática hacia orden narrativo (Task E).

**Selección (`selected_indices`):**

- baseline_beam: `[1, 4, 2, 3]`
- llm_beam: `[1, 4, 0, 3]`

**Observación cualitativa:** Omite el fragmento irrelevante (índice 2). Reordena el input permutado hacia un orden narrativo coherente. La selección de llm_beam difiere del baseline_beam.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 2.150 | 1.000 |
| llm_beam | 3.175 | 1.000 |

## Suite lite — beam Fase 2 — bench_irrelevant_middle.json

**Instancia:** `bench_irrelevant_middle.json`

**Escenario:** Fragmento central irrelevante (música/anuncio, índice 2). Input en orden cronológico; debe omitirse el segmento sin contenido educativo.

**Selección (`selected_indices`):**

- baseline_beam: `[0]`
- llm_beam: `[1]`

**Observación cualitativa:** Omite el fragmento irrelevante (índice 2). La selección de llm_beam difiere del baseline_beam.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 0.600 | 0.744 |
| llm_beam | 0.675 | 0.930 |

## Suite lite — beam Fase 2 — bench_static_vs_dynamic.json

**Instancia:** `bench_static_vs_dynamic.json`

**Escenario:** Escenario «salto»: coherencia alta entre (0,2) pero baja en el puente (0,1,2). Contrasta solver estático (vecinos fijos) vs dinámico (transiciones reales).

**Selección (`selected_indices`):**

- baseline_beam: `[0, 1]`
- llm_beam: `[0, 2]`

**Observación cualitativa:** La selección de llm_beam difiere del baseline_beam.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 1.025 | 1.000 |
| llm_beam | 1.550 | 1.000 |

## Suite lite — beam Fase 2 — example_instance.json

**Instancia:** `example_instance.json`

**Escenario:** Caso base sintético (5 fragmentos, max_duration=45). Comprueba selección relevante dentro del límite de duración.

**Selección (`selected_indices`):**

- baseline_beam: `[0, 1, 2, 3, 4]`
- llm_beam: `[4, 2, 1, 0, 3]`

**Observación cualitativa:** Mismo subconjunto que el baseline pero en distinto orden de reproducción.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 1.800 | 1.000 |
| llm_beam | 2.337 | 1.000 |

## Suite lite — beam Fase 2 — example_instance_overlimit.json

**Instancia:** `example_instance_overlimit.json`

**Escenario:** Mismo contenido que example_instance con max_duration=30 (más estricto). Comprueba recorte cuando no caben todos los fragmentos.

**Selección (`selected_indices`):**

- baseline_beam: `[2, 3, 4]`
- llm_beam: `[2, 1, 4]`

**Observación cualitativa:** La selección de llm_beam difiere del baseline_beam.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 0.938 | 0.900 |
| llm_beam | 1.962 | 1.000 |

## F5 Bloque 1 — escalado dur_5min

**Instancia:** `dur_5min.json`

**Escenario:** Instancia de evaluación (sin descripción registrada).

**Selección (`selected_indices`):**

- baseline_beam: `[7, 8, 9]`
- llm_beam: `[8, 9, 10]`

**Observación cualitativa:** La selección de llm_beam difiere del baseline_beam.

**Métricas clave:**

| solver | objective_score | duration_utilization |
| --- | --- | --- |
| baseline_beam | 2.225 | 0.961 |
| llm_beam | 2.250 | 0.990 |

