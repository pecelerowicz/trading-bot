# trading-bot

Data analysis and experimenting

## Setup

```bash
conda env create -f environment.yml
conda activate trading-bot
```

## Container (Podman)

Run these commands from the project root in PowerShell.

### Build the image

```powershell
podman build -t trading-bot:local .
```

### Run the container in the background

```powershell
podman run -d --name trading-bot --env-file .env trading-bot:local
```

Do not use `--rm` if you want to inspect the container or retrieve its files after the program finishes.

### Inspect containers

Show running containers:

```powershell
podman ps
```

Show all containers, including finished ones:

```powershell
podman ps -a
```

### View application output

```powershell
podman logs trading-bot
```

Follow output live:

```powershell
podman logs -f trading-bot
```

`Ctrl+C` stops following the logs; it does not stop the container.

### Enter a running container

```powershell
podman exec -it trading-bot /bin/sh
```

For example:

```sh
cd /app/logs
ls -lah
cat portfolio-reconciliation-*.log
```

### Retrieve log files after the program finishes

When the program finishes, the container changes to `Exited`, but its filesystem and generated files remain available until the container is removed.

Copy the reconciliation logs to the current directory:

```powershell
podman cp trading-bot:/app/logs .\logs-from-container
```

Starting an exited container again with:

```powershell
podman start trading-bot
```

starts the bot again. It does not start an empty shell.

### Stop and remove the container

Stop:

```powershell
podman stop trading-bot
```

Remove:

```powershell
podman rm trading-bot
```

Removing the container also removes files stored only inside that container.

To stop and remove all containers:

```powershell
podman rm --all --force
```
