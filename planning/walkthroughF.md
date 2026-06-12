# Walkthrough Fase 2 — Pipeline beam search unificado

Registro de cambios del refactor arquitectónico (F1–F6). Actualizado: 2026-06-12.

## Objetivo

Un **solo pipeline** ejecutable: precálculo LLM cacheado → beam search top-M → juez macro del resumen.

Variantes permitidas: `baseline_beam` y `llm_beam`. Nada más como algoritmo de producción.

---

## F1 — Beam search + score matrix ✅

**Estado:** completado.

### Archivos creados

| Archivo | Rol |
|---|---|
| `src/llm/scoring.py` | `ScoreMatrix`, `build_llm_scores()`, `build_baseline_scores()`, matriz n×n cacheada |
| `src/solver/unified.py` | `beam_search_select_and_order()`, `unified_solve()` |
| `src/test_unified.py` | Regresión mock: bench_disordered, irrelevant_middle, n=15 |

### Comportamiento

- El LLM puntúa **todos** los fragmentos y **todos** los pares dirigidos antes del beam search.
- El beam search **no** llama a la API; score local = Σ relevancia + w·Σ coherencia consecutiva.
- `beam_width` default = 10.

### Validación

```bash
python src/test_unified.py
```

---

## F2 — Redirigir `solve()` + limpieza legacy ✅

**Estado:** completado.

### Cambios en producción

| Antes (Task E) | Después (Fase 2) |
|---|---|
| `solve()` → DP bitmask (n≤12) o heurística 2 fases (n>12) | `solve()` → `build_llm_scores()` + `unified_solve()` |
| `solve_baseline()` → mismo enrutado | `solve_baseline()` → `build_baseline_scores()` + `unified_solve()` |
| Modos `exact_reorder` / `heuristic_reorder` | Modos `llm_beam` / `baseline_beam` |
| `src/solver/baseline.py`, `reorder.py` | Movidos a `tests/legacy/` |

### Archivos modificados

- `src/solver/llm_assisted.py` — thin wrapper (~60 líneas)
- `src/test_bench_instances.py` — solo tests beam vía `solve()`
- `src/test_llm_solver.py` — prueba beam con mock
- `src/run_experiments.py` — solo `baseline_beam` + `llm_beam`; eliminados `--static`, `--reorder`
- `src/run_lite_suite.py` — sin flag `--static`

### Validación

```bash
python src/test_bench_instances.py
python src/test_llm_solver.py
python src/run_example.py
python src/run_example.py bench_disordered.json --llm   # requiere .env
```

Tests legacy (referencia Task E, no producción):

```bash
python tests/legacy/test_legacy_solvers.py
```

---

## F3 — Evaluación macro del resumen ✅

**Estado:** completado (2026-06-12).

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `src/llm/prompts.py` | `summary_evaluation_prompt(summary_text, max_duration)` — pide JSON con `relevance`, `coherence`, `overall` |
| `src/llm/client.py` | `SummaryEvaluation` (dataclass), `evaluate_summary()`, `_parse_summary_evaluation()` con fallback JSON → tres números → escalar |
| `src/test_llm.py` | `test_parse_summary_evaluation()` sin API; bloque API con resumen ficticio + caché |

### Comportamiento

- El juez macro recibe el texto concatenado del resumen (mismo formato que `SelectionProblem.summary_text()`).
- Respuesta esperada: JSON `{"relevance": …, "coherence": …, "overall": …}`; parseo tolerante a texto extra o tres números sueltos.
- Usa la misma caché `.llm_cache.json` que los prompts micro (`_model_call`).
- Integrado en `solve()` vía F4 (`refine_with_summary_judge`, top-M=3).

### Validación

```bash
# Sin API (~instantáneo): parseo de respuestas macro
python -c "import sys; sys.path.insert(0,'.'); from src.test_llm import test_parse_summary_evaluation; test_parse_summary_evaluation(); print('OK')"

# Con API (~10–20 s): fragmento + resumen ficticio + caché
python src/test_llm.py
```

---

## F4 — Refinamiento top-M ✅

**Estado:** completado (2026-06-12).

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `src/solver/unified.py` | `beam_search_select_and_order(..., top_m=1)` devuelve `List[BeamCandidate]` |
| `src/solver/llm_assisted.py` | `refine_with_summary_judge()`, integración en `solve()` con `summary_refine_top_m=3` |
| `src/run_experiments.py` | CSV: `summary_llm_score`, `summary_llm_relevance`, `summary_llm_coherence`; flag `--summary-refine-top-m` |
| `src/run_example.py` | Muestra evaluación macro; flag `--summary-refine-top-m` |
| `src/test_llm_solver.py` | Mock `evaluate_summary()` + test juez macro vs score local |
| `src/test_unified.py` | Test top-M candidatos distintos |
| `src/experiments/metrics.py` | Fix import `build_relevance_scores` (eliminado `compute_relevance_with_llm`) |

### Comportamiento

- `solve()` obtiene hasta **M=3** candidatos del beam (score local) y elige el de mayor `overall` vía `evaluate_summary()`.
- `solve_baseline()` no usa juez macro (sin LLM).
- `--summary-refine-top-m 0` desactiva el refinamiento (solo mejor candidato local).
- Métricas macro en CSV solo para filas `llm_beam`.

### Validación

```bash
python src/test_unified.py
python src/test_bench_instances.py
python src/test_llm_solver.py
```

---

## F5 — Experimentos + CSV ⏳

**Estado:** en curso (2026-06-12). Registro detallado: `planning/f5_bloques_ejecucion.md`.

### Bloque 0 ✅

- `prepare_mini_instances.py`: `--target-minutes`, `--source-video`
- `run_experiments.py`: `--beam-width`
- Tests mock OK; generados `dur_5min.json` … `dur_20min.json` (n=12/23/34/47)

### Bloque 1 ✅

- `results/unified_scaling.csv`: 2 filas (`dur_5min`, baseline_beam + llm_beam)
- Caché: 192 → 339 entradas (+147 llamadas Groq, ~6,3 min)
- Notas: bloque «F5 Bloque 1 — escalado dur_5min» en `informe/notas_experimentos.md`

### Pendiente

- Bloques 2–4: escalado `dur_10/15/20min`
- Bloque 5: verificación caché (E2)
- Bloque 6: ablation `beam_width` ∈ {3, 5, 10}
- Reescribir `execute.md` con un solo flujo beam

---

## F6 — Informe + README ⏳

**Estado:** pendiente (README parcialmente actualizado en F2).

### Entregables previstos

- Informe §2–4: solo beam search como algoritmo entregado
- Solvers legacy mencionados solo en «trabajo previo» o eliminados del informe final

---

## Política de código (recordatorio)

| Permitido | Prohibido en producción |
|---|---|
| `baseline_beam`, `llm_beam` | DP, greedy, heurística 2 fases, `--static`, `--reorder` |
| Precálculo cacheado + juez macro (F3–F4) | Llamadas LLM dentro del bucle beam |
| `tests/legacy/` para referencia Task E | Import de legacy desde `src/` |
