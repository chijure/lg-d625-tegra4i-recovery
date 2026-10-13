param(
    [string]$TegraRcm,
    [string]$Readback
)
$ErrorActionPreference = 'Stop'
$recoveryRoot = Split-Path -Parent $PSScriptRoot
if (-not $TegraRcm) {
    $TegraRcm = Join-Path $recoveryRoot 'private/tools/tegrarcm_debug_RAWWRITE.exe'
}
if (-not $Readback) {
    $Readback = Join-Path $recoveryRoot ('out/bootstrap-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.bin')
}
$recoveryPython = Join-Path $recoveryRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $recoveryPython)) {
    throw 'Create the repository Python .venv first, as described in docs/RECOVERY.md'
}
& $recoveryPython (Join-Path $PSScriptRoot 'build_payload.py')
if ($LASTEXITCODE -ne 0) { throw 'Payload validation failed' }
$recoveryInputs = @(
    $TegraRcm,
    (Join-Path $recoveryRoot 'out/t148_nvflash_miniloader_ARMV4_RECOVERY.bin'),
    (Join-Path $recoveryRoot 'private/backups/bct-original-slot.cfg'),
    (Join-Path $recoveryRoot 'private/backups/bootloader-original.bin')
)
foreach ($recoveryInput in $recoveryInputs) {
    if (-not (Test-Path -LiteralPath $recoveryInput)) { throw "Missing local input: $recoveryInput" }
}
if (Test-Path -LiteralPath $Readback) { throw 'Readback output already exists' }
# Legacy CLI requires BCT/BL flags; --rawread returns before either upload.
& $TegraRcm "--miniloader=$($recoveryInputs[1])" '--miniloader_entry=0x4000e000' `
    "--bct=$($recoveryInputs[2])" "--bootloader=$($recoveryInputs[3])" '--loadaddr=0x80108000' `
    "--rawread=$Readback" '--rawreadsector=128' '--rawreadcount=12' '--usb-timeout=10000'
if ($LASTEXITCODE -ne 0) { throw 'Miniloader bootstrap read failed' }
Write-Output "Recovery loader running; initial BCT read: $Readback"
