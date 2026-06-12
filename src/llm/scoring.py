"""
Precálculo cacheado de relevancia y coherencia para el solver unificado.

Todas las llamadas al LLM ocurren aquí (fuera del bucle de beam search).
"""
from dataclasses import dataclass
from typing import List, Protocol

from ..problem import Fragment, SelectionProblem


class FragmentScorer(Protocol):
    def score_fragment(self, fragment: Fragment) -> float: ...

    def score_coherence(self, first_fragment: Fragment, second_fragment: Fragment) -> float: ...


@dataclass(frozen=True)
class ScoreMatrix:
    relevance: List[float]
    coherence: List[List[float]]

    @property
    def n(self) -> int:
        return len(self.relevance)

    def coherence_fn(self, i: int, j: int) -> float:
        return self.coherence[i][j]


def build_relevance_scores(
    problem: SelectionProblem,
    llm_client: FragmentScorer,
) -> List[float]:
    n = len(problem.fragments)
    scores: List[float] = []
    for index, fragment in enumerate(problem.fragments):
        print(f"  relevancia: fragmento {index + 1}/{n}")
        scores.append(llm_client.score_fragment(fragment))
    return scores


def build_coherence_matrix(
    problem: SelectionProblem,
    llm_client: FragmentScorer,
) -> List[List[float]]:
    n = len(problem.fragments)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            print(f"  coherencia: par ({i},{j})")
            matrix[i][j] = llm_client.score_coherence(
                problem.fragments[i],
                problem.fragments[j],
            )
    return matrix


def build_llm_scores(problem: SelectionProblem, llm_client: FragmentScorer) -> ScoreMatrix:
    """Precalcula relevance[n] y coherence[n×n] vía LLM (caché en el cliente)."""
    if not problem.fragments:
        return ScoreMatrix(relevance=[], coherence=[])

    print(f"Precálculo LLM: {len(problem.fragments)} fragmentos")
    relevance = build_relevance_scores(problem, llm_client)
    coherence = build_coherence_matrix(problem, llm_client)
    return ScoreMatrix(relevance=relevance, coherence=coherence)


def build_temporal_coherence_matrix(fragments: List[Fragment]) -> List[List[float]]:
    """Proxy de coherencia sin LLM: favorece pares en orden cronológico del video."""
    n = len(fragments)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            delta = fragments[j].start_time - fragments[i].start_time
            if delta > 0:
                matrix[i][j] = max(0.0, 1.0 - delta / 40.0)
            else:
                matrix[i][j] = 0.1
    return matrix


def build_baseline_scores(problem: SelectionProblem) -> ScoreMatrix:
    """Scores proxy: relevancia uniforme + coherencia temporal por start_time."""
    n = len(problem.fragments)
    if n == 0:
        return ScoreMatrix(relevance=[], coherence=[])

    relevance = [1.0] * n
    coherence = build_temporal_coherence_matrix(problem.fragments)
    return ScoreMatrix(relevance=relevance, coherence=coherence)
