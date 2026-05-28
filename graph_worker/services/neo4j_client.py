"""Neo4j client — upserts entities and relationships extracted from document chunks."""
import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def verify_connectivity(self):
        self._driver.verify_connectivity()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_indexes(self):
        with self._driver.session() as s:
            s.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            s.run("CREATE INDEX document_doc_id IF NOT EXISTS FOR (d:Document) ON (d.doc_id)")

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def upsert_document(self, doc_id: str, title: str, source_url: str, agent: str):
        with self._driver.session() as s:
            s.run(
                """
                MERGE (d:Document {doc_id: $doc_id})
                SET d.title = $title,
                    d.source_url = $source_url,
                    d.agent = $agent
                """,
                doc_id=doc_id, title=title, source_url=source_url, agent=agent,
            )

    def upsert_entity(self, name: str, entity_type: str, doc_id: str, collection: str):
        if not name:
            return
        with self._driver.session() as s:
            s.run(
                """
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e.collection = $collection
                WITH e
                MATCH (d:Document {doc_id: $doc_id})
                MERGE (e)-[:APPEARS_IN]->(d)
                """,
                name=name, type=entity_type, collection=collection, doc_id=doc_id,
            )

    def upsert_relationship(
        self,
        from_entity: str,
        to_entity: str,
        rel_type: str,
        confidence: float,
        source_chunk_id: str = "",
    ):
        if not from_entity or not to_entity:
            return
        with self._driver.session() as s:
            s.run(
                """
                MERGE (a:Entity {name: $from_name})
                MERGE (b:Entity {name: $to_name})
                MERGE (a)-[r:RELATED_TO {rel_type: $rel_type}]->(b)
                SET r.confidence = $confidence,
                    r.source_chunk_id = $source_chunk_id
                """,
                from_name=from_entity,
                to_name=to_entity,
                rel_type=rel_type,
                confidence=confidence,
                source_chunk_id=source_chunk_id,
            )

    # ------------------------------------------------------------------
    # Reads (used by GraphRAG)
    # ------------------------------------------------------------------

    def query_related_entities(self, query_terms: list[str], limit: int = 10) -> list[str]:
        """Return entity names related to any of the query terms — used to expand ChromaDB queries."""
        if not query_terms:
            return []
        with self._driver.session() as s:
            result = s.run(
                """
                UNWIND $terms AS term
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower(term)
                OPTIONAL MATCH (e)-[:RELATED_TO]-(related:Entity)
                WITH collect(DISTINCT e.name) + collect(DISTINCT related.name) AS names
                UNWIND names AS name
                RETURN DISTINCT name
                LIMIT $limit
                """,
                terms=query_terms,
                limit=limit,
            )
            return [row["name"] for row in result if row["name"]]
