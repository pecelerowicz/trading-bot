. "$PSScriptRoot\_config.ps1"

$RemoteCommand = 'tmp=$(mktemp -d); if podman cp "{0}:/app/logs" "$tmp/" 2>/dev/null; then set -- "$tmp"/logs/portfolio-reconciliation-*.log; if [ -e "$1" ]; then cat "$@"; else echo "No reconciliation logs found."; fi; else echo "No reconciliation logs found."; fi; rm -rf "$tmp"' -f $Container

ssh -i $SshKey $Server $RemoteCommand