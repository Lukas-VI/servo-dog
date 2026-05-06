param(
    [string]$HostName = "192.168.12.1",
    [string]$User = "pi",
    [string]$Password = "123456",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$argsList = @(
    "$scriptDir\deploy_to_pi.py",
    "--host", $HostName,
    "--user", $User,
    "--password", $Password
)
if ($SkipTests) {
    $argsList += "--skip-tests"
}

python @argsList
