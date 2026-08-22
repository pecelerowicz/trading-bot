$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SshKey = Join-Path $ProjectRoot "..\keys\ssh-key-2026-08-21.key"

$Server = "opc@138.2.190.219"
$Container = "trading-bot"

if (-not (Test-Path $SshKey)) {
    throw "SSH key not found: $SshKey"
}

$RemoteCommand = "TMP_DIR=`$(mktemp -d); podman cp ${Container}:/app/logs `"`$TMP_DIR/`" 2>/dev/null; if ls `"`$TMP_DIR/logs`"/portfolio-reconciliation-*.log >/dev/null 2>&1; then cat `"`$TMP_DIR/logs`"/portfolio-reconciliation-*.log; else echo 'No reconciliation logs found.'; fi; rm -rf `"`$TMP_DIR`""

ssh -i $SshKey $Server $RemoteCommand