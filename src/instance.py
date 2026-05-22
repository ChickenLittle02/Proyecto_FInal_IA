"""
Carga y representación de instancias de fragmentos de video.
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from .problem import Fragment, SelectionProblem


def load_instance_file(path: str) -> SelectionProblem:
    path_obj = Path(path)
    with path_obj.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    fragments_data = data.get("fragments", [])
    fragments: List[Fragment] = []
    for item in fragments_data:
        fragments.append(
            Fragment(
                id=str(item.get("id", "")),
                text=str(item.get("text", "")),
                duration=float(item.get("duration", 0.0)),
                start_time=float(item.get("start_time", 0.0)),
                end_time=float(item.get("end_time", 0.0)),
                metadata=item.get("metadata"),
            )
        )

    max_duration = float(data.get("max_duration", 60.0))
    return SelectionProblem(fragments=fragments, max_duration=max_duration)


def save_instance_file(path: str, problem: SelectionProblem) -> None:
    path_obj = Path(path)
    data: Dict[str, Any] = {
        "max_duration": problem.max_duration,
        "fragments": [
            {
                "id": frag.id,
                "text": frag.text,
                "duration": frag.duration,
                "start_time": frag.start_time,
                "end_time": frag.end_time,
                "metadata": frag.metadata,
            }
            for frag in problem.fragments
        ],
    }
    with path_obj.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
