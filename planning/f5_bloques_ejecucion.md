# F5 — Registro de ejecución por bloques

Actualizado: 2026-06-12. Política: solo `baseline_beam` + `llm_beam`. Proveedor: Groq (`llama-3.3-70b-versatile`).

Ritmo observado (n pequeño, n≤12): **~1,7 s/llamada API neta** (suite lite + Bloque 1).  
Para n≥23 el tiempo **real de pared** es mucho mayor — ver § «Por qué las estimaciones de ~15 min fallan» y el reporte del Bloque 2 interrumpido.

Fórmula API fría por instancia: `n + n×(n−1) + 3` (precálculo + juez macro top-M=3).  
Con caché caliente desde `dur_5min`: relevancia +11, coherencia +374, juez +3 → **~388 llamadas nuevas** (no 532).

---

## Bloque 0 — Preparación local ✅ (2026-06-12)

| Paso | Comando / cambio | API | Resultado |
|------|------------------|-----|-----------|
| Código | `prepare_mini_instances.py` → `--target-minutes`, `--source-video` | 0 | OK |
| Código | `run_experiments.py` → `--beam-width` | 0 | OK |
| Tests mock | `python src/test_unified.py` | 0 | OK |
| Tests mock | `python src/test_bench_instances.py` | 0 | OK |
| Instancias | `python src/prepare_mini_instances.py --target-minutes 5 10 15 20 --source-video 2` | 0 | 4 JSON generados |

**Instancias `dur_*` (video_2.json):**

| Archivo | n | Duración acum. | max_duration (25 %) |
|---------|---|----------------|---------------------|
| `dur_5min.json` | 12 | 317 s (~5,3 min) | 79,24 s |
| `dur_10min.json` | 23 | 612 s (~10,2 min) | 152,94 s |
| `dur_15min.json` | 34 | 902 s (~15 min) | 225,51 s |
| `dur_20min.json` | 47 | 1226 s (~20,4 min) | 306,40 s |

**Tiempo total Bloque 0:** ~20 s (tests) + ~1 s (generación).

---

## Bloque 1 — Escalado `dur_5min` ✅ (2026-06-12)

**Plan de ejecución**

| Campo | Valor |
|-------|-------|
| Comando | `python src/run_experiments.py --instances dur_5min.json --llm --evaluate --output results/unified_scaling.csv --notes informe/notas_experimentos.md --block-label "F5 Bloque 1 — escalado dur_5min"` |
| API | Sí (Groq) |
| Llamadas nuevas | **147** (caché 192→339) |
| Duración real | **~6,3 min** (380 s) |
| Criterio de éxito | 2 filas en CSV | ✅ |

**Resultados (`results/unified_scaling.csv`):**

| solver | selección | duration_used | solver_score | objective_score | summary_llm_* |
|--------|-----------|---------------|--------------|-----------------|---------------|
| baseline_beam | [7,8,9] | 76,16 | 3,21 | 2,23 | — |
| llm_beam | [8,9,10] | 78,44 | 2,85 | 2,25 | 0,75 / 0,8 / 0,7 |

**Observación:** baseline y LLM eligen ventanas contiguas distintas; ambos usan ~96–99 % del `max_duration`.

---

## Bloque 2 — Escalado `dur_10min` ⚠️ INTERRUMPIDO (2026-06-12)

### Reporte de ejecución

| Campo | Valor |
|-------|-------|
| Comando | `python src/run_experiments.py --instances dur_10min.json --llm --evaluate --output results/part_dur_10min.csv --notes informe/notas_experimentos.md --block-label "F5 Bloque 2 — escalado dur_10min"` |
| Inicio | 2026-06-12 ~19:38 UTC |
| Detención | Manual por el usuario tras **~50 min** sin CSV ni salida visible |
| Caché antes | **339** entradas |
| Caché al parar | **524** entradas (**+185** llamadas API nuevas) |
| `results/part_dur_10min.csv` | **No generado** (el script solo escribe CSV al final) |
| `results/unified_scaling.csv` | Sin cambios (solo `dur_5min`, 2 filas) |
| `informe/notas_experimentos.md` | Sin sección Bloque 2 (append solo al completar) |
| Cuota Groq al inicio | **793** solicitudes restantes / 1000 |

### Hasta dónde llegó (orden real del script)

`run_experiments.py` ejecuta las fases en este orden para `--llm --evaluate`:

| Fase | Descripción | API nuevas est. | Estado |
|------|-------------|-----------------|--------|
| 1 | Precalcular relevancia (evaluación post-hoc) | 11 (fragm. 12–22; 0–11 en caché de Bloque 1) | ✅ Completada |
| 2 | `baseline_beam` (beam sin LLM) | 0 | ✅ Completada |
| 3 | Evaluar selección baseline (pares coherencia) | ~2 | ✅ Completada |
| 4 | `llm_beam` → `build_llm_scores` → matriz coherencia 23×23 | 374 nuevos (132 ya en caché) | **~46 %** (~172/374 pares) |
| 5 | Juez macro top-M=3 | 3 | ❌ No iniciado |
| 6 | Evaluación post-hoc de `llm_beam` | 0 (reutiliza caché) | ❌ No iniciado |
| 7 | Escribir CSV + notas | 0 | ❌ No iniciado |

**Progreso global del bloque:** ~**47 %** de las ~390 llamadas nuevas estimadas.  
**Faltan ~205 llamadas** (~55–70 min adicionales al ritmo observado en esta corrida).

### Por qué la estimación original (~15 min) fue optimista

La cifra de ~15 min venía de `532 llamadas × 1,7 s ≈ 15 min`, medida en instancias **n≤12**. En la práctica, con n=23 y caché parcial, la pared fue **~16 s/llamada efectiva** (50 min / 185 llamadas). Causas:

1. **Delay de cortesía Groq:** `LLMClient._courtesy_delay()` añade **2,1 s** antes de *cada* llamada no cacheada (`src/llm/client.py`). La métrica de 1,7 s midió sobre todo latencia de red + respuesta, no el sleep fijo.
2. **Matriz O(n²):** n=23 implica **506 pares** de coherencia; aunque 132 vienen de `dur_5min`, quedan **374 llamadas nuevas** solo en precálculo LLM.
3. **Caché en disco costosa:** cada respuesta nueva reescribe **todo** `.llm_cache.json` con `indent=2` (`src/llm/cache.py`). Con ~500 KB y creciendo, el I/O por llamada se degrada.
4. **Rate limit Groq:** ante HTTP 429 el cliente espera **35 s** y reintenta (hasta 3 veces). Ráfagas largas pueden disparar pausas invisibles en consola.
5. **Salida sin flush:** el progreso (`relevancia: fragmento i/n`, `coherencia: par (i,j)`) no apareció en la terminal del agente; parecía colgado aunque la caché crecía.
6. **Estimación en frío vs caliente:** se comunicó ~532 llamadas (caché vacía); con Bloque 1 hecho son ~388 nuevas, pero el tiempo **no** escala linealmente con ese número por los puntos anteriores.

### Duración revisada (Bloque 2)

| Escenario | Llamadas nuevas | Tiempo de pared estimado |
|-----------|-----------------|--------------------------|
| Caché vacía (n=23) | ~532 | **~70–90 min** |
| Tras Bloque 1 (reanudar ahora) | ~205 restantes | **~55–70 min** |
| Ritmo ideal teórico (1,7 s/call) | — | ~15 min *(no alcanzable con delay 2,1 s + I/O caché)* |

### Reanudación

Repetir **el mismo comando**. La caché continúa (524 entradas); no borrar `.llm_cache.json`.

```powershell
python src/run_experiments.py --instances dur_10min.json --llm --evaluate `
  --output results/part_dur_10min.csv `
  --notes informe/notas_experimentos.md `
  --block-label "F5 Bloque 2 — escalado dur_10min"
```

Al terminar, fusionar las 2 filas de `part_dur_10min.csv` en `results/unified_scaling.csv`.

> **Nota:** Si quedó un `python.exe` huérfano del intento anterior, cerrarlo antes de reanudar (`Stop-Process -Id <PID>`).

---

## Bloques pendientes

### Bloque 2 — Escalado `dur_10min` ⏳ (reanudar)

| Campo | Valor |
|-------|-------|
| Comando | (ver § Reanudación arriba) |
| API | Sí (~205 llamadas restantes) |
| Duración est. | **~55–70 min** (revisada tras intento 2026-06-12) |
| Post-ejecución | Fusionar filas en `results/unified_scaling.csv` |

### Bloque 3 — Escalado `dur_15min` ⏳ (dividir en tramos)

| Campo | Valor |
|-------|-------|
| Comando | `--instances dur_15min.json` (mismos flags) |
| API | Sí |
| Llamadas est. | **~1159** (frío) / menos con caché acumulada |
| Duración est. | **~2–3 h** (revisada; no confiar en ~33 min) |
| Nota | Reanudar mismo comando; caché continúa; pausar si rate limit |

### Bloque 4 — Escalado `dur_20min` ⏳

| Campo | Valor |
|-------|-------|
| Llamadas est. | **~2212** (frío) |
| Duración est. | **~4–6 h** (revisada; planificar varios tramos) |

### Bloque 5 — Verificación caché (E2) ⏳

| Campo | Valor |
|-------|-------|
| Comando | Repetir escalado completo o `--instances dur_5min.json` solo |
| API | **~0** (caché completa) |
| Duración est. | **~2–5 min** |

### Bloque 6 — Ablation `beam_width` ⏳

| Instancia | beam_width | API est. | Duración |
|-----------|------------|----------|----------|
| `bench_disordered.json` | 3, 5, 10 | ~9 (solo juez macro) | ~1 min |
| `dur_10min.json` | 3, 5, 10 | ~9 | ~1 min |

Comando ejemplo:

```powershell
python src/run_experiments.py --instances bench_disordered.json --llm --evaluate --beam-width 5 --output results/ablation_bw5.csv
```

### Bloque 7 — Documentación F5/F6 ⏳

- Reescribir `execute.md` (solo beam)
- Actualizar `informe/notas_experimentos.md` resumen final
- F6: `informe_tecnico.tex` §2–4, README

---

## Cuota Groq

Consulta con una llamada mínima:

```powershell
python -c "
import os; from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
c = OpenAI(api_key=os.getenv('OPENAI_API_KEY') or os.getenv('GROQ_API_KEY'),
           base_url=os.getenv('OPENAI_BASE_URL','https://api.groq.com/openai/v1'))
r = c.chat.completions.with_raw_response.create(
    model=os.getenv('LLM_MODEL','llama-3.3-70b-versatile'),
    messages=[{'role':'user','content':'0.5'}], max_tokens=5, temperature=0)
for k,v in r.headers.items():
    if 'ratelimit' in k.lower(): print(f'{k}: {v}')
"
```

| Momento | `remaining-requests` | Notas |
|---------|------------------------|-------|
| Tras Bloque 1 | **790** | snapshot inicial |
| Inicio Bloque 2 (2026-06-12) | **793** | +3 por checks previos; cuota suficiente |
| Tras Bloque 2 interrumpido (+185 calls) | ~**608** (est.) | sin verificar en panel |

Panel web: [console.groq.com/settings/limits](https://console.groq.com/settings/limits)

---

## Datos ya disponibles para el informe (sin más API)

| Fuente | Uso en informe |
|--------|----------------|
| `results/experiments_bench_beam.csv` | §7.2 bench sintéticos (lite) |
| `results/unified_scaling.csv` | §7.3 escalado (parcial: dur_5min) |
| `informe/notas_experimentos.md` | Observaciones cualitativas |
| `planning/walkthroughF.md` | Arquitectura Fase 2 |
| `data/instances/dur_*.json` | §6.1 dataset por duración |
