$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SshKey = Join-Path $ProjectRoot "..\keys\ssh-key-2026-08-21.key"

$Server = "opc@138.2.190.219"
$Container = "trading-bot"

if (-not (Test-Path $SshKey)) {
    throw "SSH key not found: $SshKey"
}

Write-Host "Container status:"
ssh -i $SshKey $Server "podman ps -a --filter name=$Container"

Write-Host ""
Write-Host "Container logs:"

ssh -i $SshKey $Server "podman logs $Container"