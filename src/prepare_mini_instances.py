"""Genera instancias mini_* a partir de video_*.json (primeros N fragmentos consecutivos)."""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def build_mini_instance(source: Dict[str, Any], n_fragments: int) -> Dict[str, Any]:
    fragments: List[Dict[str, Any]] = source.get("fragments", [])[:n_fragments]
    if not fragments:
        raise ValueError("La instancia fuente no contiene fragmentos.")

    total_duration = sum(float(frag["duration"]) for frag in fragments)
    max_duration = round(total_duration * 0.25, 2)

    return {
        "max_duration": max_duration,
        "fragments": fragments,
    }


def prepare_mini_instance(
    source_path: Path,
    output_path: Path,
    n_fragments: int,
) -> None:
    with source_path.open("r", encoding="utf-8") as handle:
        source = json.load(handle)

    mini = build_mini_instance(source, n_fragments)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(mini, handle, indent=2, ensure_ascii=False)

    print(
        f"{output_path.name}: {len(mini['fragments'])} fragmentos, "
        f"duración total={round(total_duration := sum(f['duration'] for f in mini['fragments']), 1)}s, "
        f"max_duration={mini['max_duration']}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae los primeros N fragmentos de video_*.json y guarda mini_video_*.json."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Número de fragmentos consecutivos a conservar (default: 10)",
    )
    parser.add_argument(
        "--videos",
        nargs="*",
        type=int,
        default=[1, 2, 3, 4],
        help="Índices de video a procesar (default: 1 2 3 4)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    instances_dir = root / "data" / "instances"

    for video_id in args.videos:
        source_path = instances_dir / f"video_{video_id}.json"
        if not source_path.exists():
            print(f"Omitido: no existe {source_path.name}")
            continue

        output_path = instances_dir / f"mini_video_{video_id}.json"
        prepare_mini_instance(source_path, output_path, args.n)


if __name__ == "__main__":
    main()
