import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SubtitleBlock:
    index: int
    start_time: float
    end_time: float
    text: str


def srt_time_to_seconds(time_str: str) -> float:
    """Convierte un timestamp SRT (HH:MM:SS,mmm) a segundos."""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def clean_subtitle_text(text: str) -> str:
    """Elimina etiquetas no verbales como [Música], (Risas) y limpia espacios."""
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_srt(srt_content: str) -> List[SubtitleBlock]:
    """Parsea el contenido de un archivo SRT en una lista de bloques."""
    # Normalizar saltos de línea a estilo UNIX
    content = srt_content.replace("\r\n", "\n")
    blocks_raw = content.strip().split("\n\n")

    blocks: List[SubtitleBlock] = []
    for raw in blocks_raw:
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        if len(lines) < 3:
            continue
        try:
            # Línea 1: índice
            idx = int(lines[0])
            # Línea 2: rango de tiempo (ej: 00:00:00,400 --> 00:00:13,000)
            time_line = lines[1]
            if "-->" not in time_line:
                continue
            start_str, end_str = time_line.split("-->")
            start_time = srt_time_to_seconds(start_str.strip())
            end_time = srt_time_to_seconds(end_str.strip())

            # Línea 3 en adelante: texto de subtítulo
            text_lines = " ".join(lines[2:])
            clean_text = clean_subtitle_text(text_lines)

            # Omitir subtítulos vacíos (ej. solo decían [Música])
            if not clean_text:
                continue

            blocks.append(
                SubtitleBlock(
                    index=idx,
                    start_time=start_time,
                    end_time=end_time,
                    text=clean_text,
                )
            )
        except Exception:
            # Omitir bloques con errores de parseo
            continue

    return sorted(blocks, key=lambda b: b.start_time)


def group_subtitles(
    blocks: List[SubtitleBlock], target_duration: float = 20.0
) -> List[Dict[str, Any]]:
    """Agrupa bloques de subtítulos cortos en segmentos lógicos más grandes."""
    if not blocks:
        return []

    raw_groups: List[List[SubtitleBlock]] = []
    current_group: List[SubtitleBlock] = []

    for block in blocks:
        if not current_group:
            current_group.append(block)
            continue

        group_start = current_group[0].start_time
        group_duration = block.end_time - group_start

        # Si añadir el bloque supera el límite máximo de 30 segundos, cerramos el grupo actual
        if group_duration > 30.0:
            raw_groups.append(current_group)
            current_group = [block]
        else:
            current_group.append(block)
            # Si se alcanza el target_duration (20s) y termina en fin de oración,
            # o si supera el límite suave de 25s, cerramos el grupo.
            ends_with_sentence = block.text.endswith((".", "?", "!", '"', "»"))
            if (
                group_duration >= target_duration and ends_with_sentence
            ) or group_duration >= 25.0:
                raw_groups.append(current_group)
                current_group = []

    if current_group:
        raw_groups.append(current_group)

    # Heurística: Si el último grupo es muy corto (< 8s), lo fusionamos con el penúltimo
    if len(raw_groups) > 1:
        last_group = raw_groups[-1]
        last_duration = last_group[-1].end_time - last_group[0].start_time
        if last_duration < 8.0:
            raw_groups[-2].extend(raw_groups.pop())

    # Formatear a diccionario de fragmentos
    fragments: List[Dict[str, Any]] = []
    for idx, group in enumerate(raw_groups):
        start_time = group[0].start_time
        end_time = group[-1].end_time
        duration = round(end_time - start_time, 2)
        text = " ".join(b.text for b in group)
        text = re.sub(r"\s+", " ", text).strip()

        fragments.append(
            {
                "id": str(idx + 1),
                "text": text,
                "duration": duration,
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "metadata": {"topic": "segmento_educativo"},
            }
        )

    return fragments


def process_video_directory(video_dir: Path, output_dir: Path) -> Optional[Path]:
    """Busca un archivo .srt en el directorio del video y lo convierte a JSON."""
    # Buscar el primer archivo .srt en la carpeta
    srt_files = list(video_dir.glob("*.srt"))
    if not srt_files:
        print(f"No se encontró ningún archivo .srt en: {video_dir}")
        return None

    srt_path = srt_files[0]
    print(f"Procesando: {srt_path.name}")

    try:
        with srt_path.open("r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback por si acaso tiene codificación diferente (ej. CP1252 o UTF-8-BOM)
        with srt_path.open("r", encoding="utf-8-sig", errors="ignore") as f:
            content = f.read()

    blocks = parse_srt(content)
    fragments = group_subtitles(blocks)

    if not fragments:
        print(f"No se generaron fragmentos válidos para: {srt_path.name}")
        return None

    # Calcular la duración total de la secuencia
    total_duration = sum(frag["duration"] for frag in fragments)
    # Límite del resumen: 25% de la duración total
    max_duration = round(total_duration * 0.25, 2)

    instance_data = {
        "max_duration": max_duration,
        "fragments": fragments,
    }

    # Guardar en data/instances/
    output_filename = f"video_{video_dir.name}.json"
    output_path = output_dir / output_filename
    output_dir.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(instance_data, f, indent=2, ensure_ascii=False)

    print(
        f"Instancia guardada en: {output_path} (Fragmentos: {len(fragments)}, Duración Total: {round(total_duration, 1)}s, Resumen Máx: {max_duration}s)"
    )
    return output_path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    videos_dir = root / "videos"
    output_dir = root / "data" / "instances"

    if not videos_dir.exists():
        print(f"Error: El directorio de videos no existe en {videos_dir}")
        return

    # Buscar subdirectorios numéricos o cualquier subdirectorio en videos/
    video_dirs = [d for d in videos_dir.iterdir() if d.is_dir()]
    # Ordenar numéricamente si es posible
    video_dirs.sort(key=lambda d: int(d.name) if d.name.isdigit() else d.name)

    print(f"Encontrados {len(video_dirs)} directorios de videos en {videos_dir}")

    processed_count = 0
    for v_dir in video_dirs:
        res = process_video_directory(v_dir, output_dir)
        if res:
            processed_count += 1

    print(f"\nProceso finalizado. Se crearon {processed_count} instancias en {output_dir}")


if __name__ == "__main__":
    main()
