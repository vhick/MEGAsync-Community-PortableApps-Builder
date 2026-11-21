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
