# Quickstart Guide

This guide will help you get kagent-memory running locally and deployed to Kubernetes.

## Prerequisites

- Python 3.11+
- Docker (for Qdrant)
- OpenAI API key
- (Optional) Kubernetes cluster with Helm

## Local Development

### 1. Start Qdrant

```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### 3. Set Environment Variables

```bash
export OPENAI_API_KEY="sk-your-api-key"
export KAGENT_MEMORY_QDRANT_URL="http://localhost:6333"
```

### 4. Start the Service

```bash
# Using uv
uv run kagent-memory serve

# Or directly
kagent-memory serve
```

The service will be available at `http://localhost:8080`.

### 5. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Add a memory
curl -X POST http://localhost:8080/api/memory \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The user prefers dark mode and uses vim keybindings",
    "user_id": "user-123",
    "metadata": {"category": "preferences"}
  }'

# Search memories
curl -X POST http://localhost:8080/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the user preferences?",
    "user_id": "user-123",
    "top_k": 5
  }'
```

## Kubernetes Deployment

### 1. Add the Helm Repository (if published)

```bash
# Or use local chart
cd kagent-memory
```

### 2. Create OpenAI Secret

```bash
kubectl create namespace kagent

# Create a secret specifically for kagent-memory embeddings
kubectl create secret generic kagent-memory-openai \
  --namespace kagent \
  --from-literal=KAGENT_MEMORY_OPENAI_API_KEY="sk-your-api-key"
```

### 3. Build Helm Dependencies

```bash
# Download the Qdrant sub-chart (required for embedded Qdrant)
cd helm/kagent-memory && helm dependency build && cd ../..
```

### 4. Install with Helm

**Option A: With embedded Qdrant (recommended for testing)**

```bash
helm install kagent-memory ./helm/kagent-memory \
  --namespace kagent \
  --set openai.existingSecret=kagent-memory-openai
```

**Option B: With external Qdrant**

```bash
# No need to run `helm dependency build` if using external Qdrant
helm install kagent-memory ./helm/kagent-memory \
  --namespace kagent \
  --set openai.existingSecret=kagent-memory-openai \
  --set qdrant.enabled=false \
  --set memory.qdrant.url=http://my-qdrant:6333
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n kagent -l app.kubernetes.io/name=kagent-memory

# Check logs
kubectl logs -n kagent -l app.kubernetes.io/name=kagent-memory

# Port-forward for testing
kubectl port-forward -n kagent svc/kagent-memory 8080:8080
```

### 6. Test from Inside the Cluster

From any pod in the `kagent` namespace:

```bash
curl http://kagent-memory:8080/health
```

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `KAGENT_MEMORY_PORT` | Server port | 8080 |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `KAGENT_MEMORY_QDRANT_URL` | Qdrant URL | http://localhost:6333 |
| `KAGENT_MEMORY_QDRANT_COLLECTION` | Collection name | kagent-memories |
| `KAGENT_MEMORY_EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |
| `KAGENT_MEMORY_EMBEDDING_DIMENSIONS` | Vector dimensions | 1536 |
| `KAGENT_MEMORY_CHUNK_SIZE` | Chunk size (chars) | 1000 |
| `KAGENT_MEMORY_CHUNK_OVERLAP` | Chunk overlap (chars) | 200 |

## Next Steps

- See [examples/](../examples/) for integration examples
- Check [API Reference](api-reference.md) for detailed endpoint documentation
