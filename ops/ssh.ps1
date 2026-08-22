$ErrorActionPreference = "Stop"


$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SshKey = Join-Path $ProjectRoot "..\keys\ssh-key-2026-08-21.key"


$Server = "opc@138.2.190.219"


if (-not (Test-Path $SshKey)) {
    throw "SSH key not found: $SshKey"
}


ssh -i $SshKey $Server