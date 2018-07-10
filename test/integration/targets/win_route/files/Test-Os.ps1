$os = [Environment]::OSVersion
$major = $os.Version.Major
$minor = $os.Version.Minor
$ok = $false

if(($major -gt 6)){
    $ok = $true
}
elseif (($major -eq 6) -and ($minor -ge 3)){
    $ok = $true
}

$ok