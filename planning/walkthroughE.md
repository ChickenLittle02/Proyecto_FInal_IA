# Walkthrough — Task E: Solver unificado (reordenar automáticamente)

El enunciado del Tema 2 exige **seleccionar y ordenar** fragmentos. Antes, el usuario debía elegir manualmente entre subsecuencia fija (`run_example.py --llm`) o reordenación explícita (`--reorder` / `solve_with_llm_reorder`). Task E unifica el flujo: el sistema **siempre** devuelve un orden de reproducción coherente y elige la estrategia según el tamaño de la instancia.

## Problema resuelto

| Antes | Después |
|---|---|
| Input permutado → salida incorrecta con `--llm` | `solve()` reordena automáticamente |
| Usuario activa `--reorder` a mano | Enrutado interno por `n` fragmentos |
| DP exacto inviable en `video_*.json` (n≈50) | Heurística 2 fases para n > 12 |

`SelectionProblem.validate_order()` detecta input desordenado, pero el usuario **no necesita** consultarlo ni pasar flags.

## Diseño: enrutado automático

Punto de entrada único en `src/solver/llm_assisted.py`:

| Función | Con LLM | Sin LLM |
|---|---|---|
| `solve(problem, llm_client)` | Producción | — |
| `solve_baseline(problem)` | — | Referencia clásica |

Ambas devuelven `(indices, score, mode_str)` e imprimen el modo:

```
Solver: exact_reorder (n=5)
Solver: heuristic_reorder (n=30, input desordenado según start_time)
```

### Tabla exacto vs heurístico

| n fragmentos | Modo | Algoritmo | Complejidad | Calidad |
|---|---|---|---|---|
| ≤ 12 | `exact_reorder` | DP bitmask (`unordered_knapsack_dp_with_coherence`) | O(2ⁿ · n · capacidad) | Óptimo |
| > 12 | `heuristic_reorder` | Fase 1: subconjunto greedy (relevancia/duración); Fase 2: inserción greedy sobre matriz de coherencia | O(n²) por fase | Aproximada |

**Por qué no siempre DP exacto:** con n=50 hay ~10¹⁵ estados — inviable en práctica. La heurística escala y sigue reordenando cuando el input llega permutado.

### Qué ocurre si no se distingue por tamaño

| Decisión incorrecta | Efecto |
|---|---|
| DP exacto siempre | Videos de 25–50 fragmentos: tiempo/memoria prohibitivos; experimentos con LLM inviables (O(n²) coherencia). |
| Heurística siempre | En bench (n=5) resultados subóptimos; casos diseñados (`bench_disordered`) dejan de validar reordenación óptima. |
| Sin reordenación (solo subsecuencia) | Input permutado produce resumen incoherente aunque la selección de fragmentos sea buena. |

El umbral **12** (`REORDER_EXACT_LIMIT`) deja exactitud demostrable en laboratorio (`mini_video_*`, n=10) y escalabilidad en producción (`video_*`). Documentación para usuarios: `README.md` § *Por qué se distingue el tamaño*; informe: `informe/informe_tecnico.md` §5.

### Heurística (n > 12)

Implementación en `src/solver/reorder.py`:

1. **`select_subset_greedy`** — elige fragmentos por ratio relevancia/duración hasta agotar `max_duration`.
2. **`order_subset_greedy`** — inserta cada fragmento restante en la posición que maximiza relevancia + coherencia entre pares consecutivos.
3. **`heuristic_reorder_with_coherence`** — orquesta ambas fases.

Variantes LLM / baseline:

- `solve_with_llm_heuristic_reorder` — matriz de coherencia vía `LLMClient.score_coherence`.
- `solve_baseline_heuristic_reorder` — coherencia proxy por `start_time` (`build_temporal_coherence_fn`).

## Puntos de entrada actualizados

| Script | Comportamiento |
|---|---|
| `run_example.py --llm` | `solve()` |
| `run_example.py` (sin flag) | `solve_baseline()` |
| `run_experiments.py` → `baseline`, `llm_dynamic` | `solve_baseline()` / `solve()` |
| `run_experiments.py --reorder` | Alias legacy (`baseline_reorder`, `llm_reorder`) — delega en las mismas funciones unificadas; solo para comparación en el informe |

Funciones legacy (`solve_with_llm`, `solve_with_llm_reorder`, etc.) se conservan para tests y contrastes experimentales.

## Validación

### Mock (sin API)

```bash
python src/test_bench_instances.py
```

Casos clave:

- `bench_disordered.json` + `solve()` mock → `[1, 4, 3, 0]` (orden narrativo, omite índice 2).
- `bench_irrelevant_middle.json` + `solve()` mock → omite índice 2 (input ya ordenado).
- Instancia sintética n=15 inline → `heuristic_reorder`.

### End-to-end con LLM

```bash
python src/run_example.py bench_disordered.json --llm
python src/run_example.py bench_irrelevant_middle.json --llm
```

### Bloque 6b (ejecutado)

Resultado en `results/part06b_disordered.csv` (solver unificado, sin `--reorder`):

| solver | selected_indices | notas |
|---|---|---|
| baseline | `[1, 4, 2, 3]` | reordenación exacta; omite irrelevante (índice 2) |
| llm_dynamic | `[0, 3, 4, 1]` | reordenación exacta; omite irrelevante; orden depende de scores LLM reales |

Los tests mock fijan scores y validan `[1, 4, 3, 0]`; con API real el orden puede variar según el modelo.

## Texto sugerido para el informe (limitaciones)

> El solver unificado enruta automáticamente: DP exacto con bitmask para n ≤ 12 (óptimo, O(2ⁿ)) y heurística en dos fases para n > 12 (aproximada, O(n²)). En videos completos (25–50 fragmentos) la heurística garantiza tiempo razonable pero no optimalidad global. Los flags `--reorder` y las funciones `solve_with_llm` / `solve_with_llm_reorder` se mantienen solo para contrastar subsecuencia fija vs reordenación en el análisis experimental (`bench_disordered.json`).

## Criterios de aceptación Task E

- [x] `run_example.py CUALQUIER.json --llm` sin saber si el input está ordenado.
- [x] `bench_disordered.json` → orden narrativo automático.
- [x] `bench_irrelevant_middle.json` → omite fragmento irrelevante.
- [x] `mini_video_*.json` (n=10) → `exact_reorder`.
- [x] `video_*.json` (n>12) → `heuristic_reorder` (escala).
- [x] Flags legacy disponibles para experimentos.

## Referencias

- Plan detallado: `planning/taskE.md`
- Código: `src/solver/llm_assisted.py`, `src/solver/reorder.py`
- Tests: `src/test_bench_instances.py`
