from pathlib import Path
from neo4j import GraphDatabase
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

SQL = (Path(__file__).parent / "init_schema.cypher").read_text(encoding="utf-8")
statements = [s.strip() for s in SQL.split(";") if s.strip()]

def main():
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            for stmt in statements:
                session.run(stmt)
                print("OK:", stmt.splitlines()[0])

if __name__ == "__main__":
    main()