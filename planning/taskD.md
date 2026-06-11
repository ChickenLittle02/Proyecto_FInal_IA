# Checklist de Tareas — Paso D: Experimentos y Análisis

## Objetivo
Comparar de forma sistemática el solver clásico (baseline) frente al asistido por LLM, recoger métricas reproducibles y exportarlas a CSV para el informe.

## Dataset: videos resumidos y uso experimental

### Origen `video_*.json` (Día 2)
- `src/prepare_dataset.py` parsea `.srt` → agrupa subtítulos (~20 s) → JSON con transcripción, tiempos y `max_duration = 25 %` del total.
- 4 videos en `data/instances/video_1..4.json` (25–50 fragmentos cada uno).

### Mini-videos `mini_video_*.json` (preparados, no ejecutados con LLM)
- Script: `src/prepare_mini_instances.py`
- Toma los **primeros N=10 fragmentos consecutivos** de cada `video_N.json`
- Recalcula `max_duration = 25 %` solo del subconjunto
- Guarda `mini_video_N.json` sin modificar el original
- **No se corrieron** con `--llm --evaluate`: 4×10 fragmentos + coherencia dinámica = cientos de llamadas Gemini

### Instancias sintéticas (casos sencillos — sí ejecutadas)
- `example_instance.json`, `example_instance_overlimit.json`
- `bench_static_vs_dynamic.json`, `bench_irrelevant_middle.json` (5 fragmentos; mock en `test_bench_instances.py`)

### Corridas realizadas / descartadas
- [x] `example_instance.json` → `results/experiments.csv` (baseline + llm_dynamic + llm_static)
- [x] Suite **lite** recomendada: `--suite lite` → 4 instancias sintéticas (~5–10 min)
- [ ] Suite **bench** completa (`--suite bench`, incluye `mini_video_*`): **no ejecutar** — intento previo sin completar; documentado en walkthroughD

## Tareas

- `[x]` Métricas estructurales y post-hoc (`src/experiments/metrics.py`)
- `[x]` `src/run_experiments.py` con `--instances`, `--suite lite`, `--suite bench`, `--llm`, `--static`, `--evaluate`
- `[x]` `src/prepare_mini_instances.py` → `mini_video_1..4.json`
- `[x]` `bench_static_vs_dynamic.json`, `bench_irrelevant_middle.json` + `test_bench_instances.py`
- `[x]` Comparación baseline vs LLM en `example_instance.json`
- `[x]` Suite lite documentada y ejecutable (`results/experiments_bench.csv`)
- `[x]` `summarize.py` → tabla + gráfico
- `[x]` Análisis cualitativo y metodología mini-videos en `walkthroughD.md`
- [ ] Suite bench con `mini_video_*` (opcional; no recomendada)
- [ ] `video_*.json` completos con LLM (opcional; horas)

## Criterios de aceptación

- [x] CSV con filas `(instancia, solver)` en casos sintéticos
- [x] Evaluación post-hoc comparable (`--evaluate`)
- [x] Caché LLM; sin `.env` / `.llm_cache.json` en repo
- [x] Mini-videos documentados (generación + motivo de no ejecución)
- [x] Gráfico/tabla en `results/` (suite lite)
