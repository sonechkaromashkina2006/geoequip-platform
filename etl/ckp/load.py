import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
SERVER_DIR = ROOT_DIR / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from app.config import MODEL_NAME, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from normalize import load_jsonl


def ensure_schema_and_index(session, embedding_dim: int) -> None:
    session.run(
        "CREATE CONSTRAINT enterprise_name_unique IF NOT EXISTS "
        "FOR (e:Enterprise) REQUIRE e.name IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT equipment_eq_id_unique IF NOT EXISTS "
        "FOR (eq:Equipment) REQUIRE eq.eq_id IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS "
        "FOR (c:Category) REQUIRE c.name IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT task_name_unique IF NOT EXISTS "
        "FOR (t:Task) REQUIRE t.name IS UNIQUE"
    )
    session.run(
        f"""
        CREATE VECTOR INDEX equipment_embeddings IF NOT EXISTS
        FOR (eq:Equipment) ON (eq.embedding)
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {embedding_dim},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
    )


def load_to_neo4j(records: List[Dict[str, Any]], batch_size: int = 50) -> None:
    if not records:
        print("Нет записей для загрузки.")
        return

    model = SentenceTransformer(MODEL_NAME)
    texts = [r.get("description") or r["name"] for r in records]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    embedding_dim = len(embeddings[0])

    payload: List[Dict[str, Any]] = []
    for rec, emb in zip(records, embeddings):
        payload.append(
            {
                "eq_id": str(rec["eq_id"]),
                "name": rec["name"],
                "description": rec.get("description") or rec["name"],
                "manufacturer": rec.get("manufacturer"),
                "model": rec.get("model"),
                "year": rec.get("year"),
                "region": rec.get("region"),
                "source_url": rec.get("source_url"),
                "embedding": [float(x) for x in emb],
                "enterprise_name": rec["enterprise_name"],
                "enterprise_type": rec.get("enterprise_type") or "ЦКП",
                "lat": rec.get("lat"),
                "lon": rec.get("lon"),
                "accessibility": float(rec.get("accessibility", 0.7)),
                "cost": float(rec.get("cost", 0.5)),
                "category": rec.get("category") or "Прочее",
                "tasks": rec.get("tasks") or [],
            }
        )

    cypher = """
    UNWIND $rows AS row
    MERGE (ent:Enterprise {name: row.enterprise_name})
    SET ent.type = row.enterprise_type,
        ent.region = row.region,
        ent.lat = row.lat,
        ent.lon = row.lon,
        ent.accessibility = row.accessibility,
        ent.cost = row.cost

    MERGE (eq:Equipment {eq_id: row.eq_id})
    SET eq.name = row.name,
        eq.description = row.description,
        eq.manufacturer = row.manufacturer,
        eq.model = row.model,
        eq.year = row.year,
        eq.source_url = row.source_url,
        eq.embedding = row.embedding

    MERGE (ent)-[:HAS_EQUIPMENT]->(eq)

    MERGE (cat:Category {name: row.category})
    MERGE (eq)-[:BELONGS_TO]->(cat)

    FOREACH (t_name IN row.tasks |
        MERGE (task:Task {name: t_name})
        MERGE (eq)-[:SUITABLE_FOR]->(task)
    )
    """

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            ensure_schema_and_index(session, embedding_dim)
            for i in range(0, len(payload), batch_size):
                chunk = payload[i : i + batch_size]
                session.run(cypher, rows=chunk)
        print(f"Загружено записей в Neo4j: {len(payload)}")
    finally:
        driver.close()


if __name__ == "__main__":
    src = Path("data/processed/equipment_ready.jsonl")
    rows = load_jsonl(src)
    load_to_neo4j(rows)