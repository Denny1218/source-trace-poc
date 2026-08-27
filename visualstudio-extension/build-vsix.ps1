# Headless build → source-trace-visualstudio-0.1.0.vsix (ops offline install).
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension" }
$RepoRoot = Split-Path -Parent $Root
$OutDir = Join-Path $Root "out"
$DeliverDir = Join-Path $RepoRoot "산출물\운영PC\visualstudio"
$VsixName = "source-trace-visualstudio-0.1.0.vsix"
$localDotnet = Join-Path $Root ".tools\dotnet\dotnet.exe"
if (Test-Path $localDotnet) {
  $env:PATH = (Split-Path -Parent $localDotnet) + ";" + $env:PATH
  $env:DOTNET_ROOT = Split-Path -Parent $localDotnet
}
$dotnet = if (Test-Path $localDotnet) { $localDotnet } else { "dotnet" }

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

function Find-MSBuild {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  return $null
}

Write-Host "== Visual Studio / MSBuild =="
$msbuild = Find-MSBuild
if ($msbuild) { Write-Host "MSBuild:" $msbuild; & $msbuild -version } else { Write-Host "WARN: MSBuild not in PATH (using dotnet msbuild + VSSDK NuGet)" }

Write-Host "== Core unit tests =="
$testProj = Join-Path $Root "tests\CoreUnitTests\CoreUnitTests.csproj"
& $dotnet build $testProj -c Release --nologo -v q
if ($LASTEXITCODE -ne 0) { Fail "Core unit tests build failed." }
$testExe = Join-Path $Root "tests\CoreUnitTests\bin\Release\net472\CoreUnitTests.exe"
& $testExe
if ($LASTEXITCODE -ne 0) { Fail "Core unit tests failed." }

Write-Host "== Release VSIX build =="
$vsProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio\Atec.SourceTrace.VisualStudio.csproj"
$vsProjDir = Split-Path -Parent $vsProj
Push-Location $vsProjDir
try {
  & $dotnet restore (Split-Path -Leaf $vsProj)
  & $dotnet msbuild (Split-Path -Leaf $vsProj) /t:Build,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "VSIX build failed." }
} finally {
  Pop-Location
}

$builtVsix = Get-ChildItem $vsProjDir -Recurse -Filter $VsixName -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $builtVsix) {
  $builtVsix = Get-ChildItem $vsProjDir -Recurse -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $builtVsix) { Fail "VSIX output not found." }
Write-Host "OK VSIX:" $builtVsix.FullName

Write-Host "== VSIX sanity =="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($builtVsix.FullName)
try {
  if (-not ($zip.Entries | Where-Object { $_.FullName -eq "extension.vsixmanifest" })) { Fail "extension.vsixmanifest missing inside VSIX." }
  if (-not ($zip.Entries | Where-Object { $_.FullName -like "*Atec.SourceTrace*.dll" })) { Fail "Extension DLL missing inside VSIX." }
} finally {
  $zip.Dispose()
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix.FullName $VsixName
if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }

Write-Host "== SUCCESS =="
Write-Host (Join-Path $OutDir $VsixName)
Write-Host (Join-Path $DeliverDir $VsixName)
