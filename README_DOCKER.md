# Docker Setup for SQLWhisper

This guide explains how to build and run SQLWhisper using Docker.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+ (optional, for docker-compose setup)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

This will start both the FastAPI backend and Streamlit frontend:

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access the application:**
- Streamlit UI: http://localhost:8501
- FastAPI API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Using Docker directly

#### Build the image:

```bash
docker build -t sqlwhisper:latest .
```

#### Run FastAPI backend only:

```bash
docker run -d \
  --name sqlwhisper-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e MODEL_NAME=yasserrmd/Text2SQL-1.5B \
  -e SUMMARY_MODEL_NAME=google/flan-t5-base \
  sqlwhisper:latest \
  python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

#### Run Streamlit frontend only:

```bash
docker run -d \
  --name sqlwhisper-frontend \
  -p 8501:8501 \
  -v $(pwd)/streamlit_app:/app/streamlit_app \
  -v $(pwd)/data:/app/data \
  -e API_URL=http://localhost:8000 \
  sqlwhisper:latest \
  streamlit run streamlit_app/streamlitapp.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

## Environment Variables

Create a `.env` file in the project root (optional):

```bash
# Model Configuration
MODEL_NAME=yasserrmd/Text2SQL-1.5B
SUMMARY_MODEL_NAME=google/flan-t5-base

# Hugging Face Token (if needed for private models)
HF_TOKEN=your_token_here
```

Docker Compose will automatically load these variables.

## Volumes

The following directories are mounted as volumes:

- `./data` → `/app/data` - Database files
- `./streamlit_app/history.csv` → `/app/streamlit_app/history.csv` - Query history
- Model cache → `/root/.cache/huggingface` - Cached models (persisted in named volume)

## Ports

- **8000**: FastAPI backend API
- **8501**: Streamlit frontend UI

## Building for Production

For production deployments, you may want to:

1. **Use a specific Python version:**
   ```dockerfile
   FROM python:3.10-slim
   ```

2. **Optimize image size:**
   The Dockerfile uses multi-stage builds to minimize final image size.

3. **Set production environment variables:**
   ```bash
   docker-compose -f docker-compose.prod.yml up
   ```

## Troubleshooting

### Models not downloading

If models fail to download, ensure:
- Internet connection is available
- Hugging Face token is set (if using private models)
- Sufficient disk space (models can be several GB)

### Port conflicts

If ports 8000 or 8501 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
  - "8502:8501"  # Use 8502 instead of 8501
```

### Database connection issues

Ensure database files in the `data/` directory are accessible and have correct permissions:

```bash
chmod -R 755 data/
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Docker container logs
docker logs sqlwhisper-backend
docker logs sqlwhisper-frontend
```

## Development Mode

For development with hot-reload:

```bash
# Backend with auto-reload
docker-compose up backend

# Frontend (modify streamlit_app files and they'll reload)
docker-compose up frontend
```

## GPU Support (Optional)

If you have NVIDIA GPU and want to use it:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Add to `docker-compose.yml`:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

3. Run with GPU:
   ```bash
   docker-compose up --build
   ```

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (including model cache)
docker-compose down -v

# Remove images
docker rmi sqlwhisper:latest

# Full cleanup
docker system prune -a
```

## Health Checks

The backend includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

Docker Compose will wait for the backend to be healthy before starting the frontend.

