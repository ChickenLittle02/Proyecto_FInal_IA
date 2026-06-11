# Task E — Solver unificado: reordenar automáticamente sin flags

## Problema a resolver

Hoy el usuario debe elegir manualmente entre dos modos:

| Modo | Cómo se activa | Comportamiento |
|---|---|---|
| Subsecuencia fija | `run_example.py --llm` (por defecto) | No reordena; respeta posición en el JSON |
| Reordenación | `run_experiments.py --reorder` o `solve_with_llm_reorder` explícito | Sí reordena |

El enunciado del proyecto (Tema 2) exige **seleccionar y ordenar** fragmentos. El sistema debe recibir fragmentos en cualquier orden y decidir solo si reordenar es necesario — **sin flags del usuario**.

`SelectionProblem.validate_order()` ya detecta input desordenado, pero **no se usa** en ningún punto de entrada.

---

## Por qué no usar siempre el DP exacto con bitmask (reorder) para n grande

No es una preferencia de diseño: es un **límite de complejidad**.

| n | Estados del DP (≈ 2ⁿ) | ¿Viable? |
|---|---|---|
| 5 | 32 | Sí (~ms) |
| 12 | 4 096 | Sí (~segundos) |
| 20 | ~1 millón | Límite |
| 30 | ~1 000 millones | No |
| 50 | ~10¹⁵ | Imposible en práctica |

Complejidad real: **O(2ⁿ · n · estados_de_capacidad)**.

Con `video_*.json` (25–50 fragmentos), el DP exacto con bitmask **colgaría o tardaría horas**. Eso no significa que no debamos reordenar: significa que para n grande hace falta una **heurística de reordenación** (dos fases: elegir subconjunto + ordenar con inserción greedy o 2-opt sobre la matriz de coherencia), ya descrita en `plan_trabajo.md` como alternativa.

**Conclusión reajustada:** el sistema debe **siempre intentar producir un orden de reproducción coherente**, pero la *estrategia* cambia según n:

```
n ≤ 12  → reorder exacto (DP bitmask)     — óptimo, cubre input ordenado y desordenado
n > 12  → reorder heurístico (2 fases)    — no óptimo, pero escala y reordena si hace falta
```

Si el input ya viene cronológico y la heurística no mejora el orden, la salida coincide con el orden del video. Si viene permutado, la heurística (o el DP exacto) lo corrige.

---

## Diseño objetivo

### API pública (`src/solver/llm_assisted.py`)

```python
def resolve_solver_mode(problem: SelectionProblem) -> str:
    """Devuelve 'exact_reorder' | 'heuristic_reorder'."""

def solve(problem, llm_client, coherence_weight=0.25) -> Tuple[List[int], float, str]:
    """Punto de entrada único. Siempre devuelve orden de reproducción."""
```

Equivalente sin LLM en `src/solver/reorder.py` o `baseline.py`:

```python
def solve_baseline(problem, coherence_weight=0.25) -> Tuple[List[int], float, str]:
```

### Enrutado automático

```python
REORDER_EXACT_LIMIT = 12

if n <= REORDER_EXACT_LIMIT:
    return solve_with_llm_reorder(...)   # o solve_baseline_reorder
else:
    return solve_with_llm_heuristic_reorder(...)  # NUEVO — Prompt 2
```

### Puntos de entrada a actualizar

- `src/run_example.py` — `--llm` usa `solve()`; sin `--llm` usa `solve_baseline()`
- `src/run_experiments.py` — `llm_dynamic` usa `solve()`; `baseline` usa `solve_baseline()`
- Mantener `--reorder` / `llm_reorder` / `llm_dynamic` (ordenado) solo como **aliases de experimento** para el informe, no como flujo normal

### Logging obligatorio

Imprimir en cada ejecución:

```
Solver: exact_reorder (n=5)
Solver: heuristic_reorder (n=30, input desordenado según start_time)
```

---

## División en 3 prompts (para agente nuevo)

Marca cada ítem en este archivo y en `planning/plan_trabajo.md` al completarlo.

---

### Prompt 1 — Núcleo exacto + enrutado (n ≤ 12)

**Objetivo:** unificar el flujo para instancias pequeñas sin flags.

- [x] Implementar `resolve_solver_mode()` en `src/solver/llm_assisted.py`
- [x] Implementar `solve()` que enruta a `solve_with_llm_reorder` si `n ≤ 12`
- [x] Implementar `solve_baseline()` con el mismo enrutado (reorder exacto / temporal)
- [x] Actualizar `run_example.py`: `--llm` → `solve()`; sin LLM → `solve_baseline()`
- [x] Tests en `src/test_bench_instances.py`:
  - [x] `bench_disordered.json` resuelto con `solve()` mock → `[1, 4, 3, 0]` sin flags
  - [x] `bench_irrelevant_middle.json` con `solve()` mock → resultado coherente (índices crecientes OK)
- [x] Marcar ítems completados en `planning/plan_trabajo.md` (sección Task E, Prompt 1)

**Verificación:**

```bash
python src/test_bench_instances.py
python src/run_example.py bench_disordered.json --llm   # tras configurar .env
```

---

### Prompt 2 — Heurística para n > 12 + experimentos

**Objetivo:** que videos grandes también reordenen sin colgar.

- [x] Implementar en `src/solver/reorder.py`:
  - [x] `select_subset_greedy()` o knapsack sin orden (relevancia/duración)
  - [x] `order_subset_greedy()` — inserción greedy o 2-opt sobre matriz de coherencia
  - [x] `solve_with_llm_heuristic_reorder()` en `llm_assisted.py`
  - [x] `solve_baseline_heuristic_reorder()` (proxy temporal)
- [x] Completar `solve()` / `solve_baseline()`: rama `n > 12` → heurística
- [x] Actualizar `run_experiments.py`: `llm_dynamic` y `baseline` usan funciones unificadas
- [x] Test mock con instancia sintética de n=15 (generar `data/instances/bench_large_disordered.json` o inline en test)
- [x] Marcar ítems en `plan_trabajo.md` (Prompt 2)

**Verificación:**

```bash
python src/test_bench_instances.py
python src/run_experiments.py --instances mini_video_1.json --llm --evaluate --output results/part08_unified.csv
```

---

### Prompt 3 — Documentación, plan y cierre

**Objetivo:** que el comportamiento quede claro para el informe y la entrega.

- [x] Actualizar `README.md`: flujo normal sin `--reorder`; tabla exact vs heurístico
- [x] Actualizar `planning/plan_trabajo.md`: Task E completo; Día 4 enrutado automático
- [x] Añadir nota en `planning/walkthroughC.md` o nuevo `walkthroughE.md` con decisión de diseño
- [x] Ejecutar Bloque 6b (`bench_disordered`) con solver unificado
- [x] Marcar Task E como `[x]` en `plan_trabajo.md`
- [x] Dejar anotado en informe (sección limitaciones): exacto O(2ⁿ) vs heurístico para n > 12

**Verificación final:**

```bash
python src/test_bench_instances.py
python src/test_llm_solver.py
python src/run_example.py bench_disordered.json --llm
python src/run_example.py bench_irrelevant_middle.json --llm
```

---

## Criterios de aceptación (Task E completo)

1. El usuario ejecuta `python src/run_example.py CUALQUIER.json --llm` y **no necesita saber** si el input está ordenado.
2. `bench_disordered.json` → orden narrativo correcto automáticamente.
3. `bench_irrelevant_middle.json` → misma calidad que antes (subsecuencia = orden cronológico).
4. `mini_video_*.json` (n=10) → reorder exacto.
5. `video_*.json` (n>12) → reorder heurístico, termina en tiempo razonable.
6. Los flags `--reorder` / solvers legacy siguen disponibles para comparación en experimentos.

---

## Referencias de código existente

| Archivo | Qué reutilizar |
|---|---|
| `src/solver/reorder.py` | `unordered_knapsack_dp_with_coherence`, `solve_baseline_reorder` |
| `src/solver/llm_assisted.py` | `solve_with_llm_reorder`, `compute_relevance_with_llm` |
| `src/problem.py` | `validate_order()`, `is_valid_ordered_selection()` |
| `src/test_bench_instances.py` | Tests mock existentes para disordered |
