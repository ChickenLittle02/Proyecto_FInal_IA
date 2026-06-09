# Proyecto Final IA - Selección y ordenación de fragmentos

Este repositorio contiene una base inicial para el proyecto final de IA sobre selección de fragmentos de video educativo.

## Estructura creada
- `src/problem.py` — definición formal del problema y representación de fragmentos.
- `src/instance.py` — carga y guardado de instancias en JSON.
- `src/solver/baseline.py` — solver clásico con selección ordenada y DP.
- `src/solver/llm_assisted.py` — solver asistido por LLM con puntuación de relevancia y coherencia.
- `src/llm/client.py` — wrapper de configuración de LLM.
- `src/llm/prompts.py` — prompts base para evaluación de fragmentos.
- `src/llm/cache.py` — caché local para respuestas de LLM.

## Primeros pasos (día 1)
1. Definir claramente la estructura de datos y el problema formal.
2. Completar la implementación del solver clásico.
3. Preparar datos de prueba pequeños en `data/instances/`.
4. Conectar la implementación LLM real en `src/llm/client.py`.

## Instancia de ejemplo
Se añadió `data/instances/example_instance.json` con una secuencia de 5 fragmentos de un video educativo. El ejemplo usa una duración máxima de `45.0` segundos, de modo que el solver debe seleccionar los fragmentos más relevantes y coherentes dentro del límite.

Para cargar la instancia y ejecutar un ejemplo rápido con el solver clásico:

```bash
python src/run_example.py
```

## Configuración de la API (Gemini)
Para poder utilizar el solver asistido por LLM, debes configurar tu clave de API de Gemini:

1. Ve a [Google AI Studio](https://aistudio.google.com/) y genera una clave de API gratuita (puedes iniciar sesión con tu cuenta de Gmail).
2. Crea un archivo llamado `.env` en la raíz de este proyecto (está configurado en `.gitignore` para que tus claves nunca se suban públicamente al repositorio).
3. Añade el siguiente contenido al archivo `.env`, reemplazando el valor con la clave de API obtenida:

```env
GEMINI_API_KEY=tu_clave_api_de_gemini_aqui
LLM_MODEL=gemini-1.5-flash
LLM_PROVIDER=gemini
```

## Ejecución de ejemplos
Para ejecutar una prueba clásica con la instancia sintética pequeña:
```bash
python src/run_example.py
```

Para probar con una instancia real generada a partir de los subtítulos de los videos (por ejemplo, el video 3):
```bash
python src/run_example.py video_3.json
```

## Configuración del entorno
- Python 3.10+
- Instalar dependencias con:
  ```bash
  pip install -r requirements.txt
  ```
