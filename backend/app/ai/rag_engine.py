"""
Graph-RAG Engine — M4.2.

Implements the Graph-Retrieval Augmented Generation pipeline for adaptive
question selection. Combines three retrieval strategies (ADR-004):

  1. Graph Traversal  — use NetworkX to find neighbor skills via prerequisite edges
  2. Vector Search    — query ChromaDB for semantically similar questions
  3. LLM Fallback     — generate a brand-new question via Gemini when retrieval fails

Architecture:
  The engine is a singleton service that depends on:
    - app.services.skill_graph.skill_graph_service (NetworkX graph)
    - app.db.chroma_client (ChromaDB queries)
    - app.ai.embeddings (EmbeddingService)
    - app.ai.llm_client (Gemini fallback)
"""

from __future__ import annotations

from pydantic import BaseModel

from app.ai.embeddings import get_embedding_service
from app.ai.llm_client import get_llm_client
from app.ai.prompts.question_gen import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.logging import get_logger
from app.db.chroma_client import query_similar
from app.services.skill_graph import skill_graph_service

logger = get_logger(__name__)

# ─── Output schemas ────────────────────────────────────────────────────────────


class GeneratedQuestion(BaseModel):
    """A brand-new LLM-generated question (not from the DB)."""

    question_text: str
    expected_answer: str
    concepts: list[str]
    difficulty: int
    topic: str


class RetrievedCandidate(BaseModel):
    """A question retrieved from ChromaDB (maps back to PG by id)."""

    question_id: str
    document: str
    topic: str
    difficulty: int
    distance: float  # cosine distance — lower is better


# ─── GraphRAGEngine ─────────────────────────────────────────────────────────


class GraphRAGEngine:
    """
    Orchestrates the three-stage retrieval pipeline.

    Stage 1: graph traversal  → find related skill_ids
    Stage 2: vector search    → find semantically similar questions
    Stage 3: LLM fallback     → generate if nothing suitable retrieved
    """

    def _get_neighbor_skills(self, skill_id: str) -> list[str]:
        """
        BFS over the NetworkX skill graph to collect adjacent skill IDs.

        Returns the target skill + its direct prerequisites and dependents.
        This widens the search scope when few questions exist for a skill.
        """
        neighbors = {skill_id}

        node = skill_graph_service.get_node(skill_id)
        if node:
            for prereq in skill_graph_service.get_prerequisites(skill_id):
                neighbors.add(prereq.skill_id)
            for dep in skill_graph_service.get_dependent_skills(skill_id):
                neighbors.add(dep.skill_id)

        logger.debug(
            "Graph traversal complete",
            target=skill_id,
            neighbors=list(neighbors),
        )
        return list(neighbors)

    def _vector_search(
        self,
        skill_id: str,
        mastery: float,
        n: int = 5,
        difficulty_target: int | None = None,
    ) -> list[RetrievedCandidate]:
        """
        Embed the skill description and query ChromaDB.

        The query text is constructed from the skill name + difficulty hint
        so the vector matches semantically relevant questions.
        """
        node = skill_graph_service.get_node(skill_id)
        skill_name = node.name if node else skill_id.replace("_", " ").title()
        diff = difficulty_target or max(1, min(10, int(mastery * 10) + 2))

        query_text = f"{skill_name} difficulty {diff}"
        embedding_svc = get_embedding_service()
        query_vec = embedding_svc.embed_text(query_text)

        # Build a neighbor-based filter if ChromaDB supports $in
        neighbor_ids = self._get_neighbor_skills(skill_id)

        raw = query_similar(
            query_embedding=query_vec,
            n_results=n,
        )

        candidates: list[RetrievedCandidate] = []
        for item in raw:
            meta = item.get("metadata") or {}
            item_topic = meta.get("topic", "")
            # Filter to neighbor skills only
            if item_topic not in neighbor_ids and item_topic != skill_id:
                continue
            candidates.append(
                RetrievedCandidate(
                    question_id=item["id"],
                    document=item["document"],
                    topic=item_topic,
                    difficulty=int(meta.get("difficulty", diff)),
                    distance=item["distance"],
                )
            )

        logger.debug(
            "Vector search complete",
            skill_id=skill_id,
            raw_results=len(raw),
            filtered=len(candidates),
        )
        return candidates

    async def _llm_fallback(
        self,
        skill_id: str,
        mastery: float,
        difficulty_target: int,
        history: list[str] | None = None,
    ) -> GeneratedQuestion:
        """
        Use Gemini to generate a question when retrieval yields nothing.

        This implements Module 2.6 (Next Question Generation) from the architecture.
        """
        node = skill_graph_service.get_node(skill_id)
        skill_name = node.name if node else skill_id.replace("_", " ").title()
        category = node.category if node else "General"

        prompt = USER_PROMPT_TEMPLATE.format(
            topic=skill_name,
            difficulty=difficulty_target,
            category=category,
            target_concepts="core concepts, edge cases, practical application",
            skill_mastery=f"{mastery:.0%}",
            history=", ".join(history) if history else "None",
        )

        client = get_llm_client()
        result: GeneratedQuestion = await client.generate_json(
            prompt=prompt,
            response_model=GeneratedQuestion,
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        )
        logger.info(
            "LLM fallback question generated",
            skill_id=skill_id,
            difficulty=difficulty_target,
        )
        return result

    async def retrieve(
        self,
        skill_id: str,
        mastery: float,
        n: int = 5,
        difficulty_target: int | None = None,
        asked_question_ids: list[str] | None = None,
        asked_titles: list[str] | None = None,
    ) -> tuple[list[RetrievedCandidate], GeneratedQuestion | None]:
        """
        Full Graph-RAG retrieval pipeline.

        Returns:
            (retrieved_candidates, generated_question)
            - retrieved_candidates: list of DB-backed candidates (may be empty)
            - generated_question: LLM-generated question if retrieval fails, else None

        The caller (AdaptiveSelector) decides which to use.
        """
        diff = difficulty_target or max(1, min(10, int(mastery * 10) + 2))

        # Stage 1 + 2: graph traversal + vector search
        candidates = self._vector_search(
            skill_id=skill_id,
            mastery=mastery,
            n=n + (len(asked_question_ids or [])),
            difficulty_target=diff,
        )

        # Filter out already-asked questions
        if asked_question_ids:
            candidates = [c for c in candidates if c.question_id not in asked_question_ids]

        # Stage 3: LLM fallback if nothing retrieved
        generated: GeneratedQuestion | None = None
        if not candidates:
            logger.info(
                "No retrieved candidates — invoking LLM fallback",
                skill_id=skill_id,
                difficulty=diff,
            )
            generated = await self._llm_fallback(
                skill_id=skill_id,
                mastery=mastery,
                difficulty_target=diff,
                history=asked_titles,
            )

        return candidates, generated


# ─── Singleton & FastAPI dependency ──────────────────────────────────────────

_rag_engine: GraphRAGEngine | None = None


def get_rag_engine() -> GraphRAGEngine:
    """Return the module-level GraphRAGEngine singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = GraphRAGEngine()
        logger.info("GraphRAGEngine singleton created")
    return _rag_engine
