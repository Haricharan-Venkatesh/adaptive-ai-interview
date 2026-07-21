import logging
from app.db import neo4j_client
from app.models.dashboard import CodeMapGraphResponse, CodeMapLink, CodeMapNode

logger = logging.getLogger(__name__)

# Standard default concept map used as fallback when Neo4j is unpopulated or offline
DEFAULT_CONCEPT_NODES = [
    CodeMapNode(id="arrays_strings", name="Arrays & Strings", group="Data Structures", val=12.0, description="Sequential memory contiguous elements"),
    CodeMapNode(id="two_pointers", name="Two Pointers", group="Algorithms", val=9.0, description="Opposing or fast/slow pointer traversals"),
    CodeMapNode(id="binary_search", name="Binary Search", group="Algorithms", val=9.0, description="Logarithmic search in sorted space"),
    CodeMapNode(id="trees_graphs", name="Trees & Graphs", group="Data Structures", val=14.0, description="Hierarchical and network nodes with edges"),
    CodeMapNode(id="dynamic_programming", name="Dynamic Programming", group="Advanced", val=16.0, description="Memoization & bottom-up optimal substructure"),
    CodeMapNode(id="graph_rag", name="Graph-RAG Engine", group="AI Systems", val=15.0, description="Knowledge-graph retrieval augmented generation")
]

DEFAULT_CONCEPT_LINKS = [
    CodeMapLink(source="arrays_strings", target="two_pointers", label="PREREQUISITE_FOR", weight=1.0),
    CodeMapLink(source="two_pointers", target="binary_search", label="EXTENDS", weight=1.0),
    CodeMapLink(source="binary_search", target="dynamic_programming", label="DEPENDS_ON", weight=1.0),
    CodeMapLink(source="arrays_strings", target="trees_graphs", label="FOUNDATION_FOR", weight=1.0),
    CodeMapLink(source="trees_graphs", target="graph_rag", label="USED_IN", weight=1.0)
]


async def fetch_codemap_graph(session_id: str | None = None) -> CodeMapGraphResponse:
    """
    Fetch candidate code map graph (nodes + relationships) from Neo4j database.
    Performs response validation, relationship deduplication, and fallback handling.
    """
    if not neo4j_client.is_neo4j_initialized():
        logger.info("Neo4j driver uninitialized. Returning default fallback concept map.")
        return CodeMapGraphResponse(
            status="success",
            nodes=DEFAULT_CONCEPT_NODES,
            links=DEFAULT_CONCEPT_LINKS,
            message="Neo4j driver offline/uninitialized. Serving fallback concept map.",
            count_nodes=len(DEFAULT_CONCEPT_NODES),
            count_links=len(DEFAULT_CONCEPT_LINKS)
        )

    try:
        # Query nodes and relationships from Neo4j
        cypher_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        records = await neo4j_client.execute_query(cypher_query)

        if not records:
            logger.info("Neo4j database returned 0 records. Returning empty status fallback.")
            return CodeMapGraphResponse(
                status="empty",
                nodes=DEFAULT_CONCEPT_NODES,
                links=DEFAULT_CONCEPT_LINKS,
                message="Neo4j graph empty. Default candidate map loaded.",
                count_nodes=len(DEFAULT_CONCEPT_NODES),
                count_links=len(DEFAULT_CONCEPT_LINKS)
            )

        nodes_dict: dict[str, CodeMapNode] = {}
        links_list: list[CodeMapLink] = []
        seen_links: set[tuple[str, str, str]] = set()

        for rec in records:
            n_data = rec.get("n")
            if n_data and isinstance(n_data, dict):
                # Neo4j record dictionary format
                node_props = dict(n_data)
                node_id = str(node_props.get("id") or node_props.get("name") or "node_unknown")
                if node_id not in nodes_dict:
                    nodes_dict[node_id] = CodeMapNode(
                        id=node_id,
                        name=str(node_props.get("name") or node_id),
                        group=str(node_props.get("group") or "Concept"),
                        val=float(node_props.get("val") or 10.0),
                        description=node_props.get("description"),
                        mastery_score=float(node_props["mastery_score"]) if "mastery_score" in node_props and node_props["mastery_score"] is not None else None
                    )

            m_data = rec.get("m")
            if m_data and isinstance(m_data, dict):
                m_props = dict(m_data)
                m_id = str(m_props.get("id") or m_props.get("name") or "node_unknown")
                if m_id not in nodes_dict:
                    nodes_dict[m_id] = CodeMapNode(
                        id=m_id,
                        name=str(m_props.get("name") or m_id),
                        group=str(m_props.get("group") or "Concept"),
                        val=float(m_props.get("val") or 10.0),
                        description=m_props.get("description"),
                        mastery_score=float(m_props["mastery_score"]) if "mastery_score" in m_props and m_props["mastery_score"] is not None else None
                    )

                r_data = rec.get("r")
                if r_data and n_data:
                    source_id = str(dict(n_data).get("id") or dict(n_data).get("name"))
                    target_id = m_id
                    rel_type = "DEPENDS_ON"
                    rel_weight = 1.0
                    if isinstance(r_data, tuple) and len(r_data) >= 3:
                        rel_type = str(r_data[1])
                    elif isinstance(r_data, dict):
                        rel_type = str(r_data.get("type") or "DEPENDS_ON")
                        rel_weight = float(r_data.get("weight", 1.0))

                    link_key = (source_id, target_id, rel_type)
                    if link_key not in seen_links:
                        seen_links.add(link_key)
                        links_list.append(CodeMapLink(
                            source=source_id,
                            target=target_id,
                            label=rel_type,
                            weight=rel_weight
                        ))

        final_nodes = list(nodes_dict.values())
        if not final_nodes:
            final_nodes = DEFAULT_CONCEPT_NODES
            links_list = DEFAULT_CONCEPT_LINKS

        return CodeMapGraphResponse(
            status="success",
            nodes=final_nodes,
            links=links_list,
            message="Graph retrieved successfully from Neo4j.",
            count_nodes=len(final_nodes),
            count_links=len(links_list)
        )

    except Exception as exc:
        logger.error("Error executing Neo4j codemap graph query: %s", exc, exc_info=True)
        return CodeMapGraphResponse(
            status="error",
            nodes=DEFAULT_CONCEPT_NODES,
            links=DEFAULT_CONCEPT_LINKS,
            message=f"Neo4j query exception: {str(exc)}. Falling back to default map.",
            count_nodes=len(DEFAULT_CONCEPT_NODES),
            count_links=len(DEFAULT_CONCEPT_LINKS)
        )
