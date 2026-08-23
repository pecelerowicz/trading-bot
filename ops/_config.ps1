$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env.ops"

if (-not (Test-Path $EnvFile)) {
    throw "Operations environment file not found: $EnvFile"
}

$Config = @{}

foreach ($RawLine in Get-Content $EnvFile) {
    $Line = $RawLine.Trim()

    if (-not $Line -or $Line.StartsWith("#")) {
        continue
    }

    $Parts = $Line -split "=", 2

    if ($Parts.Count -ne 2) {
        throw "Invalid line in .env.ops: $Line"
    }

    $Name = $Parts[0].Trim()
    $Value = $Parts[1].Trim()

    if (
        ($Value.StartsWith('"') -and $Value.EndsWith('"')) -or
        ($Value.StartsWith("'") -and $Value.EndsWith("'"))
    ) {
        $Value = $Value.Substring(1, $Value.Length - 2)
    }

    $Config[$Name] = $Value
}

$RequiredVariables = @(
    "SERVER_HOST",
    "SERVER_USER",
    "SSH_KEY_PATH",
    "CONTAINER_NAME"
)

foreach ($Variable in $RequiredVariables) {
    if (-not $Config[$Variable]) {
        throw "Missing variable in .env.ops: $Variable"
    }
}

$SshKeyPath = $Config["SSH_KEY_PATH"]

if ([System.IO.Path]::IsPathRooted($SshKeyPath)) {
    $SshKey = $SshKeyPath
}
else {
    $SshKey = [System.IO.Path]::GetFullPath(
        (Join-Path $ProjectRoot $SshKeyPath)
    )
}

if (-not (Test-Path $SshKey)) {
    throw "SSH key not found: $SshKey"
}

$Server = "$($Config["SERVER_USER"])@$($Config["SERVER_HOST"])"
$Container = $Config["CONTAINER_NAME"]