# CineGraph

**A graph-powered movie discovery and recommendation engine.** CineGraph uses Neo4j relationships between films and people to turn a simple title search into connected recommendations.

![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)

## Product features

- Search and browse the movie graph.
- Open a film to view its cast and crew.
- Discover related films based on shared cast members.
- Explore a responsive React + Tailwind interface built for movie discovery.
- Run the stack locally with FastAPI, Neo4j, and Docker Compose.

## Architecture

```text
React + Tailwind web app → FastAPI CineGraph API → Neo4j movie graph
```

The API is read-only by design in this first version. It exposes discovery, movie detail, graph neighbourhood, and relationship-based recommendations.

## Start with Docker

1. Create a local configuration file.

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start the services.

   ```bash
   docker compose up --build
   ```

3. Open `http://localhost:5173` for CineGraph and `http://localhost:7474` for Neo4j Browser.

4. Load the official Neo4j Movies sample graph in Neo4j Browser using `:play movies`, then run its supplied `CREATE` query. CineGraph needs a graph containing `Movie`, `Person`, and `ACTED_IN` relationships.

## Local development

API:

```bash
pip install -r requirements.txt
uvicorn cinegraph_api:app --reload --port 8000
```

Web app:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` when the API is not at `http://localhost:8000`.

## API

| Endpoint | Description |
| --- | --- |
| `GET /health` | API and database connectivity status |
| `GET /api/movies?q=` | Search/discover films |
| `GET /api/movies/{title}` | Film details plus cast/crew |
| `GET /api/movies/{title}/recommendations` | Films connected by cast |
| `GET /api/graph?title=` | Film neighbourhood for visual extensions |

## Roadmap

- Personal profiles, watchlists, ratings, and recommendation feedback.
- Genre/director filters and richer graph visualisation.
- Movie-import workflow for a user-owned dataset.
- Authentication, tests, CI, and deployed demo.

## Copyright and license

Copyright © 2026 `perfect-e`. CineGraph is independently authored, uses Neo4j as its graph database, and is released under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
