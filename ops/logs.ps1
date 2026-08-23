. "$PSScriptRoot\_config.ps1"

Write-Host "Container status:"
ssh -i $SshKey $Server "podman ps -a --filter name=$Container"

Write-Host ""
Write-Host "Container logs:"

ssh -i $SshKey $Server "podman logs $Container"