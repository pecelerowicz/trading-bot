# trading-bot

## Setup

```bash
conda env create -f environment.yml
conda activate trading-bot
```

## Podman

### Build image

```powershell
podman build -t trading-bot:local .
```

### Run container

```powershell
podman run -d --name trading-bot -v "${PWD}\.env:/app/.env:ro" trading-bot:local
```

### List running containers

```powershell
podman ps
```

### List all containers

```powershell
podman ps -a
```

### Show logs

```powershell
podman logs trading-bot
```

### Follow logs

```powershell
podman logs -f trading-bot
```

### Enter running container

```powershell
podman exec -it trading-bot /bin/sh
```

### Reconciliation logs inside container

```sh
cd /app/logs
ls -lah
cat portfolio-reconciliation-*.log
```

### Stop container

```powershell
podman stop trading-bot
```

### Start existing container

```powershell
podman start trading-bot
```

### Copy reconciliation logs from container

```powershell
podman cp trading-bot:/app/logs .\logs-from-container
```

### Remove container

```powershell
podman rm trading-bot
```

### Remove all containers

```powershell
podman rm --all --force
```

### List images

```powershell
podman images
```
