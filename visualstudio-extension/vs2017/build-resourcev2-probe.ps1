# Diagnostic A/B only: ResourceVersion2 probe (NOT official 0.1.3).
# Single variable vs Source Trace 0.1.2: ProvideMenuResource(..., 2). VSCT unchanged.
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ExtRoot = Split-Path -Parent $Root
$VsixName = "source-trace-visualstudio2017-resourcev2-probe.vsix"
$BaselineVsix = Join-Path $Root "out\source-trace-visualstudio2017-0.1.2.vsix"
if (-not (Test-Path $BaselineVsix)) {
  $BaselineVsix = Join-Path $ExtRoot "out\source-trace-visualstudio2017-0.1.2.vsix"
}
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

$vsProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017\Atec.SourceTrace.VisualStudio2017.csproj"
$vsProjDir = Split-Path -Parent $vsProj

Write-Host "== ResourceVersion2 probe build (diagnostic) =="
Push-Location $vsProjDir
try {
  & $dotnet restore (Split-Path -Leaf $vsProj)
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $dotnet msbuild (Split-Path -Leaf $vsProj) /t:Rebuild,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "ResourceV2 probe VSIX build failed." }
} finally {
  Pop-Location
}

$builtVsix = Get-ChildItem $vsProjDir -Recurse -Filter $VsixName -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $builtVsix) { Fail "VSIX not found: $VsixName" }
Write-Host "OK VSIX:" $builtVsix.FullName

Add-Type -AssemblyName System.IO.Compression.FileSystem
$tmp = Join-Path $env:TEMP "resourcev2_probe_unzip"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
[IO.Compression.ZipFile]::ExtractToDirectory($builtVsix.FullName, $tmp)
$pkgdef = Get-ChildItem $tmp -Filter "*.pkgdef" | Select-Object -First 1
if (-not $pkgdef) { Fail "pkgdef missing in VSIX" }
$pkgText = Get-Content $pkgdef.FullName -Encoding Unicode -Raw
Write-Host "--- pkgdef (Packages / Menus) ---"
($pkgText -split "`r?`n") | Where-Object { $_ -match 'Menus|e4b17c90|Packages\\' } | ForEach-Object { $_.TrimEnd() }

if ($pkgText -notmatch 'e4b17c90-6a2f-4d8e-9c11-7f8a2b3c4d5e') { Fail "Package GUID mismatch" }
if ($pkgText -notmatch 'Menus\.ctmenu, 2') { Fail "pkgdef Menus version is not 2 (attribute->pkgdef failed)" }
Write-Host "OK  generated pkgdef: , Menus.ctmenu, 2"
Write-Host "OK  Package GUID unchanged {e4b17c90-6a2f-4d8e-9c11-7f8a2b3c4d5e}"

# Fail loudly if VSIX somehow still packs version 1 (stale Intermediate pkgdef)
$tmpCheck = Join-Path $env:TEMP "rv2_vsix_menus_check"
if (Test-Path $tmpCheck) { Remove-Item $tmpCheck -Recurse -Force }
[IO.Compression.ZipFile]::ExtractToDirectory($builtVsix.FullName, $tmpCheck)
$vsixMenus = (Get-Content (Get-ChildItem $tmpCheck -Filter *.pkgdef).FullName -Encoding Unicode | Select-String "Menus.ctmenu").Line
if ($vsixMenus -notmatch ', 2') { Fail "VSIX packed stale Menus version: $vsixMenus" }
Write-Host "OK  VSIX packed: $vsixMenus"

$pkgCs = Get-Content (Join-Path $vsProjDir "AtecSourceTracePackage.cs") -Raw
if ($pkgCs -notmatch 'ProvideMenuResource\("Menus\.ctmenu", 2\)') { Fail "source attribute not version 2" }

$vsct = Get-Content (Join-Path $vsProjDir "AtecSourceTrace.vsct") -Raw
if ($vsct -notmatch 'IDM_VS_MENU_TOOLS') { Fail "Tools parent missing" }
if ($vsct -notmatch 'IDM_VS_CTXT_CODEWIN') { Fail "context menu unexpectedly removed" }
if ($vsct -notmatch 'AtecSubMenuMain') { Fail "Tools submenu unexpectedly removed" }

$ctoProbe = Get-ChildItem $vsProjDir -Recurse -Filter "AtecSourceTrace.cto" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $ctoProbe) { Fail "probe .cto not found" }

if (-not (Test-Path $BaselineVsix)) {
  Fail "baseline 0.1.2 VSIX missing for CTO compare: $BaselineVsix"
}
python (Join-Path $Root "scripts\compare_ctmenu_sha.py") $builtVsix.FullName $BaselineVsix
if ($LASTEXITCODE -ne 0) { Fail "CTMENU hash compare failed" }

python (Join-Path $ExtRoot "scripts\verify_ctmenu_resource.py") $builtVsix.FullName "VSPackage.resources" $ctoProbe.FullName
if ($LASTEXITCODE -ne 0) { Fail "CTMENU embed verify failed" }

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix.FullName $VsixName
if ($LASTEXITCODE -ne 0) { Fail "deliverable copy failed" }

Write-Host ""
Write-Host "== SUCCESS (diagnostic ResourceVersion2 probe) =="
Write-Host $builtVsix.FullName
Write-Host "NOT an official 0.1.3 release."
Write-Host "PC: install probe -> devenv /setup -> Tools -> ATEC Source Trace"
