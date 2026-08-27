# Headless build → source-trace-visualstudio2010-0.1.3.vsix (VS2010 VSIX 1.0).
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2010" }
$ExtRoot = Split-Path -Parent $Root
$RepoRoot = Split-Path -Parent $ExtRoot
$OutDir = Join-Path $Root "out"
$DeliverDir = Join-Path $RepoRoot "산출물\운영PC\visualstudio"
$VsixName = "source-trace-visualstudio2010-0.1.3.vsix"
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

Write-Host "== Visual Studio 2010 headless build =="
Write-Host "Target: VS 2010 / 10.0  VSIX schema 1.0  net40"

Write-Host "== VS2010 unit tests =="
$testProj = Join-Path $Root "tests\Vs2010UnitTests\Vs2010UnitTests.csproj"
& $dotnet build $testProj -c Release --nologo -v q
if ($LASTEXITCODE -ne 0) { Fail "VS2010 unit tests build failed." }
$testExe = Join-Path $Root "tests\Vs2010UnitTests\bin\Release\net40\Vs2010UnitTests.exe"
& $testExe
if ($LASTEXITCODE -ne 0) { Fail "VS2010 unit tests failed." }

Write-Host "== Release build =="
$vsProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2010\Atec.SourceTrace.VisualStudio2010.csproj"
$vsProjDir = Split-Path -Parent $vsProj
Push-Location $vsProjDir
try {
  & $dotnet restore (Split-Path -Leaf $vsProj)
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $dotnet msbuild (Split-Path -Leaf $vsProj) /t:Build /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=false /v:m
  if ($LASTEXITCODE -ne 0) { Fail "VS2010 extension build failed." }
} finally {
  Pop-Location
}

Write-Host "== Pack VSIX 1.0 =="
$builtVsix = Join-Path $vsProjDir $VsixName
python (Join-Path $Root "scripts\pack_vsix.py") $vsProjDir $builtVsix
if ($LASTEXITCODE -ne 0) { Fail "VSIX pack failed." }

python (Join-Path (Split-Path -Parent $Root) "scripts\verify_ctmenu_resource.py") $builtVsix "VSPackage.resources" (Join-Path $vsProjDir "obj\Release\net40\AtecSourceTrace.cto")
if ($LASTEXITCODE -ne 0) { Fail "CTMENU managed resource verification failed." }

Write-Host "== VSIX sanity =="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($builtVsix)
try {
  $names = $zip.Entries | ForEach-Object { $_.FullName }
  if (-not ($names -contains "extension.vsixmanifest")) { Fail "extension.vsixmanifest missing." }
  if (-not ($names -contains "Atec.SourceTrace.VisualStudio2010.dll")) { Fail "extension DLL missing." }
  if (-not ($names -contains "Atec.SourceTrace.Core.dll")) { Fail "Core DLL missing." }
  if (-not ($names -contains "Atec.SourceTrace.VisualStudio2010.pkgdef")) { Fail "pkgdef missing." }
  $manifestEntry = $zip.Entries | Where-Object { $_.FullName -eq "extension.vsixmanifest" }
  $sr = New-Object System.IO.StreamReader($manifestEntry.Open())
  try { $manifestText = $sr.ReadToEnd() } finally { $sr.Dispose() }
  if ($manifestText -notmatch 'Version="1\.0\.0"') { Fail "Not VSIX 1.0 schema." }
  if ($manifestText -notmatch 'Version="10\.0"') { Fail "Installation target is not VS2010 10.0." }
  if ($manifestText -match 'PackageManifest') { Fail "VSIX 2.0 PackageManifest cannot install on VS2010." }
  if ($manifestText -match 'amd64') { Fail "VS2010 VSIX must not force amd64." }
  if ($manifestText -match '7c8f3a21|e4b17c90') { Fail "VS2010 VSIX reused a later VS identity." }
} finally {
  $zip.Dispose()
}

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix $VsixName
if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }

Write-Host "== SUCCESS =="
Write-Host (Join-Path $OutDir $VsixName)
Write-Host (Join-Path $DeliverDir $VsixName)
