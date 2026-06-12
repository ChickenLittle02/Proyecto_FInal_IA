# Proyecto Final IA - Selección y ordenación de fragmentos

Este repositorio contiene una base inicial para el proyecto final de IA sobre selección de fragmentos de video educativo.

## Estructura creada

- `src/problem.py` — definición formal del problema y representación de fragmentos.
- `src/instance.py` — carga y guardado de instancias en JSON.
- `src/llm/scoring.py` — precálculo cacheado `relevance[n]` + `coherence[n×n]`.
- `src/solver/unified.py` — **beam search** (único algoritmo combinatorio de producción).
- `src/solver/llm_assisted.py` — puntos de entrada `solve()` / `solve_baseline()` → beam.
- `src/llm/client.py` — wrapper de configuración de LLM (Gemini, Groq y APIs compatibles con OpenAI).
- `src/llm/prompts.py` — prompts micro (fragmento/par) y macro (`summary_evaluation_prompt`).
- `src/llm/cache.py` — caché local para respuestas de LLM.
- `src/run_experiments.py` — comparación `baseline_beam` vs `llm_beam` con salida CSV.
- `src/experiments/` — métricas y resumen (`summarize.py`).
- `tests/legacy/` — solvers Task E (DP, heurística); **no importar desde producción**.
- `planning/walkthroughF.md` — registro de cambios Fase 2 (F1–F6).
- `informe/informe_tecnico.md` — borrador del informe (problema, algoritmos, metodología).
- `informe/notas_experimentos.md` — notas automáticas por bloque experimental.
- `execute.md` — plan de ejecución (Fase 2 beam + histórico Task E).

## Arquitectura unificada (Fase 2)

```
Entrada: fragmentos + max_duration
    │
    ▼
[Precálculo LLM cacheado]  relevance[n] + coherence[n×n]   ← src/llm/scoring.py
    │
    ▼
[Beam search]              selecciona + ordena (sin API)   ← src/solver/unified.py
    │
    ▼
[Top-M + juez macro]       evaluate_summary (F3 ✅; integración en solve → F4)
    │
    ▼
Salida: índices ordenados + score local
```

| Variante | Función | Scores | Modo impreso |
|---|---|---|---|
| Sin LLM | `solve_baseline()` | relevancia uniforme + coherencia temporal | `baseline_beam` |
| Con LLM | `solve()` | relevancia + coherencia vía API (cacheadas) | `llm_beam` |

Parámetro `beam_width=10` (default). El LLM **no elige índices**; solo puntúa fragmentos y pares antes del beam search.

Solvers legacy (Task E: DP bitmask, heurística 2 fases, `--static`) están en `tests/legacy/` y **no** son ejecutables desde CLI.

## Configuración del entorno

- Python 3.10+
- Instalar dependencias:

```bash
pip install -r requirements.txt
```

Copia `.env.example` a `.env` en la raíz del proyecto (`.env` está en `.gitignore`).

```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux / macOS
```

## Configuración de APIs LLM

El proveedor activo se elige con `LLM_PROVIDER` en `.env`. El cliente lee las variables al iniciar cada script.

### Google Gemini (por defecto)

1. Genera una clave en [Google AI Studio](https://aistudio.google.com/).
2. Configura `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_api_de_gemini_aqui
LLM_MODEL=gemini-2.5-flash
```

| Aspecto | Plan gratuito |
|---|---|
| Peticiones/día | ~20 |
| Velocidad | Lenta (reintentos por rate limit) |
| Calidad en español | Muy buena |

### Groq (recomendado para experimentos masivos)

Groq expone una API **compatible con OpenAI**. Registro gratuito sin tarjeta en [console.groq.com](https://console.groq.com).

```env
LLM_PROVIDER=groq
OPENAI_API_KEY=gsk_tu_clave_aqui
LLM_MODEL=llama-3.3-70b-versatile
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

Equivalente usando `LLM_PROVIDER=openai` (misma integración):

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=gsk_tu_clave_aqui
LLM_MODEL=llama-3.1-8b-instant
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

| Aspecto | Plan gratuito |
|---|---|
| Peticiones/día | ~14 400 |
| Req/min | ~30 |
| Modelo recomendado | `llama-3.3-70b-versatile` (mejor que `llama-3.1-8b-instant` para coherencia) |

### Cómo cambiar de API

1. Edita `.env` y cambia `LLM_PROVIDER`, la clave y el modelo.
2. **Borra la caché** para no mezclar respuestas de modelos distintos:

```bash
del .llm_cache.json          # Windows
rm .llm_cache.json           # Linux / macOS
```

3. Verifica la conexión:

```bash
python src/test_llm.py
```

4. Ejecuta los experimentos con la nueva API (mismos comandos, distinto proveedor).

> **Nota:** no hace falta cambiar código. Solo `.env` + borrar caché al cambiar de proveedor o modelo.

## Ejecución de ejemplos

Prueba clásica con instancia sintética:

```bash
python src/run_example.py
```

Instancia real (subtítulos de un video TED):

```bash
python src/run_example.py video_3.json
```

Solver asistido por LLM (requiere `.env` configurado). Selecciona y ordena con beam search:

```bash
python src/run_example.py --llm
python src/run_example.py bench_disordered.json --llm
python src/run_example.py video_3.json --llm
```

Solver baseline sin LLM (mismos beam search, scores proxy por `start_time`):

```bash
python src/run_example.py bench_disordered.json
```

Cada ejecución imprime el modo, p. ej. `Solver: llm_beam (n=5, beam=10)`.

## Instancias de datos

| Tipo | Archivos | Fragmentos | Uso |
|---|---|---|---|
| Sintéticas | `example_instance*.json` | 5 | Casos base del proyecto |
| Bench | `bench_*.json` | 5 | Contraste estático/dinámico, fragmento irrelevante, input permutado |
| Mini videos | `mini_video_1..4.json` | 10 c/u | Recortes de videos reales (generados con `prepare_mini_instances.py`) |
| Videos completos | `video_1..4.json` | 25–50 c/u | Dataset completo del Día 2 (muy pesado con LLM) |

Generar o regenerar mini-instancias (primeros N fragmentos consecutivos de cada video):

```bash
python src/prepare_mini_instances.py
python src/prepare_mini_instances.py --n 10 --videos 1 2    # solo videos 1 y 2
```

### ¿Los mini-videos prueban fragmentos desordenados?

**No.** Los `mini_video_*.json` conservan el **orden cronológico** del video original: `prepare_mini_instances.py` toma los primeros N fragmentos consecutivos de cada `video_*.json`, sin barajar ni reordenar.

### Instancias bench

Los casos **bench** (sintéticas) validan comportamiento lógico del beam search:

| Instancia | Qué valida |
|---|---|
| `bench_irrelevant_middle.json` | **Omisión** de un fragmento irrelevante en el centro (música/anuncio) |
| `bench_disordered.json` | Mismos textos permutados en el JSON. Con `solve()` debe devolver `[1, 4, 3, 0]` — introducción → definición → ejemplo → conclusión — omitiendo el irrelevante (índice 2). |
| `bench_static_vs_dynamic.json` | Caso histórico Task E (contraste estático/dinámico); referencia en `tests/legacy/` |

Para comprobar todo sin API:

```bash
python src/test_unified.py
python src/test_bench_instances.py
```

## Suite lite automatizada (notas + gráfico)

Para ejecutar **todos los bloques 3–8** de una vez, borrar la caché LLM al inicio y generar automáticamente `informe/notas_experimentos.md` (escenario, selecciones, observación cualitativa y métricas por bloque), más `experiments_bench.csv`, `summary_bench.md` y `comparison_bench.png`:

```bash
python src/run_lite_suite.py
```

Opciones útiles:

| Flag | Descripción |
|---|---|
| `--from-block 4` | Ejecutar desde el bloque 4 hasta el final |
| `--block 5` | Solo el bloque 5 |
| `--keep-cache` | No borrar `.llm_cache.json` al inicio |
| `--skip-tests` | Omitir `test_bench_instances.py` antes de los bloques LLM |
| `--no-merge` | Solo bloques + notas; sin fusionar CSV ni gráfico |

Cada bloque individual también puede anotar notas si usas `--notes` y `--block-label` en `run_experiments.py`:

```bash
python src/run_experiments.py --instances bench_irrelevant_middle.json --llm --evaluate \
  --output results/part06_irrelevant_middle.csv \
  --notes informe/notas_experimentos.md \
  --block-label "Bloque 6 — bench_irrelevant_middle"
```

## Experimentación por bloques (≤ 3 min por bloque)

Plan de ejecución incremental. Cada bloque LLM con instancias de 5 fragmentos tarda ~2–3 min con Groq; con Gemini free puede ser más lento por cuota.

Desde la raíz del proyecto (PowerShell):

```powershell
Set-Location "C:\Users\marti\OneDrive\Documents\ia\Proyecto_FInal_IA"
```

### Bloque 0 — Validación (~10 s)

```bash
python src/test_bench_instances.py
```

### Bloque 1 — Baseline en instancias lite (~15 s, sin API)

Métricas estructurales de referencia; no consume LLM.

```bash
python src/run_experiments.py --suite lite --output results/part01_baseline_lite.csv
```

### Bloque 2 — Baseline en videos reales (~15 s, opcional)

Compara el solver clásico con el dataset del Día 2.

```bash
python src/run_experiments.py --instances video_1.json video_2.json video_3.json video_4.json --output results/part02_baseline_videos.csv
```

### Bloque 3 — `example_instance` (~2–3 min)

Opcional si ya confías en `results/experiments.csv`.

```bash
python src/run_experiments.py --instances example_instance.json --llm --evaluate --output results/part03_example_instance.csv
```

### Bloque 4 — `example_instance_overlimit` (~2–3 min)

```bash
python src/run_experiments.py --instances example_instance_overlimit.json --llm --evaluate --output results/part04_overlimit.csv
```

### Bloque 5 — `bench_static_vs_dynamic` (~2–3 min)

```bash
python src/run_experiments.py --instances bench_static_vs_dynamic.json --llm --evaluate --output results/part05_static_vs_dynamic.csv
```

### Bloque 6 — `bench_irrelevant_middle` (~2–3 min)

```bash
python src/run_experiments.py --instances bench_irrelevant_middle.json --llm --evaluate --output results/part06_irrelevant_middle.csv
```

### Bloque 6b — `bench_disordered` (~2–3 min)

Input permutado; `baseline_beam` + `llm_beam` reordenan automáticamente:

```bash
python src/run_experiments.py --instances bench_disordered.json --llm --evaluate --output results/part06b_disordered.csv
```

### Bloque 7 — Fusionar CSVs (~10 s)

Une la suite bench completa. Guarda en `results/experiments_bench.csv`.

```bash
python src/experiments/merge_results.py
```

Si ejecutaste el Bloque 3, edita la lista de fuentes en `merge_results.py` o sustituye `experiments.csv` por `part03_example_instance.csv`.

Alternativa manual (si prefieres no usar el script):

```bash
python -c "import csv; from pathlib import Path; root=Path('.'); sources=[root/'results/experiments.csv', root/'results/part04_overlimit.csv', root/'results/part05_static_vs_dynamic.csv', root/'results/part06_irrelevant_middle.csv']; out=root/'results/experiments_bench.csv'; rows,fields=[],None
for p in sources:
    if not p.exists(): print(f'FALTA: {p}'); continue
    with p.open(encoding='utf-8',newline='') as f:
        r=csv.DictReader(f); fields=fields or r.fieldnames; rows.extend(list(r))
with out.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print(f'Guardado {out} ({len(rows)} filas)')"
```

### Bloque 8 — Tabla y gráfico para el informe (~15 s)

```bash
python src/experiments/summarize.py --input results/experiments_bench.csv --markdown results/summary_bench.md --chart results/comparison_bench.png
```

### Bloques opcionales — Mini-videos (subconjuntos)

Cada `mini_video_*.json` tiene 10 fragmentos. Con `--llm --evaluate` implica más llamadas que los bench de 5 fragmentos (~4–8 min por mini-video con Groq).

```bash
python src/run_experiments.py --instances mini_video_1.json --llm --evaluate --output results/part07_mini_video_1.csv
python src/run_experiments.py --instances mini_video_1.json mini_video_2.json --llm --evaluate --output results/part07_mini_videos_1_2.csv
python src/run_experiments.py --instances mini_video_*.json --output results/part07_baseline_mini.csv
```

Suite predefinida (lite + mini-videos; **pesada** con LLM):

```bash
python src/run_experiments.py --suite bench --llm --evaluate --output results/experiments_bench_full.csv
```

### Opciones útiles de `run_experiments.py`

| Flag | Descripción |
|---|---|
| `--suite lite` | `example_*.json` + `bench_*.json` |
| `--suite bench` | lite + `mini_video_*.json` |
| `--instances A B` | Lista explícita de instancias (nombre, ruta o glob) |
| `--llm` | Incluir `llm_beam` (precálculo LLM + beam search) |
| `--evaluate` | Métricas post-hoc (relevancia, coherencia, objective_score) |
| `--output PATH` | CSV de salida |
| `--coherence-weight 0.25` | Peso de coherencia (default 0.25) |

Siempre se ejecuta `baseline_beam`. Con `--llm` se añade `llm_beam` (2 filas por instancia).

## Instancia de ejemplo

`data/instances/example_instance.json` tiene 5 fragmentos y `max_duration=45.0`. El solver debe seleccionar los más relevantes y coherentes dentro del límite.

```bash
python src/run_example.py
```
