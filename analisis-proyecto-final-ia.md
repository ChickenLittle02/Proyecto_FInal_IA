# Análisis del Proyecto Final — Inteligencia Artificial 2025-2026

> 10 temas que combinan **optimización / planificación / CSP** con un **LLM** como componente funcional. Análisis de cada uno, ranking de dificultad, stack recomendado, estructura de proyecto, rol del LLM y qué entregar.

---

## 📋 Índice

1. [Lo que el profesor realmente está pidiendo](#lo-que-el-profesor-realmente-está-pidiendo)
2. [Stack tecnológico recomendado](#stack-tecnológico-recomendado)
3. [Estructura común del proyecto](#estructura-común-del-proyecto)
4. [Patrones de integración del LLM](#patrones-de-integración-del-llm)
5. [Ranking de dificultad](#ranking-de-dificultad)
6. [Análisis de cada tema (1–10)](#análisis-de-cada-tema)
7. [Mi recomendación](#mi-recomendación)
8. [Checklist de entrega](#checklist-de-entrega)

---

## Lo que el profesor realmente está pidiendo

Lee con cuidado el enunciado. El proyecto es **híbrido**:

- Un **componente algorítmico clásico** de IA: optimización, búsqueda, planificación, satisfacción de restricciones (CSP), búsqueda local, metaheurísticas, programación entera, etc.
- Un **componente de LLM**: integrado de forma significativa en el flujo, no como adorno.

Lo que evalúan implícitamente:
1. **Modelado formal**: que sepas formalizar el problema (variables, dominios, restricciones, función objetivo).
2. **Algoritmo no trivial**: backtracking + heurísticas, A*, programación dinámica, GRASP, simulated annealing, ILP, etc.
3. **Integración real del LLM**: el LLM debe aportar algo que el algoritmo solo no puede (interpretar texto, evaluar coherencia semántica, generar candidatos).
4. **Diseño experimental**: instancias variadas, comparación entre configuraciones (con vs sin LLM, distintos algoritmos, distintos prompts), análisis de resultados.

> ⚠️ **Trampa común**: hacer un sistema donde el LLM hace TODO el trabajo y el "algoritmo" es trivial. Eso normalmente baja la nota. El LLM debe ser un **componente** del sistema, no el sistema completo.

---

## Stack tecnológico recomendado

### Lenguaje: **Python**

Es la opción dominante por:
- Ecosistema de IA y LLM (langchain, openai, anthropic SDK).
- Solvers de optimización (`ortools`, `pulp`, `python-constraint`).
- Manipulación de datos (`pandas`, `numpy`).
- Visualización rápida (`matplotlib`, `streamlit` si quieres demo).

### LLM: opciones según presupuesto

| Opción | Costo | Pros | Contras |
|--------|-------|------|---------|
| **API Anthropic Claude** (Haiku) | ~$0.25 / 1M tok input | Calidad alta, fácil | Necesitas tarjeta |
| **API OpenAI** (gpt-4o-mini) | ~$0.15 / 1M tok input | Muy popular, fácil | Necesitas tarjeta |
| **Google Gemini** | Plan gratuito decente | Gratis | Rate limits |
| **Groq** (Llama 3.x) | Gratis con rate limit | Rápido | Limitado |
| **Ollama local** (Llama 3.1, Qwen, etc.) | Gratis | Sin internet, sin costo | Necesita GPU/RAM decente |

**Recomendación práctica**: empieza con un modelo gratis (Gemini o Groq) para desarrollar, y deja una variable de entorno que permita cambiar de proveedor. Para los experimentos finales, si te alcanza, usa un modelo bueno (Claude Haiku, gpt-4o-mini); si no, Llama 3.1 70B en Groq es gratis y suficientemente bueno.

### Librerías clave

```
# LLM
openai / anthropic / google-generativeai  (elige una)
litellm                                    # abstrae proveedores

# Optimización / CSP
ortools                                    # CP-SAT, MIP, routing
python-constraint                          # CSP simple
pulp                                       # ILP fácil
networkx                                   # grafos (planificación, prerequisitos)

# Datos
pandas, numpy

# Validación / serialización
pydantic                                   # forzar respuestas estructuradas del LLM

# Pruebas / experimentos
pytest, tqdm, matplotlib
```

---

## Estructura común del proyecto

```
proyecto-final-ia/
├── README.md
├── requirements.txt
├── .env.example                  # API keys de ejemplo
├── informe/
│   └── informe.pdf
├── src/
│   ├── __init__.py
│   ├── problem.py                # definición formal del problema
│   ├── instance.py               # carga/genera instancias
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── baseline.py           # algoritmo sin LLM (control)
│   │   ├── exact.py              # backtracking / ILP / CP-SAT
│   │   ├── heuristic.py          # GRASP / SA / búsqueda local
│   │   └── llm_assisted.py       # solver que usa LLM en algún paso
│   ├── llm/
│   │   ├── client.py             # wrapper agnóstico de proveedor
│   │   ├── prompts.py            # plantillas
│   │   └── cache.py              # cache para no quemar tokens
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── experiments.py
│   └── main.py                   # CLI
├── data/
│   ├── instances/                # JSONs con casos de prueba
│   └── results/                  # CSVs de corridas
├── notebooks/
│   └── analysis.ipynb
└── tests/
    └── test_*.py
```

### Regla de oro: **cachear las respuestas del LLM**

Vas a iterar mucho. Sin caché vas a quemar dinero (o cuotas) repitiendo las mismas llamadas. Un caché simple en disco (clave = hash del prompt) te ahorra horas:

```python
import hashlib, json, pathlib
class LLMCache:
    def __init__(self, dir="data/llm_cache"):
        self.dir = pathlib.Path(dir); self.dir.mkdir(parents=True, exist_ok=True)
    def _key(self, prompt, model): 
        return hashlib.sha256(f"{model}::{prompt}".encode()).hexdigest()
    def get(self, prompt, model):
        f = self.dir / f"{self._key(prompt, model)}.json"
        return json.loads(f.read_text()) if f.exists() else None
    def put(self, prompt, model, response):
        f = self.dir / f"{self._key(prompt, model)}.json"
        f.write_text(json.dumps(response))
```

---

## Patrones de integración del LLM

Hay esencialmente **5 roles** que el LLM puede jugar. Identificar bien cuál(es) usas es media nota del informe.

### 1. **LLM como extractor / parser**
Toma texto crudo y produce estructura: extrae síntomas de una historia clínica, prerequisitos de la descripción de un curso, etc. Salida en JSON validado con `pydantic`.

### 2. **LLM como evaluador (juez)**
Le das una solución candidata y devuelve un score (0-1) o un análisis cualitativo. Útil cuando el "valor" de una solución depende de coherencia semántica que no puedes medir con métricas duras.

### 3. **LLM como generador de candidatos**
El LLM propone soluciones (o partes); el algoritmo las valida y combina. Útil en metaheurísticas: el LLM hace de "mutación inteligente".

### 4. **LLM como heurística**
Guía la búsqueda: dada una decisión a tomar, el LLM ranquea opciones. Esencialmente reemplaza una heurística manual.

### 5. **LLM como interfaz**
Convierte el objetivo del usuario en lenguaje natural a parámetros del problema, y los resultados a explicación legible. Vale puntos pero por sí solo no es suficiente.

> 💡 **Lo más impresionante**: combinar al menos dos roles. Por ejemplo: extracción (1) + evaluación (2), o generación (3) + evaluación (2).

---

## Ranking de dificultad

| # | Tema | Componente algorítmico | Dificultad | Tiempo |
|---|------|------------------------|-----------|--------|
| 8 | Generación de mensajes con restricciones | CSP + generación | ⭐⭐ | 15–25 h |
| 6 | Segmentación óptima de contenido | DP / cortes óptimos | ⭐⭐ | 20–30 h |
| 2 | Resúmenes (selección de segmentos) | Knapsack | ⭐⭐ | 20–30 h |
| 9 | Rutas de aprendizaje | DAG + scheduling | ⭐⭐⭐ | 25–35 h |
| 3 | Trayectoria profesional | Planificación con prerequisitos | ⭐⭐⭐ | 25–35 h |
| 1 | Priorización de casos clínicos | Knapsack / scheduling | ⭐⭐⭐ | 30–40 h |
| 10 | Anomalías en secuencias | Min-set cover | ⭐⭐⭐ | 30–40 h |
| 4 | Patrones sospechosos | Pattern matching | ⭐⭐⭐⭐ | 35–45 h |
| 7 | Trayectorias alternativas | Búsqueda multi-objetivo | ⭐⭐⭐⭐ | 35–50 h |
| 5 | Reparación de inconsistencias | SAT / belief revision | ⭐⭐⭐⭐⭐ | 40–60 h |

(Las horas son orientativas, asumiendo que estás aprendiendo sobre la marcha.)

---

## Análisis de cada tema

### Tema 1 — Priorización de casos clínicos bajo recursos limitados

**Problema formal:** tienes N pacientes, cada uno con (severidad, recursos requeridos, tiempo estimado, descripción textual). Debes producir un orden / asignación que maximice el "impacto total" sin exceder los recursos.

**Modelado matemático:**
- Variante **knapsack** si el orden no importa (atender o no a cada uno).
- Variante **scheduling con recursos** si hay que ordenar y asignar a slots de tiempo.
- Variables: x_i ∈ {0,1}, asignación a recurso/turno, orden temporal.
- Restricciones: capacidad de recursos, prerequisitos médicos, ventanas de tiempo.

**Algoritmos:**
- ILP con `pulp` u `ortools` (rápido y exacto en instancias razonables).
- Branch & bound propio para instancias pequeñas.
- GRASP/SA para instancias grandes.

**Rol del LLM:**
- (1) **Extractor**: convierte la descripción textual del caso ("paciente con dolor torácico y antecedentes...") en features numéricos/categóricos (severidad estimada, urgencia, especialidad requerida).
- (2) **Evaluador**: dado un orden propuesto, evalúa si el ranking médicamente tiene sentido.

**Dataset:**
- Sintético: generar 50–200 casos con plantillas + LLM en modo "creador de pacientes".
- Real (mejor): usar dataset MIMIC-III/IV (público, requiere registro), o simplificar y usar resúmenes anonimizados.

**Riesgo:** ético/médico. Aclarar fuertemente que es académico y no clínico.

**Por qué tiene su dificultad media:** el modelado de "impacto" no es trivial, y la métrica de evaluación tampoco.

---

### Tema 2 — Resúmenes como selección óptima de segmentos

**Problema formal:** dados N fragmentos {f_i} de un video con (duración_i, contenido_i), seleccionar S ⊆ {1..N} y un orden, tal que:
- Σ duración_i ≤ L (límite).
- Maximizar coherencia(S) + cobertura(S).

**Modelado matemático:**
- **Knapsack 0/1** por la restricción de duración.
- **TSP-like** por el orden (peso = penalización por discontinuidad entre fragmentos).
- Variante: **knapsack con sinergia** (el valor de un fragmento depende de los otros seleccionados).

**Algoritmos:**
- DP knapsack clásico para 0/1 sin orden.
- Local search 2-opt para ordenamiento.
- ILP para versión combinada.

**Rol del LLM:**
- (2) **Evaluador**: scoring de coherencia entre fragmentos consecutivos y cobertura total. Esta es la métrica clave que NO puedes calcular sin LLM (o con embeddings + reglas).
- (1) **Extractor**: tags/temas por fragmento.
- (5) **Interfaz**: pedir el resumen final como texto fluido.

**Dataset:**
- Tomar transcripts reales de YouTube educativos (yt-dlp + whisper) y partirlos en fragmentos por subtítulos.
- 5-10 videos × 30-50 fragmentos cada uno.

**Por qué es accesible:** la métrica de coherencia tiene definición clara, los algoritmos de selección son estándar, y los videos educativos son fáciles de conseguir.

---

### Tema 3 — Planificación de trayectoria profesional

**Problema formal:** grafo dirigido de cursos con prerequisitos (DAG). Estado meta: tener cierto conjunto de habilidades. Encontrar secuencia válida (topológica) que llegue al objetivo.

**Modelado:**
- **Planning STRIPS-like**: estados = subconjuntos de habilidades; acciones = tomar curso (precondiciones = prerequisitos, efectos = añadir habilidades).
- O simplemente **shortest path en DAG** si es mono-objetivo.

**Algoritmos:**
- A* con heurística admisible (ej. nº mínimo de cursos restantes para llegar al objetivo).
- BFS/DFS si los costos son uniformes.
- Topological sort si solo se busca un orden.

**Rol del LLM:**
- (5) **Interfaz**: el usuario dice "quiero ser ingeniero de ML enfocado en NLP" → LLM mapea a conjunto de habilidades meta.
- (2) **Evaluador**: dada una trayectoria, valora qué tan buena es para el objetivo.
- (1) **Extractor**: convierte descripciones de cursos a (prerequisitos, habilidades_obtenidas).

**Dataset:**
- Catálogo de cursos sintético (50-200 cursos) con prerequisitos.
- Real: scrapear catálogo de Coursera/edX o tu propia universidad.

**Buen tema porque:** A* + LLM como heurística ranking es elegante, y permite contar bien la metodología.

---

### Tema 4 — Detección de patrones sospechosos en secuencias de mensajes

**Problema formal:** dada secuencia M = [m_1, ..., m_n], encontrar subsecuencias contiguas/no-contiguas que matchean reglas como "pedir información personal seguido de presión" o "phishing escalonado".

**Modelado:**
- Si las reglas son regulares → autómata finito.
- Si hay restricciones de "ventana temporal" → CSP.
- Si las reglas son semánticas → híbrido.

**Algoritmos:**
- Pattern matching clásico (Aho-Corasick, regex) sobre etiquetas semánticas.
- CSP: variables = posiciones, dominios = subconjuntos, restricciones = orden y semántica.
- Sliding window con clasificador.

**Rol del LLM:**
- (1) **Extractor**: clasifica cada mensaje en etiquetas semánticas ("pregunta personal", "presión emocional", "request_dinero").
- (2) **Evaluador**: confirma si una subsecuencia candidata realmente cumple el patrón sospechoso (resuelve falsos positivos).

**Dataset:**
- Sintético (con LLM): generar conversaciones limpias y sospechosas según plantillas.
- Real: dataset de phishing emails, o conversaciones de scam públicas (cuidar privacidad).

**Por qué es difícil:** definir formalmente qué es "sospechoso" es resbaladizo. Hay que diseñar bien el lenguaje de reglas.

---

### Tema 5 — Reparación de inconsistencias en historiales (EL MÁS DIFÍCIL)

**Problema formal:** conjunto de hechos H = {h_1, ..., h_n}, posiblemente inconsistentes. Encontrar D ⊆ H mínimo tal que H \ D sea consistente.

**Modelado:**
- **Belief revision** (AGM).
- **Min-cost SAT**: variables = inclusión de cada hecho, restricciones = consistencia.
- **MaxSAT**: maximizar hechos retenidos sujeto a consistencia.

**Algoritmos:**
- Solver MaxSAT (`pysat`).
- Branch & bound sobre subconjuntos.
- Aproximación greedy (eliminar el más conflictivo primero).

**Rol del LLM:**
- (2) **Evaluador**: dada una pareja de hechos, decide si son contradictorios. Esto es lo único que un solver clásico no puede hacer (porque la consistencia es semántica, no sintáctica).
- (1) **Extractor**: normaliza hechos textuales a forma estructurada.

**Dataset:**
- Sintético: generar historiales con contradicciones inyectadas.
- Real: facts de Wikipedia con vandalismo histórico (complejo de obtener).

**Por qué es el más difícil:**
- Definir "consistencia semántica" es complejo.
- El espacio de soluciones es 2^n.
- El LLM como oráculo de consistencia introduce ruido (no es 100% confiable) y hay que manejarlo.
- Riesgo alto de no terminar bien.

**Si lo eliges**, restringe MUCHO el dominio (ej. solo hechos sobre fechas y lugares).

---

### Tema 6 — Segmentación óptima de contenido

**Problema formal:** dada secuencia E = [e_1, ..., e_n], encontrar particiones {[i_0..i_1], [i_1+1..i_2], ...} contiguas tal que se maximice la suma de coherencias internas.

**Modelado:**
- Es un problema de **partición secuencial / cortes óptimos**.
- Variable: cortes c_1 < c_2 < ... < c_k entre 1 y n-1.

**Algoritmos:**
- **Programación dinámica**: dp[i] = mejor segmentación de los primeros i elementos. Transición O(n²) si pre-computas coherencias por par. **Total: O(n³)** o O(n²) con buena precomputación.
- Variante con número de segmentos fijo (DP 2D).

**Rol del LLM:**
- (2) **Evaluador**: coherencia(segmento) — el componente que el algoritmo no puede calcular solo. Llamadas O(n²) (todos los rangos posibles) → necesitas caché agresivo + quizás precalcular embeddings y usar LLM solo para top-k candidatos.

**Truco importante:** para no llamar al LLM O(n²) veces, usa un esquema en dos fases:
1. Pre-segmentar con embeddings + similitud coseno (barato).
2. LLM solo refina los cortes ambiguos.

**Dataset:**
- Capítulos de libros en dominio público (Project Gutenberg) sin sus delimitadores.
- Transcripts largos de podcasts.

**Por qué es accesible:** DP es estándar; el desafío real es la integración eficiente con LLM. Buen tema.

---

### Tema 7 — Exploración de trayectorias profesionales alternativas

**Problema formal:** árbol de decisiones de carrera. Generar K trayectorias distintas, evaluarlas en múltiples criterios (sueldo esperado, satisfacción, estabilidad, tiempo).

**Modelado:**
- **Búsqueda multi-objetivo** → frente de Pareto.
- **k-shortest paths**.
- **MOEA** (NSGA-II) si hay muchos criterios.

**Algoritmos:**
- Yen's algorithm para k-shortest.
- NSGA-II (`pymoo`) para Pareto-optimal multi-criterio.

**Rol del LLM:**
- (3) **Generador**: propone trayectorias creativas que la búsqueda no exploraría.
- (2) **Evaluador**: comparación cualitativa entre dos trayectorias en el frente de Pareto ("¿cuál es más realista para alguien sin background técnico?").
- (5) **Interfaz**: explicar trade-offs.

**Por qué es difícil:** multi-objetivo + LLM creativo = muchas piezas. Pero queda muy lucido.

---

### Tema 8 — Generación de mensajes bajo restricciones estructurales

**Problema formal:** generar un mensaje T tal que cumple restricciones C = {len(T) ≤ L, debe contener X, no contiene Y, tono = formal, etc.}.

**Modelado:**
- **CSP de generación**: el espacio de soluciones es texto.
- **Filtrado generación-y-validación** (generate-and-test).

**Algoritmos:**
- LLM genera N candidatos.
- Validador determinístico filtra los que cumplen restricciones duras.
- Si ninguno cumple → feedback al LLM y reintenta (loop tipo *self-refine*).
- Restricciones estructurales (longitud, palabras prohibidas) → fáciles de validar con código.
- Restricciones semánticas (tono, intención) → otro LLM como juez.

**Rol del LLM:**
- (3) **Generador** principal.
- (2) **Evaluador** de restricciones blandas.

**Por qué es accesible:** muchos building blocks ya existen (constrained decoding, structured outputs). Riesgo: que sea "demasiado simple" si no incluyes algo no trivial. Para subir nivel: implementa **beam search constrained** o **tree-of-thoughts** para mejorar el cumplimiento.

**Dataset:** definir un conjunto de plantillas/escenarios (correos, mensajes de soporte, anuncios).

---

### Tema 9 — Construcción de rutas de aprendizaje

**Problema formal:** DAG de recursos de aprendizaje con (duración, dificultad, dependencias). Construir secuencia que cubra ciertos temas en menos de T horas, maximizando "utilidad".

**Modelado:**
- Es **scheduling con prerequisitos**.
- Muy parecido al Tema 3 pero con restricción dura de tiempo.
- Knapsack + topological order.

**Algoritmos:**
- DP sobre topological order.
- ILP con `pulp`: variables x_i = 1 si se incluye, restricciones de prerequisito y de tiempo total.

**Rol del LLM:**
- (1) **Extractor**: leer descripciones de recursos (curso, video, libro) y extraer (duración, prerequisitos implícitos, temas cubiertos).
- (2) **Evaluador**: utilidad/calidad de cada recurso para un objetivo dado.

**Dataset:** scrapear listados de recursos (reddit /r/learnprogramming, freecodecamp, github roadmap.sh).

**Por qué es bueno:** problema bien definido, ILP elegante, LLM aporta valor real (parsing y ranking).

---

### Tema 10 — Identificación de anomalías en secuencias

**Problema formal:** secuencia S = [e_1, ..., e_n] que debe cumplir reglas R. Encontrar D ⊆ S mínimo tal que S \ D cumple R.

**Modelado:**
- **Min-element-removal** para satisfacer un autómata.
- Versión: **minimum vertex cover** sobre grafo de conflictos.

**Algoritmos:**
- Si las reglas son regulares: programación dinámica sobre estados del autómata.
- Si son arbitrarias: branch & bound, aproximaciones greedy.

**Rol del LLM:**
- (1) **Extractor**: clasifica cada evento (de texto/log) en categorías que las reglas usan.
- (2) **Evaluador**: para reglas que son semánticas más que sintácticas, juzga cumplimiento.

**Dataset:** logs sintéticos, transacciones financieras simuladas, sesiones web.

**Similar al Tema 5**, pero más acotado (anomalías ⊂ inconsistencias).

---

## Mi recomendación

### Si te preguntas a mí: **Tema 9 (Rutas de aprendizaje)** o **Tema 6 (Segmentación óptima)**.

#### Por qué Tema 9
- Modelado **claro** (knapsack con prerequisitos).
- Algoritmo **estándar bien justificado** (ILP en `pulp`/`ortools`).
- LLM tiene **rol natural**: parsing + ranking. Sin LLM no podrías procesar las descripciones; con LLM se ve la utilidad real.
- **Dataset fácil** de conseguir (cualquier roadmap de aprendizaje público).
- **Material rico** para análisis: comparar rutas con/sin LLM, distintas configuraciones de tiempo.

#### Por qué Tema 6
- DP sobre cortes es **elegante** y de libro.
- Métrica clara: coherencia.
- Permite hablar de **eficiencia** (el truco de embeddings + LLM solo en zonas ambiguas).
- Datasets gratis abundantes.
- Riesgo medio.

### Si quieres lucirte: **Tema 7** (multi-objetivo) o **Tema 1** (impacto sanitario, tema de moda en IA aplicada).

### Si tienes poco tiempo: **Tema 8** (mensajes con restricciones).

### Evita si no tienes mucha experiencia: **Tema 5** (consistencia semántica), **Tema 4** (patrones sospechosos a definir).

---

## Plantilla de "Diseño del algoritmo" (para el informe)

Esto te van a pedir sí o sí. Estructura sugerida:

```
1. Definición formal del problema
   - Conjuntos, parámetros, variables, dominios
   - Restricciones (duras y blandas)
   - Función objetivo

2. Algoritmo principal
   - Tipo (exacto / heurístico / metaheurístico)
   - Pseudocódigo
   - Complejidad temporal y espacial
   - Garantías (óptimo, ε-aproximado, sin garantía)

3. Integración del LLM
   - En qué paso del algoritmo se invoca
   - Qué prompt se usa (incluir plantilla literal)
   - Qué se hace con la respuesta (parsing, validación, fallback)
   - Mecanismo de caché

4. Variantes implementadas (para comparar)
   - Variante A: solo algoritmo (baseline)
   - Variante B: algoritmo + LLM como heurística
   - Variante C: algoritmo + LLM como evaluador
```

---

## Metodología experimental

El profesor pide explícitamente **comparación entre configuraciones**. Diseño mínimo:

- **3 tamaños de instancia** (pequeño / mediano / grande). 5–10 instancias por tamaño.
- **Al menos 3 configuraciones** comparadas (ej. baseline sin LLM, baseline + LLM-evaluador, baseline + LLM-generador).
- **Métricas**:
  - Calidad de la solución (objetivo).
  - Tiempo de ejecución.
  - Número de llamadas al LLM (proxy de costo).
  - Métricas específicas del problema.
- **Reproducibilidad**: semilla fija, snapshots de respuestas del LLM en caché.
- **Tablas y gráficas**: barras comparativas, scatter plots de calidad vs tiempo.

---

## Checklist de entrega

### Código fuente

- [ ] Repositorio en GitHub.
- [ ] README con: descripción, instalación, ejemplos de uso, variables de entorno.
- [ ] `requirements.txt` o `pyproject.toml`.
- [ ] `.env.example` con keys ficticias.
- [ ] Implementación completa (sin `# TODO` sospechosos).
- [ ] **Dataset incluido** (en `data/` o instrucciones claras de descarga).
- [ ] **Configuración del LLM** clara: qué proveedor, qué modelo, parámetros (temperature, max_tokens), prompts en archivos legibles.
- [ ] Tests mínimos.
- [ ] Caché del LLM versionado (para reproducibilidad).

### Informe técnico

- [ ] Descripción del problema (intuición + formal).
- [ ] **Modelado formal**: variables, restricciones, función objetivo.
- [ ] Descripción del dataset y cómo se generó/obtuvo.
- [ ] Diseño del algoritmo (con pseudocódigo).
- [ ] **Rol del LLM** (qué patrón de los 5 usas).
- [ ] **Prompt(s)** literal usado, con explicación de decisiones.
- [ ] Metodología experimental.
- [ ] Resultados (tablas + gráficas).
- [ ] Análisis: cuándo funciona, cuándo falla.
- [ ] Limitaciones y mejoras futuras.
- [ ] Bibliografía mínima.

---

## Comparativa rápida

| Tema | Algoritmo | Rol LLM principal | Dataset fácil | Riesgo |
|------|-----------|-------------------|---------------|--------|
| 1 Casos clínicos | ILP / Knapsack | Extractor + Evaluador | Medio | Medio |
| 2 Resúmenes | Knapsack + orden | Evaluador | Fácil | Bajo |
| 3 Trayectoria | A* / planning | Interfaz + Evaluador | Medio | Medio |
| 4 Patrones sospechosos | CSP / FSM | Extractor + Evaluador | Medio | Alto |
| 5 Reparación inconsistencias | MaxSAT | Evaluador | Difícil | **Muy alto** |
| 6 Segmentación | DP | Evaluador | Fácil | Bajo |
| 7 Trayectorias alternativas | NSGA-II | Generador + Eval | Medio | Alto |
| 8 Mensajes con restricciones | Generate & test | Generador + Eval | Fácil | Bajo |
| 9 Rutas aprendizaje | ILP / DP | Extractor + Evaluador | Fácil | Bajo |
| 10 Anomalías | DP / set-cover | Extractor + Evaluador | Medio | Medio |

---

## Una observación final

El proyecto de **Eventos Discretos** (el otro PDF) y este de **IA** son completamente independientes (asignaturas distintas). Podrías intentar cosas como:
- Reusar el motor de Python entre ambos proyectos para ahorrar tiempo de setup.
- Si en Eventos Discretos eliges Kojo's Kitchen, te queda **mucho** tiempo para invertir aquí, donde realmente conviene esforzarse (más complejo, más nota).
- En IA, la calidad del **informe técnico** y el **diseño experimental** pesan tanto como el código. Empieza el informe **temprano**, no al final.
