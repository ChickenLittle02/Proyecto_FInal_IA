"""
Definición formal del problema de selección y ordenación de fragmentos.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

@dataclass
class Fragment:
    id: str
    text: str
    duration: float
    start_time: float
    end_time: float
    metadata: Optional[Dict[str, Any]] = None

    @property
    def length(self) -> float:
        return self.duration


@dataclass
class SelectionProblem:
    fragments: List[Fragment]
    max_duration: float

    def validate_order(self) -> bool:
        for i in range(1, len(self.fragments)):
            if self.fragments[i].start_time < self.fragments[i - 1].start_time:
                return False
        return True

    def is_valid_selection(self, selected_indices: Sequence[int]) -> bool:
        """Selección válida como subsecuencia del array de entrada (índices crecientes)."""
        if any(i < 0 or i >= len(self.fragments) for i in selected_indices):
            return False
        if list(selected_indices) != sorted(selected_indices):
            return False
        total_duration = sum(self.fragments[i].duration for i in selected_indices)
        return total_duration <= self.max_duration

    def is_valid_ordered_selection(self, order: Sequence[int]) -> bool:
        """Selección válida con orden explícito de reproducción (reordenación permitida)."""
        if any(i < 0 or i >= len(self.fragments) for i in order):
            return False
        if len(order) != len(set(order)):
            return False
        total_duration = sum(self.fragments[i].duration for i in order)
        return total_duration <= self.max_duration

    @staticmethod
    def objective_score(
        relevance_scores: Sequence[float],
        coherence_scores: Sequence[float],
        selected_indices: Sequence[int],
        coherence_weight: float = 0.5,
    ) -> float:
        if not selected_indices:
            return 0.0
        relevance_sum = sum(relevance_scores[i] for i in selected_indices)
        coherence_sum = 0.0
        if len(selected_indices) >= 2:
            for first, second in zip(selected_indices, selected_indices[1:]):
                coherence_sum += coherence_scores[first, second]
        return relevance_sum * (1.0 - coherence_weight) + coherence_sum * coherence_weight

    def selected_fragments(self, selected_indices: Sequence[int]) -> List[Fragment]:
        return [self.fragments[i] for i in selected_indices]

    def summary_duration(self, selected_indices: Sequence[int]) -> float:
        return sum(self.fragments[i].duration for i in selected_indices)

    def summary_text(self, selected_indices: Sequence[int]) -> str:
        return "\n\n".join(self.fragments[i].text.strip() for i in selected_indices)
