$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SshKey = Join-Path $ProjectRoot "..\keys\ssh-key-2026-08-21.key"

$Server = "opc@138.2.190.219"

if (-not (Test-Path $SshKey)) {
    throw "SSH key not found: $SshKey"
}

$RemoteCommand = 'echo "=== CONTAINERS ==="; podman ps -a; echo; echo "=== MEMORY ==="; free -h; echo; echo "=== SWAP ==="; swapon --show; echo; echo "=== DISK ==="; df -h /; echo; echo "=== UPTIME ==="; uptime'

ssh -i $SshKey $Server $RemoteCommand