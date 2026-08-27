$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
python (Join-Path $PSScriptRoot "package_source_bundle.py")
