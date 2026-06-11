# Walkthrough — Paso D: Experimentos y Análisis

Comparación sistemática entre solver clásico y solver asistido por LLM, con exportación de métricas a CSV. Se priorizan **instancias sintéticas pequeñas** para el informe; los videos reales completos y los `mini_video_*` quedan preparados pero **no se ejecutan con LLM** por coste de API.

## Objetivo

Ejecutar experimentos reproducibles sobre casos controlados (5 fragmentos), comparar selecciones y cuantificar diferencias en longitud, cobertura y calidad estimada por LLM — sin depender de corridas de horas sobre `video_*.json` o `mini_video_*.json`.

## Origen del dataset y mini-videos resumidos

### 1. Videos completos (`video_*.json`) — Día 2

Los JSON reales se generaron con `src/prepare_dataset.py`:

1. Se leen los subtítulos `.srt` de cada carpeta en `videos/1..4/`.
2. Los bloques SRT se agrupan en segmentos de ~20–25 s (`group_subtitles`), conservando orden temporal y texto transcrito.
3. Se calcula `max_duration = 25 %` de la duración total de todos los fragmentos.
4. Se guarda en `data/instances/video_N.json` (25–50 fragmentos por video, sin modificar el original).

Cada instancia cumple el enunciado del tema: fragmentos con transcripción, orden del video original, límite de duración para el resumen.

### 2. Mini-videos (`mini_video_*.json`) — Paso D

Para acortar el coste sin tocar los originales, se añadió `src/prepare_mini_instances.py`:

```bash
python src/prepare_mini_instances.py          # default: N=10, videos 1..4
python src/prepare_mini_instances.py --n 5    # solo 5 fragmentos
```

**Qué hace el script:**

| Paso | Acción |
|---|---|
| Entrada | `data/instances/video_N.json` |
| Corte | Conserva los **primeros N fragmentos consecutivos** (default N=10) |
| Límite | Recalcula `max_duration = 25 %` de la duración **del subconjunto** |
| Salida | `data/instances/mini_video_N.json` (nuevo archivo; `video_N.json` intacto) |

**Ejemplo generado** (`mini_video_1.json`): 10 fragmentos, ~250 s de contenido fuente, `max_duration ≈ 62.6 s`.

**Por qué los primeros N:** el inicio de cada charla suele contener la introducción y la tesis principal; es representativo para comparar solvers sin procesar todo el vídeo.

### 3. Instancias sintéticas bench (`bench_*.json`)

Diseñadas a mano (5 fragmentos, textos pedagógicos en español):

- `bench_static_vs_dynamic.json` — escenario “salto”: el estático favorece pares consecutivos; el dinámico puede saltar un fragmento puente. Validado con `src/test_bench_instances.py` (mock, sin API).
- `bench_irrelevant_middle.json` — fragmento central de música/anuncio sin contenido educativo; comprueba que el LLM lo deprioriza.

## Cómo se usaron en los experimentos

| Instancia | Fragmentos | ¿Ejecutada con LLM? | Motivo |
|---|---|---|---|
| `example_instance.json` | 5 | **Sí** | Caso base del proyecto; resultados en `results/experiments.csv` |
| `example_instance_overlimit.json` | 5 | **Sí** (suite lite) | Límite de duración más estricto |
| `bench_static_vs_dynamic.json` | 5 | **Sí** (suite lite) | Contraste estático vs dinámico |
| `bench_irrelevant_middle.json` | 5 | **Sí** (suite lite) | Fragmento irrelevante |
| `mini_video_1..4.json` | 10 c/u | **No** | ~40 fragmentos + coherencia dinámica → cientos de llamadas Gemini (+ 1 s sleep/call) |
| `video_1..4.json` | 25–50 c/u | **No** | Varias horas; reservado para anexo opcional |

**Corrida intentada y descartada:** `--suite bench` (lite + mini_video) se lanzó pero **no se completó** — sin salida de progreso durante >15 min, coste API excesivo. **No repetir** salvo disponer de cuota amplia y tiempo.

**Corrida recomendada y ejecutada:**

```bash
python src/run_experiments.py --suite lite --llm --static --evaluate \
  --output results/experiments_bench.csv
```

4 instancias × 3 solvers = 12 filas; ~5–10 min con caché (`.llm_cache.json`).

## Diseño

| Componente | Decisión |
|---|---|
| Script principal | `src/run_experiments.py` |
| Suite **lite** (recomendada) | `--suite lite` → `example_*.json`, `bench_*.json` |
| Suite **bench** (pesada) | `--suite bench` → lite + `mini_video_*.json` — documentada, no ejecutada |
| Mini-instancias | `src/prepare_mini_instances.py` — solo generación de datos |
| Métricas | `src/experiments/metrics.py` |
| Resumen | `src/experiments/summarize.py` → `summary_bench.md`, `comparison_bench.png` |

### Métricas recogidas

**Estructurales:** `n_selected`, `duration_utilization`, `fragment_coverage`, `solver_score`, etc.

**Post-hoc (`--evaluate`):** `mean_relevance`, `mean_coherence`, `objective_score` (misma función para baseline y LLM).

## Uso

```bash
# Generar mini-instancias (solo datos; no implica corrida LLM)
python src/prepare_mini_instances.py

# Validar bench con mock (sin API)
python src/test_bench_instances.py

# Experimentos recomendados para el informe (~5–10 min)
python src/run_experiments.py --suite lite --llm --static --evaluate \
  --output results/experiments_bench.csv

# Resumen
python src/experiments/summarize.py \
  --input results/experiments_bench.csv \
  --markdown results/summary_bench.md \
  --chart results/comparison_bench.png

# NO recomendado en plan gratuito Gemini / sin tiempo:
# python src/run_experiments.py --suite bench --llm --static --evaluate ...
```

## Análisis cualitativo (informe)

1. **Baseline vs LLM:** el baseline llena el cupo de duración con scores uniformes; los solvers LLM omiten fragmentos menos relevantes (`example_instance`: selección `[0,1,2,4]` vs baseline `[0,1,2,3,4]`).

2. **Estático vs dinámico:** en `bench_static_vs_dynamic.json` el mock demuestra selecciones distintas; con LLM real las diferencias dependen de puntuaciones, pero el diseño del caso fuerza el contraste entre coherencia consecutiva y saltos.

3. **Fragmento irrelevante:** `bench_irrelevant_middle.json` incluye un segmento de música/anuncio; se espera exclusión en la selección LLM.

4. **Mini-videos:** archivos listos en `data/instances/` para quien quiera extender el estudio; no forman parte de los resultados cuantitativos actuales por coste.

5. **Evaluación justa:** `--evaluate` aplica el mismo `evaluate_selection_with_llm` a todas las filas del CSV.

## Criterios de aceptación (estado)

- [x] Script de experimentos y exportación CSV.
- [x] Suite **lite** ejecutada → `results/experiments_bench.csv`.
- [x] Mini-videos generados y documentados (sin corrida LLM).
- [x] Suite **bench** completa documentada como no ejecutada (casos grandes).
- [x] Tabla y gráfico en `results/summary_bench.md` + `comparison_bench.png`.
- [ ] Corrida LLM sobre `mini_video_*` o `video_*` completos (opcional).

## Siguiente paso → Paso E (informe)

Incorporar CSV/gráficos de `results/` al informe; describir limitación de coste API y uso de instancias sintéticas + suite lite.
