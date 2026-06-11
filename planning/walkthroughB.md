# Walkthrough — Paso B Completado: Cliente LLM Real (Gemini)

Hemos completado el **Paso B** del plan de trabajo: conectar el sistema a la API real de **Google Gemini** para evaluar relevancia y coherencia de fragmentos, con caché local y prueba end-to-end del solver asistido por LLM.

## Cambios Realizados

1. **Configuración reproducible del entorno:**
   - `.gitignore` ignora `.env` y `.llm_cache.json`.
   - Nuevo `.env.example` con plantilla sin claves reales.
   - Dependencias en `requirements.txt`: `google-generativeai`, `python-dotenv`.
   - Modelo por defecto actualizado a **`gemini-2.5-flash`** (los modelos `gemini-1.5-flash` y `gemini-2.0-flash` devolvían 404 o cuota agotada en el tier gratuito).

2. **Cliente LLM real (`src/llm/client.py`):**
   - Carga variables desde `.env` con `python-dotenv`.
   - Llama a Gemini vía `google.generativeai`.
   - Parseo robusto de puntuaciones con regex (`_parse_score`).
   - Reintentos automáticos ante error **429** (rate limit del plan gratuito).
   - Caché en disco (`.llm_cache.json`) para no repetir llamadas idénticas.

3. **Script de prueba (`src/test_llm.py`):**
   - Verifica detección de API key, llamada real y uso del caché.

4. **Integración end-to-end (`src/run_example.py`):**
   - Nuevo flag `--llm` para ejecutar `solve_with_llm` sobre cualquier instancia JSON.

## Configuración

Copiar la plantilla y añadir la clave real:

```bash
cp .env.example .env
# Editar .env y pegar tu GEMINI_API_KEY de Google AI Studio
```

Contenido de `.env.example`:

```env
GEMINI_API_KEY=tu_clave_aqui
LLM_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini
```

## Validación de la API y Caché

Tras borrar el caché y ejecutar la prueba:

```bash
del .llm_cache.json   # Windows
python src/test_llm.py
```

**Resultado obtenido:**
- **Primera llamada (API real):** score `0.95`, ~12 s de respuesta.
- **Segunda llamada (caché):** score `0.95`, ~0.02 ms.

> **Nota:** El SDK `google.generativeai` está deprecado (aviso en consola). Funciona correctamente; migrar a `google.genai` puede hacerse más adelante si hace falta.

## Validación del Solver LLM (instancia pequeña)

```bash
python src/run_example.py --llm
```

**Resultado sobre `example_instance.json` (5 fragmentos, límite 45 s):**
- **Fragmentos seleccionados:** índices `[0, 1, 2, 4]` (4 de 5).
- **Duración total:** 38.0 s (dentro del límite).
- **Puntuación total combinada:** 2.4.

Fragmentos elegidos por el solver asistido por LLM:
1. Introducción a la selección de fragmentos...
2. Definición del problema formal...
3. Cómo evaluar relevancia de cada fragmento...
5. Conclusión y cierre con recomendaciones...

> En el plan gratuito, Gemini limita a **5 peticiones/minuto** por modelo. Las ejecuciones con muchos fragmentos pueden tardar por los reintentos automáticos; la caché acelera mucho las repeticiones.

---

## Paso C — Qué hay que hacer (Refinar solver LLM)

### Limitación actual

En `src/solver/llm_assisted.py`, `solve_with_llm` hace esto:

1. Pide al LLM relevancia de cada fragmento.
2. Pide coherencia solo entre pares **consecutivos** en el video original: `(0,1), (1,2), …`.
3. Combina todo en un score fijo por fragmento: `relevancia[i] + peso × coherencia(i, i+1)`.
4. Pasa esos scores al DP clásico (`ordered_knapsack_dp`).

**Problema:** si el DP elige fragmentos `[0, 2, 4]` (saltando el 1 y el 3), la coherencia que importa es `(0→2)` y `(2→4)`, no `(0→1)` ni `(2→3)`.

`SelectionProblem.objective_score` en `src/problem.py` **sí** evalúa coherencia entre pares consecutivos **de la selección final**, pero el solver no usa esa lógica al decidir qué incluir.

### Objetivo del Paso C

Integrar la coherencia **dentro del DP**, evaluando la transición real entre el último fragmento elegido y el candidato actual.

### Enfoque recomendado

| Componente | Acción |
|---|---|
| Relevancia | Precomputar una vez por fragmento (como ahora). |
| Coherencia | Calcular bajo demanda `coherencia(i, j)` con `i < j` vía `LLMClient.score_coherence`; memoizar en memoria + caché en disco. |
| DP | Nuevo solver (p. ej. `ordered_knapsack_dp_with_coherence`) con estado `(index, remaining, last_selected)`; `last_selected = -1` si aún no hay ninguno. |
| Baseline | No tocar `src/solver/baseline.py` — el solver clásico sigue igual. |

### Archivos a tocar

- `src/solver/llm_assisted.py` — refactor principal.
- `src/solver/baseline.py` — solo si se extrae utilidad compartida (opcional).
- `src/test_llm_solver.py` o similar — prueba con mock, sin llamadas API.
- `planning/walkthroughC.md` — documentar al cerrar C.

### Criterios de aceptación

- [ ] Al omitir fragmentos intermedios, el score del DP usa coherencia `(último_elegido → candidato)`.
- [ ] Prueba unitaria con mock demuestra selección distinta (o score distinto) vs. enfoque estático en un caso con salto.
- [ ] `python src/run_example.py --llm` sigue funcionando.
- [ ] No se rompe el solver clásico (`python src/run_example.py` sin `--llm`).

### Después del Paso C → Paso D

1. Crear `src/run_experiments.py` para comparar baseline vs LLM en `video_*.json`.
2. Recoger métricas (longitud, cobertura, coherencia) y guardarlas en CSV.
