# Checklist de Tareas — Paso C: Refinar el Solver Asistido por LLM

## Problema a resolver
Hoy `solve_with_llm` precomputa coherencia solo entre pares consecutivos `(i, i+1)` y la mezcla en un score estático por fragmento **antes** del DP. Si el solver omite fragmentos (p. ej. selecciona 0 y luego 2), la coherencia real del resumen es `(0 → 2)`, no `(0 → 1)`.

## Tareas

- `[x]` Implementar DP con coherencia dinámica: estado `(índice, duración restante, último_seleccionado)` donde al tomar el fragmento `j` se suma `relevancia[j] + peso × coherencia(último, j)`.
- `[x]` Refactorizar `src/solver/llm_assisted.py`:
  - `[x]` Precomputar solo relevancia por fragmento.
  - `[x]` Obtener coherencia `(i, j)` bajo demanda vía `LLMClient.score_coherence` (aprovechar caché en `.llm_cache.json`).
  - `[x]` Memoizar pares `(i, j)` en memoria durante la ejecución del DP.
- `[x]` Mantener `ordered_knapsack_dp` en `baseline.py` sin cambios (solver clásico intacto).
- `[x]` Añadir prueba sin API (mock de `LLMClient`) que demuestre diferencia entre enfoque estático y dinámico cuando hay saltos.
- `[x]` Validar con `python src/run_example.py --llm` sobre `example_instance.json` y comparar selección vs. versión anterior.
- `[x]` Actualizar `planning/walkthroughC.md` con cambios, decisión de diseño y resultado de validación.
