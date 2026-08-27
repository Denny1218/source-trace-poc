# Headless Maven+Tycho build → binary p2 Update Site ZIP for ops Eclipse (no PDE).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "pom.xml"))) {
  $Root = "c:\sourcechangeTrace\eclipse-plugin"
}
$RepoRoot = Split-Path -Parent $Root
$env:PYTHONIOENCODING = "utf-8"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

# Java
$java = Get-Command java -ErrorAction SilentlyContinue
if (-not $java) { Fail "Java not found. Need JDK 17+." }
Write-Host "== Java =="
java -version 2>&1 | ForEach-Object { Write-Host $_ }

# Maven (prefer local .tools)
$mvnCmd = $null
$localMvn = Get-ChildItem (Join-Path $Root ".tools") -Directory -Filter "apache-maven-*" -ErrorAction SilentlyContinue |
  Select-Object -First 1
if ($localMvn -and (Test-Path (Join-Path $localMvn.FullName "bin\mvn.cmd"))) {
  $mvnCmd = Join-Path $localMvn.FullName "bin\mvn.cmd"
} else {
  $sys = Get-Command mvn -ErrorAction SilentlyContinue
  if ($sys) { $mvnCmd = $sys.Source }
}
if (-not $mvnCmd) { Fail "Maven not found. Place apache-maven under eclipse-plugin/.tools or install mvn." }
Write-Host "== Maven =="
& $mvnCmd -version

# Unit tests (core)
Write-Host "== Core unit tests =="
$testScript = Join-Path $Root "unit-tests\run-tests.ps1"
if (Test-Path $testScript) {
  powershell -ExecutionPolicy Bypass -File $testScript
  if ($LASTEXITCODE -ne 0) { Fail "Core unit tests failed." }
} else {
  Write-Host "WARN: unit-tests/run-tests.ps1 missing — skip"
}

# Tycho build
Write-Host "== Tycho build =="
Push-Location $Root
try {
  & $mvnCmd -B clean verify
  if ($LASTEXITCODE -ne 0) { Fail "Tycho build failed." }
} finally {
  Pop-Location
}

$repoDir = Join-Path $Root "update-site\target\repository"
if (-not (Test-Path $repoDir)) { Fail "p2 repository not found: $repoDir" }

# Structure check
$need = @("content.jar", "artifacts.jar", "features", "plugins")
foreach ($n in $need) {
  $p = Join-Path $repoDir $n
  if (-not (Test-Path $p)) {
    # allow .xml uncompressed variants
    if ($n -eq "content.jar" -and (Test-Path (Join-Path $repoDir "content.xml"))) { continue }
    if ($n -eq "artifacts.jar" -and (Test-Path (Join-Path $repoDir "artifacts.xml"))) { continue }
    Fail "Missing repository entry: $n"
  }
}
$pluginJars = Get-ChildItem (Join-Path $repoDir "plugins") -Filter "com.atec.sourcetrace.eclipse_*.jar" -ErrorAction SilentlyContinue
$featureJars = Get-ChildItem (Join-Path $repoDir "features") -Filter "com.atec.sourcetrace.eclipse.feature_*.jar" -ErrorAction SilentlyContinue
if (-not $pluginJars) { Fail "Plug-in JAR missing under plugins/" }
if (-not $featureJars) { Fail "Feature JAR missing under features/" }
Write-Host "OK plugin:" $pluginJars.Name
Write-Host "OK feature:" $featureJars.Name

# Zip binary update site into 산출물/운영PC/eclipse (UTF-8 paths via Python)
Write-Host "== Package binary Update Site ZIP =="
python (Join-Path $Root "scripts\package_binary_update_site.py")
if ($LASTEXITCODE -ne 0) { Fail "Binary ZIP packaging failed." }
Write-Host "== SUCCESS: binary Update Site ZIP ready =="
Write-Host (Join-Path $RepoRoot "산출물\운영PC\eclipse\source-trace-eclipse-update-site-0.1.1.zip")
