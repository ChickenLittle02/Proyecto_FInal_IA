## Plan manual — bloque a bloque

> **Histórico (Task E, 2026-06-11):** los bloques 3–8 con `--static` generaron `results/experiments_bench.csv` (15 filas, solvers `baseline` / `llm_dynamic` / `llm_static`). Esos resultados siguen en `results/` como referencia.
>
> **Fase 2 (2026-06-12):** pipeline único **beam search**. Ver `planning/walkthroughF.md` y la sección **Fase 2 — flujo actual** más abajo.

---

## Fase 2 — flujo actual (beam search)

### Validación sin API

```powershell
Set-Location "C:\Users\marti\OneDrive\Documents\ia\Proyecto_FInal_IA"
python src/test_unified.py
python src/test_bench_instances.py
python src/test_llm_solver.py
```

### Ejemplo rápido

```powershell
python src/run_example.py
python src/run_example.py bench_disordered.json
python src/run_example.py bench_disordered.json --llm   # requiere .env
```

Salida esperada: `Solver: baseline_beam (n=5, beam=10)` o `Solver: llm_beam (n=5, beam=10)`.

### Suite lite (baseline_beam + llm_beam)

```powershell
python src/run_experiments.py --suite lite --llm --evaluate `
  --output results/experiments_bench_beam.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Suite lite — beam Fase 2"
```

Cada instancia genera **2 filas** (`baseline_beam`, `llm_beam`). Ya no existen `--static` ni `--reorder`.
Con `--llm`, `llm_beam` aplica juez macro top-M (default M=3) y escribe `summary_llm_*` en el CSV.

### F5 — Escalado por bloques (Groq)

Registro completo: `planning/f5_bloques_ejecucion.md`.

**Bloque 0 ✅** — sin API:

```powershell
python src/test_unified.py
python src/test_bench_instances.py
python src/prepare_mini_instances.py --target-minutes 5 10 15 20 --source-video 2
```

**Bloque 1 ✅** — `dur_5min` (~147 llamadas, ~6 min):

```powershell
python src/run_experiments.py --instances dur_5min.json --llm --evaluate `
  --output results/unified_scaling.csv `
  --notes informe/notas_experimentos.md `
  --block-label "F5 Bloque 1 — escalado dur_5min"
```

**Bloque 2 ⚠️ INTERRUMPIDO (2026-06-12)** — `dur_10min`: ~50 min, **47 %** completado (+185 llamadas API, caché 339→524). Sin CSV. Reporte completo y causas de la demora: `planning/f5_bloques_ejecucion.md` § Bloque 2.

Reanudar (mismo comando; **~55–70 min** restantes estimados, no ~15 min):

```powershell
python src/run_experiments.py --instances dur_10min.json --llm --evaluate `
  --output results/part_dur_10min.csv `
  --notes informe/notas_experimentos.md `
  --block-label "F5 Bloque 2 — escalado dur_10min"
```

Fusionar `part_dur_10min.csv` → `unified_scaling.csv` al terminar.

**Bloques 3–4 ⏳** — `dur_15min` / `dur_20min` (reanudable vía caché; tiempos revisados en `f5_bloques_ejecucion.md`).

**Ablation ⏳** — `--beam-width 3|5|10` en `bench_disordered.json` y `dur_10min.json` (caché caliente).

### Pendiente (F5–F6)

| Task | Descripción |
|---|---|
| F5 | Bloques 2–6 + `execute.md` final |
| F6 | Informe §2–4 solo beam; README final |

---

## Plan manual Task E (obsoleto)

**Estado: completado** (2026-06-11) — Bloques 3–6b, Fase 7 (fusión) y Fase 8 (tabla/gráfico). Entregables en `informe/notas_experimentos.md`, `results/experiments_bench.csv`, `results/summary_bench.md`, `results/comparison_bench.png`.

> ⚠️ Los comandos siguientes usan `--static` y solvers Task E. **No ejecutar** salvo para reproducir resultados históricos.

Misma lógica que `run_lite_suite.py`, pero tú ejecutas cada paso y puedes pausar entre bloques.

---

### Fase 0 — Preparación (~1 min)

```powershell
Set-Location "C:\Users\marti\OneDrive\Documents\ia\Proyecto_FInal_IA"

# Borrar caché LLM
Remove-Item .llm_cache.json -ErrorAction SilentlyContinue

# Crear cabecera del borrador del informe
python -c "from pathlib import Path; import sys; sys.path.insert(0, '.'); from dotenv import load_dotenv; load_dotenv(); from src.experiments.notes import init_notes; init_notes(Path('informe/notas_experimentos.md'), Path('.'), cache_cleared=True)"

# Validación rápida sin API (opcional pero recomendado)
python src/test_bench_instances.py
```

---

### Bloque 3 — `example_instance` (~3 min) — legacy

```powershell
python src/run_experiments.py --instances example_instance.json --llm --static --evaluate `
  --output results/experiments.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Bloque 3 — example_instance"
```

Comprobar: `Guardado ... (3 filas)` y mensaje `Notas actualizadas en informe/notas_experimentos.md`.

---

### Bloque 4 — `example_instance_overlimit` (~3 min) — legacy

```powershell
python src/run_experiments.py --instances example_instance_overlimit.json --llm --static --evaluate `
  --output results/part04_overlimit.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Bloque 4 — example_instance_overlimit"
```

---

### Bloque 5 — `bench_static_vs_dynamic` (~3 min) — legacy

```powershell
python src/run_experiments.py --instances bench_static_vs_dynamic.json --llm --static --evaluate `
  --output results/part05_static_vs_dynamic.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Bloque 5 — bench_static_vs_dynamic"
```

---

### Bloque 6 — `bench_irrelevant_middle` (~3 min) — legacy

```powershell
python src/run_experiments.py --instances bench_irrelevant_middle.json --llm --static --evaluate `
  --output results/part06_irrelevant_middle.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Bloque 6 — bench_irrelevant_middle"
```

---

### Bloque 6b — `bench_disordered` (~3 min) — legacy

```powershell
python src/run_experiments.py --instances bench_disordered.json --llm --static --evaluate `
  --output results/part06b_disordered.csv `
  --notes informe/notas_experimentos.md `
  --block-label "Bloque 6b — bench_disordered"
```

---

### Fase 7 — Fusionar CSVs (~10 s)

```powershell
python src/experiments/merge_results.py
```

Comprobar: `Guardado results/experiments_bench.csv (15 filas)`.

Si falta algún CSV, el script imprime `FALTA: ...` — ejecuta el bloque correspondiente antes de repetir.

---

### Fase 8 — Tabla, gráfico y cierre del borrador (~30 s)

```powershell
python src/experiments/summarize.py `
  --input results/experiments_bench.csv `
  --markdown results/summary_bench.md `
  --chart results/comparison_bench.png

python -c "from pathlib import Path; import sys; sys.path.insert(0, '.'); from src.experiments.notes import append_final_summary; append_final_summary(Path('informe/notas_experimentos.md'), Path('results/experiments_bench.csv'), Path('results/summary_bench.md'), Path('results/comparison_bench.png'), 15)"
```

---

## Checklist final (Task E legacy)

```powershell
(Get-Content results/experiments_bench.csv).Count   # debe ser 16 (15 filas + cabecera)
Get-Item informe/notas_experimentos.md
Get-Item results/summary_bench.md
Get-Item results/comparison_bench.png
```

---

## Si quieres reanudar a mitad (Task E legacy)

| Situación | Qué hacer |
|---|---|
| Ya tienes Bloques 3–4 hechos | Empieza en **Bloque 5** (no borres caché si quieres reutilizar llamadas ya hechas) |
| Un bloque falló por rate limit | Espera 1–2 min y repite **solo ese bloque** (misma línea de comando) |
| Quieres repetir un bloque con scores frescos | Borra `.llm_cache.json` y repite ese bloque |

**Nota:** si reanudas sin borrar caché, **no ejecutes** la Fase 0 de limpieza; los bloques ya corridos no hace falta repetirlos.

---

## Entregables Task E (histórico)

| Archivo | Contenido |
|---|---|
| `informe/notas_experimentos.md` | Notas por bloque + resumen Fase 8 |
| `results/experiments_bench.csv` | 15 filas (5 instancias × 3 solvers legacy) |
| `results/summary_bench.md` | Tabla resumen |
| `results/comparison_bench.png` | Gráfico comparativo |

Con eso puedes pasar directamente a redactar la sección **Resultados y análisis** del informe (datos históricos Task E; nueva corrida beam en F5).
