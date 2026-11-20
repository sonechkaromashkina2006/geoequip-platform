from collections import defaultdict
from sentence_transformers import SentenceTransformer
from app.config import MODEL_NAME
import asyncio

model = SentenceTransformer(MODEL_NAME)

async def vector_search_raw(driver, query_vector, top_k=10):
    query = """
    CALL db.index.vector.queryNodes('equipment_embeddings', $top_k, $vector)
    YIELD node, score
    MATCH (e:Enterprise)-[:HAS_EQUIPMENT]->(node)
    RETURN 
        e.name        AS enterprise,
        e.lat         AS lat,
        e.lon         AS lon,
        e.accessibility AS accessibility,
        e.cost        AS cost,
        node.name     AS equipment,
        node.description AS description,
        score
    """
    async with driver.session() as session:
        result = await session.run(query, top_k=top_k, vector=query_vector)
        return await result.data()

def aggregate_by_enterprise(raw_results):
    enterprises = defaultdict(lambda: {
        "score": 0.0,
        "matched_equipment": [],
        "lat": None, "lon": None,
        "accessibility": None, "cost": None
    })

    for row in raw_results:
        name = row["enterprise"]
        if row["score"] > enterprises[name]["score"]:
            enterprises[name]["score"] = row["score"]
        enterprises[name]["matched_equipment"].append({
            "name": row["equipment"],
            "description": row["description"],
            "score": round(row["score"], 4)
        })
        enterprises[name]["lat"] = row["lat"]
        enterprises[name]["lon"] = row["lon"]
        enterprises[name]["accessibility"] = row["accessibility"]
        enterprises[name]["cost"] = row["cost"]

    sorted_result = sorted(
        [{"enterprise": k, **v} for k, v in enterprises.items()],
        key=lambda x: x["score"],
        reverse=True
    )
    return sorted_result

async def search(driver, user_query, top_enterprises=5):
    vector = await asyncio.to_thread(lambda: model.encode(user_query).tolist())
    raw = await vector_search_raw(driver, vector, top_k=top_enterprises * 3)
    return aggregate_by_enterprise(raw)[:top_enterprises]