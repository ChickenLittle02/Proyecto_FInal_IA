"""Prueba generación de notas cualitativas sin llamadas LLM."""
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.experiments.notes import append_block_notes, infer_qualitative_phrase


def test_infer_irrelevant_middle() -> None:
    by_solver = {
        "baseline_beam": {"selected_indices": "[0, 1, 2, 3, 4]"},
        "llm_beam": {"selected_indices": "[0, 1, 3, 4]"},
    }
    phrase = infer_qualitative_phrase("bench_irrelevant_middle.json", by_solver)
    assert "irrelevante" in phrase.lower() or "recorta" in phrase.lower()


def test_append_block_notes_writes_section() -> None:
    csv_content = (
        "instance,solver,n_fragments,n_selected,max_duration,duration_used,"
        "duration_utilization,fragment_coverage,duration_coverage,solver_score,"
        "mean_relevance,mean_coherence,objective_score,selected_indices\n"
        "example_instance.json,baseline_beam,5,5,45,45,1.0,1.0,1.0,5.0,0.48,0.0,1.8,\"[0, 1, 2, 3, 4]\"\n"
        "example_instance.json,llm_beam,5,4,45,38,0.844,0.8,0.844,2.55,0.6,0.2,1.95,\"[0, 1, 2, 4]\"\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "part.csv"
        notes_path = tmp_path / "notas.md"
        csv_path.write_text(csv_content, encoding="utf-8")
        notes_path.write_text("# Notas\n", encoding="utf-8")
        append_block_notes(notes_path, csv_path, block_label="Bloque test")
        text = notes_path.read_text(encoding="utf-8")
        assert "Bloque test" in text
        assert "example_instance.json" in text
        assert "objective_score" in text


def main() -> None:
    test_infer_irrelevant_middle()
    test_append_block_notes_writes_section()
    print("[ÉXITO] Notas de experimentos validadas.")


if __name__ == "__main__":
    main()
