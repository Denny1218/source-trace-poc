# Headless build -> source-trace-visualstudio2017-menuprobe-directtools-0.0.2.vsix
# Single-variable A/B vs MenuProbe 0.0.1: VSCT Tools parent = IDM_VS_MENU_TOOLS only.
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ProbeProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017.MenuProbe.DirectTools\Atec.SourceTrace.VisualStudio2017.MenuProbe.DirectTools.csproj"
$ProbeDir = Split-Path -Parent $ProbeProj
$VsixName = "source-trace-visualstudio2017-menuprobe-directtools-0.0.2.vsix"
$localDotnet = Join-Path (Split-Path -Parent $Root) ".tools\dotnet\dotnet.exe"
if (Test-Path $localDotnet) {
  $env:PATH = (Split-Path -Parent $localDotnet) + ";" + $env:PATH
  $env:DOTNET_ROOT = Split-Path -Parent $localDotnet
}
$dotnet = if (Test-Path $localDotnet) { $localDotnet } else { "dotnet" }

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

Write-Host "== VS2017 MenuProbe DirectTools (parent-only) build =="
Push-Location $ProbeDir
try {
  & $dotnet restore (Split-Path -Leaf $ProbeProj)
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $dotnet msbuild (Split-Path -Leaf $ProbeProj) /t:Build,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "MenuProbe DirectTools VSIX build failed." }
} finally {
  Pop-Location
}

$builtVsix = Get-ChildItem $ProbeDir -Recurse -Filter $VsixName -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $builtVsix) {
  $builtVsix = Get-ChildItem $ProbeDir -Recurse -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $builtVsix) { Fail "VSIX output not found." }
Write-Host "OK VSIX:" $builtVsix.FullName

$cto = Join-Path $ProbeDir "obj\Release\net46\net46\MenuProbe.cto"
if (-not (Test-Path $cto)) {
  $ctoObj = Get-ChildItem $ProbeDir -Recurse -Filter "MenuProbe.cto" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($ctoObj) { $cto = $ctoObj.FullName }
}
python (Join-Path (Split-Path -Parent $Root) "scripts\verify_ctmenu_resource.py") $builtVsix.FullName "VSPackage.resources" $cto
if ($LASTEXITCODE -ne 0) { Fail "CTMENU managed resource verification failed." }

# Confirm vsct parent is IDM_VS_MENU_TOOLS and original MenuProbe still has ADDINS
$vsctNew = Get-Content (Join-Path $ProbeDir "MenuProbe.vsct") -Raw
$vsctOld = Get-Content (Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017.MenuProbe\MenuProbe.vsct") -Raw
if ($vsctNew -notmatch 'IDM_VS_MENU_TOOLS') { Fail "DirectTools vsct missing IDM_VS_MENU_TOOLS" }
if ($vsctNew -match 'IDG_VS_MM_TOOLSADDINS') { Fail "DirectTools vsct still has IDG_VS_MM_TOOLSADDINS" }
if ($vsctOld -notmatch 'IDG_VS_MM_TOOLSADDINS') { Fail "Original MenuProbe 0.0.1 vsct was unexpectedly changed" }

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix.FullName $VsixName
if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }

Write-Host "== SUCCESS =="
Write-Host $builtVsix.FullName
Write-Host "Unchanged: MenuProbe 0.0.1 source (IDG_VS_MM_TOOLSADDINS)"
Write-Host "Changed:   DirectTools 0.0.2 VSCT parent only -> IDM_VS_MENU_TOOLS"
