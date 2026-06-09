Viewed Abstract.txt

I will first look at the contents of the workspace directory to understand what files and directories have been created so far. This will help me analyze which parts of the work plan in [plan_trabajo.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/plan_trabajo.md) are already implemented.

Listed directory Proyecto_FInal_IA

I will read the contents of [plan_trabajo.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/plan_trabajo.md) to understand the current work plan. I will also check the `src` and `data` directories to see what has been implemented so far.

Viewed plan_trabajo.md:1-146

I will inspect the directories `src`, `data`, and `videos` to see what files have been created and what their current implementation status is.

Listed directory src

I will now list the contents of the `src/solver` and `src/llm` directories.

Listed directory solver

I will list the contents of the `src/llm` directory.

Listed directory llm

I will list the contents of the `data` and `videos` directories.

Listed directory data

I will list the contents of the `data/instances` directory.

Listed directory instances

I will list the contents of the `videos` directory.

Listed directory videos

I will list the contents of the `videos/1` directory.

Listed directory 1

I will read [README.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/README.md) to see what is documented about the current state of the project.

Viewed README.md:1-37

I will read [src/run_example.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/run_example.py) to see how the example is run.

Viewed run_example.py:1-36

I will read the core files: [src/problem.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/problem.py) and [src/instance.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/instance.py) to check the problem formulation and loading logic.

Viewed problem.py:1-64

I will read [src/instance.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/instance.py) and [src/solver/baseline.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/solver/baseline.py).

Viewed instance.py:1-52

I will read [src/solver/baseline.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/solver/baseline.py).

Viewed baseline.py:1-61

I will read [src/solver/llm_assisted.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/solver/llm_assisted.py).

Viewed llm_assisted.py:1-45

I will read [src/llm/client.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/llm/client.py) to see how the LLM calls are implemented.

Viewed client.py:1-53

I will read [src/llm/prompts.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/llm/prompts.py) and [src/llm/cache.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/llm/cache.py).

Viewed prompts.py:1-26

I will read [src/llm/cache.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/llm/cache.py).

Viewed cache.py:1-36

I will view [requirements.txt](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/requirements.txt) to see what dependencies are declared.

Viewed requirements.txt:1-5

I will check what is inside the rest of the subdirectories in `videos` (`videos/2`, `videos/3`, `videos/4`).

Listed directory 2

I will check `videos/3` and `videos/4` directories as well.

Listed directory 3

I will list the contents of `videos/4`.

Listed directory 4

I will check the content of [analisis-proyecto-final-ia.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/analisis-proyecto-final-ia.md) to see if there is any analysis already documented that we can reuse or build upon.

Viewed analisis-proyecto-final-ia.md:1-571

I will view the [data/instances/example_instance.json](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/data/instances/example_instance.json) file to see how a dataset instance is structured. This will help determine if the videos in the `videos` folder have already been processed into JSON instances.

Viewed example_instance.json:1-56

I will run the example script [src/run_example.py](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/src/run_example.py) to check if the current implementation of the classical solver works correctly.

Ran command: `python src/run_example.py`

I will update [plan_trabajo.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/plan_trabajo.md) to convert the tasks list into checkboxes showing the current status (completed `[x]`, in progress `[/]`, or pending `[ ]`). This will give a clear view of where we are and what remains to be done.

Edited plan_trabajo.md

He analizado el estado actual del repositorio y he actualizado el archivo [plan_trabajo.md](file:///c:/Users/marti/OneDrive/Documents/ia/Proyecto_FInal_IA/plan_trabajo.md) para reflejar detalladamente el progreso mediante casillas de verificación (`[x]` para completado, `[/]` para parcial/en progreso y `[ ]` para pendiente).

A continuación te detallo el resumen de lo que ya está hecho y los siguientes pasos recomendados para continuar completándolo:

---

### 1. ¿Qué está hecho ya en el proyecto? `[x]`

* **Definición Formal del Problema (`src/problem.py`):** Estructura del modelo con representación de fragmentos (`Fragment`), restricciones de longitud (`max_duration`), función de validación de orden cronológico y función objetivo de maximización (relevancia + coherencia).
* **Carga e Serialización de Instancias (`src/instance.py`):** Funciones para guardar y cargar archivos JSON de instancias en `data/instances/`.
* **Algoritmos Clásicos / Baseline (`src/solver/baseline.py`):** 
  * Un solver exacto basado en programación dinámica (`ordered_knapsack_dp`) que resuelve el problema de la mochila ordenando cronológicamente los fragmentos.
  * Una heurística ávida (`greedy_by_score`) basada en la relación puntuación/duración para instancias grandes.
* **Componentes Base del LLM (`src/llm/`):**
  * **Caché en disco (`src/llm/cache.py`):** Implementada para almacenar respuestas previas y evitar re-evaluaciones costosas.
  * **Prompts iniciales (`src/llm/prompts.py`):** Definidos los prompts de relevancia y coherencia.
  * **Esqueleto del cliente (`src/llm/client.py`):** Estructurado para invocar el modelo, parsear puntuaciones y cachear, aunque actualmente tiene un método dummy que retorna `"0.0"`.
* **Datos de Prueba Iniciales:** Archivo `data/instances/example_instance.json` con 5 fragmentos sintéticos para pruebas rápidas.

---

### 2. ¿Qué deberíamos hacer ahora para seguir terminándolo? (Siguientes pasos)

#### Paso A: Procesar y estructurar el Dataset Real `[/]`
* **Situación:** Tienes carpetas en `videos/` (`1`, `2`, `3`, `4`) con archivos de subtítulos `.srt` reales, pero no están convertidos al formato JSON que lee el sistema.
* **Acción:** Escribir un script (por ejemplo, `src/prepare_dataset.py`) que parsee estos archivos `.srt` agrupando líneas de subtítulos en fragmentos lógicos (de, por ejemplo, 10 a 30 segundos) con sus respectivos tiempos de inicio, fin y texto consolidado, guardando el resultado en `data/instances/` como nuevos archivos de prueba reales.

#### Paso B: Conectar un cliente LLM real `[/]`
* **Situación:** El cliente LLM actual en `src/llm/client.py` (`_invoke_model`) es un placeholder que retorna `"0.0"`.
* **Acción:** Decidir qué API/proveedor utilizar.
  * *Recomendación:* Usar la API de **Google Gemini** (gratuita) o **OpenAI** (con `gpt-4o-mini`, muy económica). Podemos instalar la dependencia necesaria (como `google-generativeai` u `openai`), actualizar el archivo `requirements.txt` y programar la llamada real en `src/llm/client.py` leyendo la API key desde un archivo `.env`.

#### Paso C: Refinar el Solver Asistido por LLM `[/]`
* **Situación:** En `src/solver/llm_assisted.py`, la coherencia se calcula combinando estáticamente la relevancia de un fragmento $i$ con la coherencia entre $i$ y el fragmento $i+1$ de la secuencia original. Si el algoritmo decide omitir fragmentos (por ejemplo, seleccionar el 1 y luego el 3), la coherencia real debería evaluarse dinámicamente sobre la transición del salto ($1 \rightarrow 3$), no sobre la transición original ($1 \rightarrow 2$).
* **Acción:** Rediseñar la formulación del DP en `ordered_knapsack_dp` o refinar la integración en `llm_assisted.py` para calcular dinámicamente las transiciones entre saltos arbitrarios de fragmentos seleccionados.

#### Paso D: Diseñar y Ejecutar el Plan Experimental `[ ]`
* **Acción:** Crear un script de pruebas/experimentos (`src/run_experiments.py`) para correr el solver clásico vs. asistido por LLM en las nuevas instancias reales, medir tiempos de ejecución, calidad de resumen final (coherencia/cobertura estimada por el LLM) y cantidad de llamadas a la API (ahorro por caché). Guardar los resultados en archivos CSV.

#### Paso E: Redactar el Informe Técnico y Documentación `[ ]`
* **Acción:** Crear la carpeta `informe/` y documentar formalmente el modelado, los algoritmos utilizados, los prompts de LLM y el análisis cualitativo/cuantitativo de los experimentos realizados (incluyendo gráficas/tablas).

---

¿Cuál de estos pasos te gustaría que abordemos primero? Puedo ayudarte a escribir el script para procesar los subtítulos `.srt` en JSON o configurar la conexión real con el LLM.