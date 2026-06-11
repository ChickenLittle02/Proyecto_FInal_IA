# Walkthrough — Paso C Completado: Coherencia Dinámica en el DP

Hemos completado el **Paso C** del plan de trabajo: refinar el solver asistido por LLM para evaluar coherencia entre el **último fragmento elegido** y el candidato actual, en lugar de mezclar solo pares consecutivos `(i, i+1)` en scores estáticos.

## Problema resuelto

En el Paso B, `solve_with_llm` precomputaba coherencia solo entre pares consecutivos del video original y la sumaba al score de cada fragmento **antes** del DP. Si el solver omitía fragmentos (p. ej. seleccionaba `[0, 2, 4]`), la coherencia relevante era `(0→2)` y `(2→4)`, no `(0→1)`.

`SelectionProblem.objective_score` ya evaluaba pares consecutivos de la selección final, pero el solver no usaba esa lógica al decidir qué incluir.

## Diseño

| Componente | Decisión |
|---|---|
| Relevancia | Precomputar una vez por fragmento (`compute_relevance_with_llm`). |
| Coherencia | Bajo demanda vía `LLMClient.score_coherence(i, j)` con `i < j`; memo en memoria + caché en disco (`.llm_cache.json`). |
| DP | Nuevo `ordered_knapsack_dp_with_coherence` con estado `(index, remaining, last_selected)`; `last_selected = -1` si no hay ninguno. |
| Baseline | `ordered_knapsack_dp` en `baseline.py` **sin cambios**. |
| Compatibilidad | `solve_with_llm_static` conserva el enfoque del Paso B para pruebas y comparación. |

### Transición en el DP

Al tomar el fragmento `j`:

```
score += relevancia[j]
if last_selected >= 0:
    score += peso × coherencia(last_selected, j)
last_selected = j
```

## Cambios realizados

1. **`src/solver/llm_assisted.py`**
   - `compute_relevance_with_llm`: solo relevancia por fragmento.
   - `ordered_knapsack_dp_with_coherence`: DP con estado `(index, remaining, last_selected)`.
   - `solve_with_llm`: relevancia precomputada + coherencia bajo demanda con memo `(i, j)`.
   - `solve_with_llm_static`: enfoque anterior (Paso B) para comparación.

2. **`src/test_llm_solver.py`**
   - Mock de `LLMClient` sin API.
   - Demuestra que con saltos de fragmentos el estático elige `[0, 1]` y el dinámico `[0, 2]`.

3. **`planning/plan_trabajo.md`** y **`planning/taskC.md`** actualizados.

## Validación

### Prueba con mock (sin API)

```bash
python src/test_llm_solver.py
```

**Resultado:**
- Enfoque estático: índices `[0, 1]`, score `10.3250`
- Enfoque dinámico: índices `[0, 2]`, score `10.2375`
- `[ÉXITO]` Selecciones distintas cuando hay saltos.

### Solver clásico intacto

```bash
python src/run_example.py
```

**Resultado:** selecciona `[0, 1, 2, 3, 4]`, duración 45.0 s, score 5.0 (sin cambios).

### Solver LLM end-to-end

```bash
python src/run_example.py --llm
```

**Resultado sobre `example_instance.json` (5 fragmentos, límite 45 s):**
- **Fragmentos seleccionados:** índices `[0, 1, 2, 4]` (omite el 4.º fragmento, índice 3).
- **Duración total:** 38.0 s.
- **Puntuación total (DP dinámico):** 2.55 (antes, en Paso B con enfoque estático: 2.4).

La selección coincide con la del Paso B en esta instancia, pero el score refleja coherencia real `(2→4)` al saltar el fragmento 3, no la coherencia `(2→3)` precomputada estáticamente.

## Criterios de aceptación

- [x] Coherencia real `(último_elegido → candidato)` dentro del DP.
- [x] Prueba unitaria con mock demuestra diferencia estático vs dinámico.
- [x] `python src/run_example.py --llm` funciona.
- [x] Solver clásico sin `--llm` intacto.

## Siguiente paso → Paso D

1. Crear `src/run_experiments.py` para comparar baseline vs LLM en `video_*.json`.
2. Recoger métricas (longitud, cobertura, coherencia) y guardarlas en CSV.
