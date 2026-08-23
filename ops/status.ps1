. "$PSScriptRoot\_config.ps1"

$RemoteCommand = 'echo "=== CONTAINERS ==="; podman ps -a; echo; echo "=== MEMORY ==="; free -h; echo; echo "=== SWAP ==="; swapon --show; echo; echo "=== DISK ==="; df -h /; echo; echo "=== UPTIME ==="; uptime'

ssh -i $SshKey $Server $RemoteCommand