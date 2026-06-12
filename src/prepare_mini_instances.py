"""Genera instancias mini_* y dur_* a partir de video_*.json."""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _slice_fragments_by_duration(
    fragments: List[Dict[str, Any]],
    target_minutes: float,
) -> Tuple[List[Dict[str, Any]], float]:
    target_seconds = target_minutes * 60.0
    selected: List[Dict[str, Any]] = []
    accumulated = 0.0
    for fragment in fragments:
        selected.append(fragment)
        accumulated += float(fragment["duration"])
        if accumulated >= target_seconds:
            break
    if not selected:
        raise ValueError("La instancia fuente no contiene fragmentos.")
    return selected, accumulated


def build_duration_instance(source: Dict[str, Any], target_minutes: float) -> Dict[str, Any]:
    fragments, _ = _slice_fragments_by_duration(source.get("fragments", []), target_minutes)
    total_duration = sum(float(frag["duration"]) for frag in fragments)
    return {
        "max_duration": round(total_duration * 0.25, 2),
        "fragments": fragments,
    }


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


def prepare_duration_instance(
    source_path: Path,
    output_path: Path,
    target_minutes: float,
) -> None:
    with source_path.open("r", encoding="utf-8") as handle:
        source = json.load(handle)

    instance = build_duration_instance(source, target_minutes)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(instance, handle, indent=2, ensure_ascii=False)

    total_duration = sum(float(frag["duration"]) for frag in instance["fragments"])
    print(
        f"{output_path.name}: {len(instance['fragments'])} fragmentos, "
        f"duración acumulada={round(total_duration, 1)}s (~{round(total_duration / 60, 1)} min), "
        f"max_duration={instance['max_duration']}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera mini_video_* (primeros N fragmentos) o dur_*min (corte por duración)."
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
    parser.add_argument(
        "--target-minutes",
        nargs="*",
        type=float,
        help="Genera dur_<N>min.json con fragmentos hasta alcanzar N minutos de video acumulado",
    )
    parser.add_argument(
        "--source-video",
        type=int,
        default=2,
        help="Índice del video fuente para cortes dur_* (default: 2)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    instances_dir = root / "data" / "instances"

    if args.target_minutes:
        source_path = instances_dir / f"video_{args.source_video}.json"
        if not source_path.exists():
            print(f"Error: no existe {source_path.name}")
            return
        for minutes in args.target_minutes:
            label = int(minutes) if minutes == int(minutes) else minutes
            output_path = instances_dir / f"dur_{label}min.json"
            prepare_duration_instance(source_path, output_path, minutes)
        return

    for video_id in args.videos:
        source_path = instances_dir / f"video_{video_id}.json"
        if not source_path.exists():
            print(f"Omitido: no existe {source_path.name}")
            continue

        output_path = instances_dir / f"mini_video_{video_id}.json"
        prepare_mini_instance(source_path, output_path, args.n)


if __name__ == "__main__":
    main()
