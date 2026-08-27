param([string]$Path, [switch]$Dll)
Add-Type -AssemblyName System.Windows.Forms
if ($Dll) {
    $asm = [Reflection.Assembly]::ReflectionOnlyLoadFrom($Path)
    Write-Host "Manifest resources:" ($asm.GetManifestResourceNames() -join ", ")
    $stream = $asm.GetManifestResourceStream("VSPackage.resources")
} else {
    $stream = [IO.File]::OpenRead($Path)
}
$reader = New-Object System.Resources.ResourceReader($stream)
try {
    foreach ($entry in $reader) {
        $len = if ($entry.Value -is [byte[]]) { $entry.Value.Length } else { "n/a" }
        Write-Host "$($entry.Key) type=$($entry.Value.GetType().Name) size=$len"
    }
} finally {
    $reader.Close()
    $stream.Close()
}
