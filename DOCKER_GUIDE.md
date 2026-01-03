# Docker Setup Guide for IRONCLAD SIEM

This guide explains how to run the IRONCLAD SIEM Dashboard in a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the container (all Sigma rules and all TTP intelligence)
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```


#### Custom Build: Only Selected Sigma Rules and TTP Intelligence

You can build a custom image with only the Sigma rules and TTP intelligence you want using the build-compose.sh script. The flags `--linux`, `--nginx`, and `--windows` now control inclusion of both Sigma and TTP rules for each platform:

```bash
# Only Linux rules (Sigma + TTP)
./build-compose.sh --linux

# Only Nginx rules (Sigma + TTP)
./build-compose.sh --nginx

# Only Windows rules (Sigma + TTP)
./build-compose.sh --windows

# All rules (Sigma + TTP)
./build-compose.sh --all

# Only base image (no rules/intel)
./build-compose.sh
```

**Note:** The `--linux`, `--nginx`, and `--windows` flags now include both Sigma and TTP rules for the selected platform. The previous `--ttp-*` flags are no longer needed.

### 2. Access the Dashboard

Once the container is running, access the dashboard at:
- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Docker Commands

### Start the container
```bash
docker-compose up -d
```

### Stop the container
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart the container
```bash
docker-compose restart
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Execute commands inside the container
```bash
docker-compose exec sih-central-app bash
```

## File Editing

All files in the project directory are **editable** from your host machine. The project is mounted as a volume, so:

1. Edit any file in the project directory on your host machine
2. Changes are immediately reflected in the container
3. For Python changes, restart the container to apply them:
   ```bash
   docker-compose restart
   ```

## Data Persistence

The following directories are persisted on your host machine:
- `collected_logs/` - Database and processed logs
- `logs/` - Application logs

Even if you delete the container, your data will remain intact.

## Manual Docker Build (Alternative)

If you prefer not to use Docker Compose:

```bash
# Build the image
docker build -t ironclad-siem .

# Run the container
docker run -d \
  --name ironclad-siem \
  -p 8000:8000 \
  -v $(pwd):/app \
  -v $(pwd)/collected_logs:/app/collected_logs \
  -v $(pwd)/logs:/app/logs \
  ironclad-siem
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Check if port 8000 is already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

### Database issues
```bash
# Remove the database and let it reinitialize
rm -rf collected_logs/ironclad_logs.db
docker-compose restart
```

### Permission issues (Linux/Mac)
```bash
# Fix permissions
chmod -R 755 collected_logs logs
```

## Features

✅ **Portable**: Run anywhere Docker is installed
✅ **Editable**: Edit code on host machine, changes reflect in container
✅ **Auto-start**: server.py runs automatically on container startup
✅ **Persistent**: Data survives container restarts
✅ **Isolated**: All dependencies bundled in the container
✅ **Customizable**: Build images with only the Sigma rules and TTP intelligence you need

## Notes

- The server runs with hot-reload enabled by default
- Python code changes require a container restart
- Static files and templates update immediately
- Database is initialized automatically on first run
