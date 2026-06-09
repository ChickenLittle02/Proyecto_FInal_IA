# Plan de trabajo - Proyecto Final IA (Tema 2)

## Contexto clave
- Tema escogido: **Construcción de resúmenes como selección óptima de segmentos**
- El sistema debe recibir fragmentos de video educativo con transcripciones.
- El objetivo es seleccionar y ordenar un subconjunto de fragmentos que represente bien el contenido bajo una longitud límite.
- El LLM debe evaluar **coherencia** y **relevancia**, y el sistema debe incluir un componente algorítmico real.
- Tener en cuenta los capítulos 1-6 de `temas-simulacion.pdf` cuando aporten al proyecto:
  - capítulo 1: modelar el sistema, sus entradas/salidas y el ambiente de decisión.
  - capítulo 2: si generas datos sintéticos, usar distribuciones y procesos aleatorios para crear instancias variadas.
  - capítulo 3: aplicar ideas de simulación de eventos discretos para estructurar la evaluación secuencial de fragmentos.
  - capítulo 4: usar análisis estadístico para comparar variantes y documentar resultados.
  - capítulo 5: usar lógica difusa para modelar grados de relevancia/coherencia y justificar una evaluación no-binaria.
  - capítulo 6: describir el sistema como un agente que percibe fragmentos y decide la selección y ordenación.

## Objetivo del plan
Terminar el sistema completo en una semana con:
- [x] dataset / instancias
- [/] implementación algorítmica + versión asistida por LLM
- [/] configuración de LLM reproducible
- [ ] análisis experimental
- [ ] informe técnico
- [ ] instrucciones de ejecución

---

## Día 1 — Definición y diseño
- [x] Definir el problema formal:
  - [x] variables: fragmentos `s_i`, longitud `l_i`, selección `x_i \in {0,1}`
  - [x] restricción: suma de longitudes ≤ límite
  - [x] objetivo: maximizar relevancia + coherencia del resumen
  - [x] orden preservado según el video original
- [x] Decidir el modelo algorítmico:
  - [x] variante de **DP / knapsack con orden** para seleccionar fragmentos
  - [x] o “subset selection con penalty de transición”
- [x] Anotar claramente qué hace el algoritmo clásico vs el LLM
- [x] Escribir un esquema de la estructura del proyecto:
  - [x] `src/problem.py`, `src/instance.py`, `src/solver/baseline.py`, `src/solver/llm_assisted.py`, `src/llm/`

## Día 2 — Dataset e instancias
- [x] Recolectar o generar dataset:
  - [x] Usar 2–3 videos reales (Procesados los subtítulos `.srt` de las 4 carpetas de videos reales y segmentados en archivos JSON en `data/instances/video_*.json`)
  - [x] Extraer fragmentos cortos + transcripciones
  - [x] Crear instancias en JSON con: texto, duración, posición (start_time, end_time)
- [x] Crear instancias de prueba razonables:
  - [x] videos de 5-10 fragmentos (`example_instance.json`)
  - [x] casos con segmentos muy relevantes y segmentos irrelevantes
- [x] Implementar loader de datos:
  - [x] `data/instances/`
  - [x] función para leer fragmentos y longitudes (`src/instance.py`)
- [ ] Guardar el proceso de generación en el informe (Se documentará en el informe final)

## Día 3 — LLM + prompts + caché
- [/] Elegir proveedor / modo de desarrollo:
  - [x] local (Ollama) o API (OpenAI / Anthropic / Gemini) -> Estructura preparada en `src/llm/client.py`
  - [ ] Integrar el cliente real del proveedor elegido (actualmente `_invoke_model` es un placeholder que retorna `"0.0"`)
- [/] Crear wrapper de LLM:
  - [x] env var para modelo y API key
  - [x] `src/llm/client.py` (Falta integrar la llamada real de API)
  - [x] `src/llm/prompts.py` (Prompts base definidos)
  - [x] `src/llm/cache.py` (Caché local en disco implementada)
- [/] Diseñar prompts claros para:
  - [x] puntuar relevancia de cada fragmento
  - [x] puntuar coherencia entre dos fragmentos consecutivos
  - [ ] evaluar la coherencia final del resumen (opcional / refinar)
- [x] Implementar caché de respuestas para no gastar tokens en cada iteración

## Día 4 — Algoritmos y primera integración
- [x] Implementar algoritmo base sin LLM (ej. DP y greedy en `src/solver/baseline.py`)
- [x] Implementar solver real:
  - [x] DP exacto / knapsack con orden (`src/solver/baseline.py`)
- [/] Implementar solver asistido por LLM:
  - [x] usar scores de relevancia LLM para cada fragmento
  - [/] usar score de transición para ordenar / validar (Parcial: se combina relevancia con la transición del fragmento siguiente, pero no soporta transiciones dinámicas entre saltos arbitrarios de fragmentos no consecutivos si se omiten fragmentos intermedios. Se podría refinar el DP para esto)
- [ ] Probar flujo completo en las instancias reales y sintéticas creadas con el LLM real activo

## Día 5 — Experimentos y análisis
- [ ] Ejecutar comparaciones:
  - [ ] baseline sin LLM vs. LLM-asistido
  - [ ] distintas formas de usar al LLM (relevancia solo / relevancia+coherencia)
  - [ ] posiblemente distintos prompts
- [ ] Recoger métricas:
  - [ ] longitud usada
  - [ ] cobertura de contenido
  - [ ] coherencia estimada por LLM
  - [ ] comparaciones cualitativas
- [ ] Guardar resultados en CSV y tablas
- [ ] Generar al menos un gráfico simple o tabla de comparación

## Día 6 — Documentación e informe
- [ ] Escribir informe técnico con estas secciones:
  1. descripción del problema
  2. modelado formal (con referencias a los capítulos de `temas-simulacion.pdf` si aplica, como lógica difusa para grados de relevancia, etc.)
  3. descripción de dataset utilizado
  4. diseño del algoritmo
  5. rol del LLM
  6. metodología experimental
  7. resultados y análisis
  8. limitaciones y mejoras
- [ ] Redactar README / `instructions.md` final con instrucciones detalladas de ejecución
- [x] Incluir `requirements.txt` (creado, pero requiere agregar paquetes necesarios del LLM elegido, ej: `google-generativeai` u `openai`)
- [ ] Crear `.env.example`
- [ ] Ejemplos de salida

## Día 7 — Revisión final y cierre
- [ ] Probar todo de punta a punta:
  - [ ] carga de datos
  - [ ] solver base
  - [ ] solver LLM
  - [ ] generación de resultados
- [ ] Revisar que:
  - [ ] el código sea reproducible
  - [ ] el informe explique el rol del LLM claramente
  - [ ] el sistema NO dependa de llamadas LLM innecesarias (verificar funcionamiento de caché)
- [ ] Ajustar detalles finales
- [ ] Empaquetar entrega:
  - [ ] `src/`
  - [ ] `data/`
  - [ ] `README.md`
  - [ ] `informe/`
  - [ ] `requirements.txt`
  - [ ] `.env.example`

---

## Enfoque recomendado para la entrega
- Entregar código fuente completo
- Entregar dataset / instancias
- Entregar instrucciones de ejecución
- Entregar configuración de LLM
- Entregar informe técnico

## Puntos clave para la nota
- Usa el LLM como **evaluador de coherencia** y **relevancia**, no como generador único.
- Mantén un solver clásico visible: por ejemplo, DP + selección ordenada.
- Documenta bien el contraste: `sin LLM` vs `con LLM` y `relevancia` vs `coherencia`.
- Explica por qué tu sistema cumple el requisito del tema 2: seleccionar y ordenar fragmentos.