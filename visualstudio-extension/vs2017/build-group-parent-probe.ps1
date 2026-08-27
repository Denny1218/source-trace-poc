# Diagnostic: official VSCT Menu→Group→Button parents (NOT official 0.1.3).
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ExtRoot = Split-Path -Parent $Root
$VsixName = "source-trace-visualstudio2017-group-parent-probe.vsix"
$vsProjDir = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017"
$localDotnet = Join-Path $ExtRoot ".tools\dotnet\dotnet.exe"
if (Test-Path $localDotnet) {
  $env:PATH = (Split-Path -Parent $localDotnet) + ";" + $env:PATH
  $env:DOTNET_ROOT = Split-Path -Parent $localDotnet
}
$dotnet = if (Test-Path $localDotnet) { $localDotnet } else { "dotnet" }

function Fail([string]$msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

Write-Host "== unit tests =="
& $dotnet build (Join-Path $Root "tests\Vs2017UnitTests\Vs2017UnitTests.csproj") -c Release --nologo -v q
if ($LASTEXITCODE -ne 0) { Fail "test build failed" }
& (Join-Path $Root "tests\Vs2017UnitTests\bin\Release\net46\Vs2017UnitTests.exe")
if ($LASTEXITCODE -ne 0) { Fail "unit tests failed" }

Write-Host "== rebuild group-parent probe =="
Remove-Item (Join-Path $vsProjDir "obj") -Recurse -Force -ErrorAction SilentlyContinue
Push-Location $vsProjDir
try {
  & $dotnet restore Atec.SourceTrace.VisualStudio2017.csproj -v q
  & $dotnet msbuild Atec.SourceTrace.VisualStudio2017.csproj /t:Rebuild,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "VSIX build failed" }
} finally { Pop-Location }

$built = Get-ChildItem $vsProjDir -Recurse -Filter $VsixName | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $built) { Fail "VSIX missing" }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$tmp = Join-Path $env:TEMP "group_parent_probe_unzip"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
[IO.Compression.ZipFile]::ExtractToDirectory($built.FullName, $tmp)
$pkg = Get-Content (Get-ChildItem $tmp -Filter *.pkgdef).FullName -Encoding Unicode -Raw
if ($pkg -notmatch 'Menus\.ctmenu, 3') { Fail "pkgdef Menus not version 3" }
if ($pkg -notmatch 'e4b17c90-6a2f-4d8e-9c11-7f8a2b3c4d5e') { Fail "Package GUID mismatch" }
Write-Host "OK  pkgdef Menus.ctmenu, 3"

$cto = Get-ChildItem $vsProjDir -Recurse -Filter AtecSourceTrace.cto | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python (Join-Path $ExtRoot "scripts\verify_ctmenu_resource.py") $built.FullName "VSPackage.resources" $cto.FullName
if ($LASTEXITCODE -ne 0) { Fail "CTMENU verify failed" }
Write-Host "CTO sha256=" ((Get-FileHash $cto.FullName -Algorithm SHA256).Hash.ToLower()) "size=$($cto.Length)"

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $built.FullName $VsixName
Write-Host "== SUCCESS (diagnostic) =="
Write-Host $built.FullName
Write-Host "NOT official 0.1.3. Install + devenv /setup then check Tools and context menus."
