$ErrorActionPreference = 'Stop'

$package_name = $env:ChocolateyPackageName
$package_version = $env:ChocolateyPackageVersion
$install_path = "--- PATH ---\$package_name-$package_version.txt"
$source = "--- SOURCE ---"  # used by the test to determine which source it was installed from

if ($env:ChocolateyAllowEmptyChecksums) {
    $allow_empty_checksums = $true
} else {
    $allow_empty_checksums = $false
}
if ($env:ChocolateyIgnoreChecksums) {
    $ignore_checksums = $true
} else {
    $ignore_checksums = $false
}
if ($env:ChocolateyForce) {
    $force = $true
} else {
    $force = $false
}
if ($env:ChocolateyForceX86) {
    $force_x86 = $true
} else {
    $force_x86 = $false
}
#$process_env = Get-EnvironmentVariableNames -Scope Process
#$env_vars = @{}
#foreach ($name in $process_env) {
#  $env_vars.$name = Get-EnvironmentVariable -Name $name -Scope Process
#}
$timeout = $env:chocolateyResponseTimeout

$package_info = @{
    allow_empty_checksums = $allow_empty_checksums
    #env_vars = $env_vars
    force = $force
    force_x86 = $force_x86
    ignore_checksums = $ignore_checksums
    install_args = $env:ChocolateyInstallArguments
    package_params = Get-PackageParameters
    proxy_url = $env:ChocolateyProxyLocation
    source = $source
    timeout = $timeout
}
$package_json = ConvertTo-Json -InputObject $package_info

[System.IO.File]::WriteAllText($install_path, $package_json)
