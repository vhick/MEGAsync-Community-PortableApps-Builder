param([Parameter(Mandatory)][string]$Source,[Parameter(Mandatory)][string]$Build,[Parameter(Mandatory)][string]$Tag)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$target=Join-Path $Source 'src/MEGASync/MegaApplication.cpp'
$s=[IO.File]::ReadAllText($target)
if(-not $s.Contains('qEnvironmentVariable("MEGA_PORTABLE_DATA_DIR")')) {throw 'Portable source override not applied'}
if(-not $Tag.EndsWith('_Win')) {throw 'Non-Windows tag resolved'}
$exe=@(Get-ChildItem -LiteralPath $Build -Recurse -Filter 'MEGAsync.exe' -File | Where-Object {$_.Directory.Name -in @('Release','RelWithDebInfo')})
if($exe.Count -ne 1){throw "Expected exactly one source compiled Windows exe; found $($exe.Count)"}
Write-Host "WINDOWS-COMPILED application: $($exe[0].FullName)"

# Upstream src/MEGASync/gui/gui.cmake installs the five binary Qt
# resources beside the built Release/MEGAsync.exe via POST_BUILD.
# Check immediately after MSBuild so CI does not waste time packaging
# a binary known to fail at start-up.
$resources = @('Resources_common.rcc', 'Resources_qml.rcc', 'Resources_light.rcc', 'Resources_dark.rcc', 'qml.rcc')
foreach ($resource in $resources) {
    $file = Join-Path $exe[0].Directory.FullName $resource
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Built MEGAsync is missing mandatory Qt resource: $resource" }
    $bytes = [IO.File]::ReadAllBytes($file)
    if ($bytes.Length -lt 64 -or [Text.Encoding]::ASCII.GetString($bytes,0,4) -ne 'qres') {
        throw "Built Qt resource has invalid RCC header or size: $resource"
    }
    Write-Host "WINDOWS-COMPILED Qt resource: $resource ($($bytes.Length) bytes)"
}
