# Walkthrough — Paso C Completado: Coherencia Dinámica en el DP

Hemos completado el **Paso C** del plan de trabajo: refinar el solver asistido por LLM para evaluar coherencia entre el **último fragmento elegido** y el candidato actual, en lugar de mezclar solo pares consecutivos `(i, i+1)` en scores estáticos.

## Qué es el DP en este proyecto

**DP** (programación dinámica) es el componente algorítmico central del Tema 2: resuelve de forma **exacta** qué fragmentos incluir en el resumen respetando el orden cronológico del video y un límite de duración.

### Problema que modela

Dado un video segmentado en fragmentos ordenados `s_0, s_1, …, s_{n-1}`, cada uno con duración `l_i` y una puntuación de relevancia `r_i`, hay que elegir un subconjunto **ordenado** (sin reordenar) tal que:

- la suma de duraciones ≤ `max_duration` (restricción tipo mochila);
- se maximice el valor total (relevancia, y en la variante LLM también coherencia entre transiciones reales).

Es una variante de **knapsack 0/1 con orden fijo**: no se puede permutar fragmentos; solo decidir, para cada posición, **incluir** o **omitir**.

### Cómo funciona el DP baseline

Implementación: `ordered_knapsack_dp` en `src/solver/baseline.py`.

**Estado:** `(index, remaining)` — fragmento actual en el recorrido y segundos aún disponibles.

**Transiciones** (de derecha a izquierda en el índice, típico en knapsack):

1. **Omitir** fragmento `index`: continuar con `(index + 1, remaining)`.
2. **Incluir** fragmento `index` (si `l_index ≤ remaining`): sumar `r_index` y continuar con `(index + 1, remaining - l_index)`.

**Caso base:** `index == n` → valor 0, selección vacía.

**Resultado:** la selección óptima y su score. Se usa memoización (`@lru_cache`) para no recomputar subproblemas.

En el baseline del Paso D, `r_i = 1.0` para todos los fragmentos: el objetivo es **maximizar cantidad** de fragmentos (equivalente a relevancia uniforme).

### Cómo funciona el DP con coherencia dinámica (LLM)

Implementación: `ordered_knapsack_dp_with_coherence` en `src/solver/llm_assisted.py`.

**Estado ampliado:** `(index, remaining, last_selected)` donde `last_selected = -1` si aún no se ha elegido ningún fragmento.

Al **incluir** el fragmento `j`:

```
score += relevancia[j]
if last_selected >= 0:
    score += peso × coherencia(last_selected, j)   # LLM evalúa el par real
last_selected = j
```

La coherencia se consulta al LLM **solo para pares que el DP está considerando** (memo en memoria + caché `.llm_cache.json`), no solo entre vecinos `(i, i+1)` del video original.

### Cómo se utiliza en el flujo del sistema

| Punto de entrada | Función | Rol del DP |
|---|---|---|
| `python src/run_example.py` | `ordered_knapsack_dp` | Solver clásico sin API |
| `python src/run_example.py --llm` | `ordered_knapsack_dp_with_coherence` vía `solve_with_llm` | Selección óptima con scores LLM |
| `python src/run_experiments.py --llm` | Igual + `--static` usa `ordered_knapsack_dp` con scores precalculados | Comparación experimental |
| `src/test_llm_solver.py` | Mock de LLM | Demuestra diferencia estático vs dinámico sin API |

**Papel del LLM vs DP:** el LLM **no elige** fragmentos; **puntúa** relevancia y coherencia. El DP **decide** la selección óptima con esas puntuaciones. La evaluación post-hoc (`--evaluate` en Paso D) vuelve a puntuar la selección final con el mismo LLM para comparar baseline y LLM de forma justa.

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

Ver `planning/walkthroughD.md` y `planning/taskD.md`.
