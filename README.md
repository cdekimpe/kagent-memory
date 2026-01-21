# Kagent Memory

Long-term memory service for the [Kagent](https://github.com/kagent-dev/kagent) platform using Vector DB (Qdrant) and OpenAI embeddings.

## Features

- **Vector-based semantic search** - Store and retrieve memories using OpenAI embeddings
- **Qdrant integration** - Scalable vector database with rich filtering
- **Text chunking** - Automatic chunking of large documents with configurable overlap
- **Multi-tenant isolation** - Filter by user_id, session_id, and agent_name
- **Kubernetes-native** - Deploy with Helm alongside Kagent
- **ADK compatible** - Works with Google ADK agents via HTTP API

## Quick Start

### Local Development

```bash
# 1. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 2. Install dependencies
uv sync

# 3. Run the service
OPENAI_API_KEY=sk-xxx uv run kagent-memory serve
```

### Kubernetes Deployment

```bash
# 1. Build Helm dependencies (downloads Qdrant chart)
cd helm/kagent-memory && helm dependency build && cd ../..

# 2. Install with embedded Qdrant
helm install kagent-memory ./helm/kagent-memory \
  --namespace kagent \
  --set openai.apiKey=$OPENAI_API_KEY

# Or with external Qdrant (skip dependency build if not using embedded)
helm install kagent-memory ./helm/kagent-memory \
  --namespace kagent \
  --set openai.apiKey=$OPENAI_API_KEY \
  --set qdrant.enabled=false \
  --set memory.qdrant.url=http://my-qdrant:6333
```

> **Note**: The `helm dependency build` step fetches the Qdrant sub-chart. This is required when using embedded Qdrant (`qdrant.enabled=true`).

## API Reference

### Add Memory

```bash
curl -X POST http://localhost:8080/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The user prefers dark mode and uses vim keybindings",
    "user_id": "user-123",
    "session_id": "session-456",
    "agent_name": "settings-agent",
    "metadata": {"category": "preferences"}
  }'
```

### Search Memories

```bash
curl -X POST http://localhost:8080/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the user preferences?",
    "user_id": "user-123",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

### Health Check

```bash
curl http://localhost:8080/health
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `KAGENT_MEMORY_PORT` | Server port | 8080 |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `KAGENT_MEMORY_QDRANT_URL` | Qdrant URL | http://qdrant:6333 |
| `KAGENT_MEMORY_QDRANT_COLLECTION` | Collection name | kagent-memories |
| `KAGENT_MEMORY_EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |
| `KAGENT_MEMORY_EMBEDDING_DIMENSIONS` | Vector dimensions | 1536 |
| `KAGENT_MEMORY_CHUNK_SIZE` | Chunk size in characters | 1000 |
| `KAGENT_MEMORY_CHUNK_OVERLAP` | Chunk overlap in characters | 200 |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────┐
│   Agents    │────►│  kagent-memory   │────►│  Qdrant │
│ (ADK/CrewAI)│     │  HTTP Service    │     │ VectorDB│
└─────────────┘     └──────────────────┘     └─────────┘
                           │
                    ┌──────▼──────┐
                    │  OpenAI API │
                    │  Embeddings │
                    └─────────────┘
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
