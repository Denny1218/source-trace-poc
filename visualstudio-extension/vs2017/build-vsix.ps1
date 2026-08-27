# Headless build → source-trace-visualstudio2017-0.1.3.vsix (ops offline install).
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ExtRoot = Split-Path -Parent $Root
$RepoRoot = Split-Path -Parent $ExtRoot
$OutDir = Join-Path $Root "out"
$DeliverDir = Join-Path $RepoRoot "산출물\운영PC\visualstudio"
$VsixName = "source-trace-visualstudio2017-0.1.3.vsix"
$localDotnet = Join-Path $ExtRoot ".tools\dotnet\dotnet.exe"
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
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  return $null
}

Write-Host "== Visual Studio 2017 / MSBuild =="
$msbuild = Find-MSBuild
if ($msbuild) { Write-Host "MSBuild:" $msbuild; & $msbuild -version } else { Write-Host "WARN: VS2017 MSBuild not found (using dotnet msbuild + VSSDK 15 NuGet)" }

Write-Host "== VS2017 unit tests =="
$testProj = Join-Path $Root "tests\Vs2017UnitTests\Vs2017UnitTests.csproj"
& $dotnet build $testProj -c Release --nologo -v q
if ($LASTEXITCODE -ne 0) { Fail "VS2017 unit tests build failed." }
$testExe = Join-Path $Root "tests\Vs2017UnitTests\bin\Release\net46\Vs2017UnitTests.exe"
& $testExe
if ($LASTEXITCODE -ne 0) { Fail "VS2017 unit tests failed." }

Write-Host "== Release VSIX build =="
$vsProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017\Atec.SourceTrace.VisualStudio2017.csproj"
$vsProjDir = Split-Path -Parent $vsProj
Push-Location $vsProjDir
try {
  & $dotnet restore (Split-Path -Leaf $vsProj)
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $dotnet msbuild (Split-Path -Leaf $vsProj) /t:Build,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "VS2017 VSIX build failed." }
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
  $manifestEntry = $zip.Entries | Where-Object { $_.FullName -eq "extension.vsixmanifest" }
  if (-not $manifestEntry) { Fail "extension.vsixmanifest missing inside VSIX." }
  $sr = New-Object System.IO.StreamReader($manifestEntry.Open())
  try { $manifestText = $sr.ReadToEnd() } finally { $sr.Dispose() }
  if ($manifestText -notmatch '\[15\.0,16\.0\)') { Fail "InstallationTarget is not VS2017 15.x." }
  if ($manifestText -match 'amd64') { Fail "VS2017 VSIX must not force amd64 ProductArchitecture." }
  if ($manifestText -match '7c8f3a21') { Fail "VS2017 VSIX reused VS2022 identity." }
  if (-not ($zip.Entries | Where-Object { $_.FullName -like "*Atec.SourceTrace.VisualStudio2017*.dll" })) { Fail "Extension DLL missing inside VSIX." }
} finally {
  $zip.Dispose()
}

python (Join-Path (Split-Path -Parent $Root) "scripts\verify_ctmenu_resource.py") $builtVsix.FullName "VSPackage.resources" (Join-Path $vsProjDir "obj\Release\net46\AtecSourceTrace.cto")
if ($LASTEXITCODE -ne 0) { Fail "CTMENU managed resource verification failed." }

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix.FullName $VsixName
if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }

Write-Host "== SUCCESS =="
Write-Host (Join-Path $OutDir $VsixName)
Write-Host (Join-Path $DeliverDir $VsixName)
