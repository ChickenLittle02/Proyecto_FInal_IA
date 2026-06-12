# F5 — Registro de ejecución por bloques

Actualizado: 2026-06-12. Política: solo `baseline_beam` + `llm_beam`. Proveedor: Groq (`llama-3.3-70b-versatile`).

Ritmo observado: **~1,7 s/llamada** (suite lite + Bloque 1). Fórmula API fría por instancia: `n + n×(n−1) + 3` (precálculo + juez macro top-M=3).

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

## Bloques pendientes

### Bloque 2 — Escalado `dur_10min` ⏳

| Campo | Valor |
|-------|-------|
| Comando | `python src/run_experiments.py --instances dur_10min.json --llm --evaluate --output results/part_dur_10min.csv --notes informe/notas_experimentos.md --block-label "F5 Bloque 2 — escalado dur_10min"` |
| API | Sí |
| Llamadas est. | **~532** |
| Duración est. | **~15 min** |
| Post-ejecución | Fusionar filas en `results/unified_scaling.csv` (manual o script) |

### Bloque 3 — Escalado `dur_15min` ⏳ (puede requerir 2 tramos)

| Campo | Valor |
|-------|-------|
| Comando | `--instances dur_15min.json` (mismos flags) |
| API | Sí |
| Llamadas est. | **~1159** |
| Duración est. | **~33 min** → dividir en 3b + 3c si rate limit |
| Nota | Reanudar mismo comando; caché continúa |

### Bloque 4 — Escalado `dur_20min` ⏳

| Campo | Valor |
|-------|-------|
| Llamadas est. | **~2212** |
| Duración est. | **~63 min** (4 tramos de ~15 min) |

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

## Cuota Groq (snapshot 2026-06-12, tras Bloque 1)

Consulta con una llamada mínima (ver README o script abajo):

| Header | Valor observado |
|--------|-----------------|
| `x-ratelimit-limit-requests` | 1000 |
| `x-ratelimit-remaining-requests` | **790** |
| `x-ratelimit-reset-requests` | ~5 h |
| `x-ratelimit-limit-tokens` | 12000 |
| `x-ratelimit-remaining-tokens` | ~11955 |

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
