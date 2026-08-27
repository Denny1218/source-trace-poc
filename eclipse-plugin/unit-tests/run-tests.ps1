# Compiles core package + runs zero-dep unit tests (JDK 17+).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pluginSrc = Join-Path $root "com.atec.sourcetrace.eclipse\src"
$testSrc = Join-Path $PSScriptRoot "src"
$out = Join-Path $PSScriptRoot "out"
$coreOut = Join-Path $out "core"
$testOut = Join-Path $out "tests"

function Find-Java {
  if ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\javac.exe")) {
    return "$env:JAVA_HOME\bin"
  }
  $candidates = @(
    "C:\Program Files\Microsoft\jdk-17*\bin",
    "C:\Program Files\Eclipse Adoptium\jdk-17*\bin",
    "C:\Program Files\Java\jdk-17*\bin"
  )
  foreach ($pattern in $candidates) {
    $hit = Get-ChildItem $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit -and (Test-Path (Join-Path $hit.FullName "javac.exe"))) {
      return $hit.FullName
    }
  }
  $cmd = Get-Command javac -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path $cmd.Source }
  return $null
}

$javaBin = Find-Java
if (-not $javaBin) {
  Write-Error "JDK 17+ (javac) not found. Install OpenJDK 17 and re-run."
}

New-Item -ItemType Directory -Force -Path $coreOut, $testOut | Out-Null
$coreFiles = Get-ChildItem -Path (Join-Path $pluginSrc "com\atec\sourcetrace\eclipse\core") -Filter *.java
& "$javaBin\javac.exe" -encoding UTF-8 -d $coreOut $coreFiles.FullName
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$javaBin\javac.exe" -encoding UTF-8 -cp $coreOut -d $testOut (Join-Path $testSrc "CoreUnitTests.java")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$javaBin\java.exe" -cp "$coreOut;$testOut" CoreUnitTests
exit $LASTEXITCODE
