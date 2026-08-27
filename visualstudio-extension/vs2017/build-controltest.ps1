# Headless build -> source-trace-visualstudio2017-controltest-0.0.1.vsix (diagnostic known-good).
# Classic (non-SDK-style) csproj + Microsoft.VSSDK.BuildTools 15.9 + VS2017 MSBuild 15.
$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\sourcechangeTrace\visualstudio-extension\vs2017" }
$ProjDir = Join-Path $Root "src\ControlTest"
$Proj = Join-Path $ProjDir "ControlTest.csproj"
$VsixName = "source-trace-visualstudio2017-controltest-0.0.1.vsix"

# Avoid MAX_PATH during VS2017 NuGet restore of Microsoft.VisualStudio.SDK 15.0.1
$env:NUGET_PACKAGES = "c:\st-nuget"
New-Item -ItemType Directory -Force -Path $env:NUGET_PACKAGES | Out-Null

$MsBuildCandidates = @(
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe",
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\MSBuild.exe",
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
)
$msbuild = $MsBuildCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $msbuild) { Write-Host "ERROR: MSBuild not found." -ForegroundColor Red; exit 1 }

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

Write-Host "== VS2017 ControlTest (classic) build =="
Write-Host "MSBuild: $msbuild"
Write-Host "NUGET_PACKAGES: $env:NUGET_PACKAGES"
Push-Location $ProjDir
try {
  # Clear partial restore from previous long-path failure
  Remove-Item (Join-Path $ProjDir "obj") -Recurse -Force -ErrorAction SilentlyContinue
  & $msbuild $Proj /t:Restore /p:Configuration=Release /p:RestorePackagesPath=$env:NUGET_PACKAGES /v:m
  if ($LASTEXITCODE -ne 0) { Fail "NuGet restore failed." }
  & $msbuild $Proj /t:Rebuild /p:Configuration=Release /p:DeployExtension=false /p:CreateVsixContainer=true /p:VisualStudioVersion=15.0 /v:m
  if ($LASTEXITCODE -ne 0) { Fail "ControlTest VSIX build failed." }
} finally {
  Pop-Location
}

$builtVsix = Get-ChildItem $ProjDir -Recurse -Filter $VsixName -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $builtVsix) {
  $builtVsix = Get-ChildItem $ProjDir -Recurse -Filter "*.vsix" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $builtVsix) { Fail "VSIX output not found." }
Write-Host "OK VSIX:" $builtVsix.FullName

$verify = Join-Path (Split-Path -Parent $Root) "scripts\verify_ctmenu_resource.py"
$cto = Get-ChildItem $ProjDir -Recurse -Filter "ControlTest.cto" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ((Test-Path $verify) -and $cto) {
  python $verify $builtVsix.FullName "VSPackage.resources" $cto.FullName
  if ($LASTEXITCODE -ne 0) { Fail "CTMENU managed resource verification failed." }
}

$copy = Join-Path $Root "scripts\copy_vsix_deliverable.py"
if (Test-Path $copy) {
  python $copy $builtVsix.FullName $VsixName
  if ($LASTEXITCODE -ne 0) { Fail "Deliverable copy failed." }
}

Write-Host "== SUCCESS =="
Write-Host $builtVsix.FullName
