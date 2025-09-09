"""CineGraph API.

Original Neo4j Movies example concepts are used under Apache-2.0; this API and
the CineGraph product experience are new project work.
"""
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase, AsyncDriver

URI = os.environ["NEO4J_URI"] if "NEO4J_URI" in os.environ else "neo4j://neo4j:7687"
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.driver = AsyncGraphDatabase.driver(URI, auth=(USER, PASSWORD))
    yield
    await app.state.driver.close()

app = FastAPI(title="CineGraph API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET"], allow_headers=["*"])

def driver() -> AsyncDriver:
    return app.state.driver

def movie_projection(alias: str = "m") -> str:
    return f"""{{ title: {alias}.title, released: {alias}.released, tagline: {alias}.tagline,
                 summary: {alias}.summary, poster: {alias}.poster, votes: coalesce({alias}.votes, 0),
                 genres: coalesce({alias}.genres, []) }}"""

@app.get("/health")
async def health():
    try:
        await driver().verify_connectivity()
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}

@app.get("/api/movies")
async def discover_movies(
    q: Annotated[str, Query(max_length=100)] = "",
    year: int | None = Query(default=None, ge=1888, le=2100),
    limit: int = Query(default=24, ge=1, le=60),
):
    records, _, _ = await driver().execute_query(
        f"""MATCH (m:Movie)
        WHERE ($q = '' OR toLower(m.title) CONTAINS toLower($q))
          AND ($year IS NULL OR m.released = $year)
        RETURN {movie_projection()} AS movie
        ORDER BY coalesce(m.votes, 0) DESC, m.released DESC LIMIT $limit""",
        q=q.strip(), year=year, limit=limit, database_=DATABASE, routing_="r",
    )
    return [record["movie"] for record in records]

@app.get("/api/movies/{title}")
async def movie_detail(title: str):
    records, _, _ = await driver().execute_query(
        f"""MATCH (m:Movie {{title: $title}})
        OPTIONAL MATCH (m)<-[r]-(person:Person)
        RETURN {movie_projection()} AS movie,
        collect(DISTINCT {{name: person.name, role: head(split(toLower(type(r)), '_')), characters: coalesce(r.roles, [])}}) AS people""",
        title=title, database_=DATABASE, routing_="r",
    )
    if not records:
        raise HTTPException(status_code=404, detail="Movie not found")
    result = records[0]
    return {"movie": result["movie"], "people": [person for person in result["people"] if person["name"]]}

@app.get("/api/movies/{title}/recommendations")
async def recommendations(title: str, limit: int = Query(default=8, ge=1, le=20)):
    records, _, _ = await driver().execute_query(
        f"""MATCH (m:Movie {{title: $title}})<-[:ACTED_IN]-(p:Person)-[:ACTED_IN]->(candidate:Movie)
        WHERE candidate <> m
        WITH candidate, count(DISTINCT p) AS shared_people
        RETURN {movie_projection('candidate')} AS movie, shared_people
        ORDER BY shared_people DESC, movie.votes DESC LIMIT $limit""",
        title=title, limit=limit, database_=DATABASE, routing_="r",
    )
    return [{**record["movie"], "reason": f"Shares {record['shared_people']} cast member(s)"} for record in records]

@app.get("/api/graph")
async def graph(title: str = Query(..., max_length=200)):
    records, _, _ = await driver().execute_query(
        """MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(p:Person)-[:ACTED_IN]->(related:Movie)
        RETURN m.title AS seed, collect(DISTINCT p.name)[..20] AS people,
               collect(DISTINCT related.title)[..20] AS movies""",
        title=title, database_=DATABASE, routing_="r",
    )
    if not records:
        raise HTTPException(status_code=404, detail="Movie not found")
    record = records[0]
    nodes = [{"id": record["seed"], "label": record["seed"], "kind": "movie"}]
    links = []
    for person in record["people"]:
        nodes.append({"id": person, "label": person, "kind": "person"}); links.append({"source": person, "target": record["seed"]})
    for movie in record["movies"]:
        if movie != record["seed"]:
            nodes.append({"id": movie, "label": movie, "kind": "movie"})
    return {"nodes": nodes, "links": links}
