# Headless build → source-trace-visualstudio2017-menuprobe-0.0.1.vsix (diagnostic).
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ProbeProj = Join-Path $Root "src\Atec.SourceTrace.VisualStudio2017.MenuProbe\Atec.SourceTrace.VisualStudio2017.MenuProbe.csproj"
$ProbeDir = Split-Path -Parent $ProbeProj
$VsixName = "source-trace-visualstudio2017-menuprobe-0.0.1.vsix"
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

Write-Host "== VS2017 MenuProbe build =="
Push-Location $ProbeDir
try {
  & $dotnet restore (Split-Path -Leaf $ProbeProj)
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $dotnet msbuild (Split-Path -Leaf $ProbeProj) /t:Build,CreateVsixContainer /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /v:m
  if ($LASTEXITCODE -ne 0) { Fail "MenuProbe VSIX build failed." }
} finally {
  Pop-Location
}

$builtVsix = Get-ChildItem $ProbeDir -Recurse -Filter $VsixName -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $builtVsix) {
  $builtVsix = Get-ChildItem $ProbeDir -Recurse -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $builtVsix) { Fail "VSIX output not found." }
Write-Host "OK VSIX:" $builtVsix.FullName

python (Join-Path (Split-Path -Parent $Root) "scripts\verify_ctmenu_resource.py") $builtVsix.FullName "VSPackage.resources" (Join-Path $ProbeDir "obj\Release\net46\net46\MenuProbe.cto")
if ($LASTEXITCODE -ne 0) { Fail "CTMENU managed resource verification failed." }

python (Join-Path $Root "scripts\copy_vsix_deliverable.py") $builtVsix.FullName $VsixName
if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }

Write-Host "== SUCCESS =="
Write-Host $builtVsix.FullName
