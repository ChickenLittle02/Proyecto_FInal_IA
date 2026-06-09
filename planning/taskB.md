# Checklist de Tareas — Paso B: Conectar un Cliente LLM Real (Gemini)

- `[x]` Configurar `.gitignore` para ignorar `.env` y `.llm_cache.json`
- `[ ]` Crear plantilla `.env.example`
- `[ ]` Instalar dependencias en `requirements.txt` (`google-generativeai` y `python-dotenv`)
- `[ ]` Modificar `src/llm/client.py` para conectar con la API de Gemini
- `[ ]` Mejorar robustez de parseo de puntuaciones en `src/llm/client.py` usando regex
- `[ ]` Validar llamadas reales y funcionamiento del sistema de caché local
