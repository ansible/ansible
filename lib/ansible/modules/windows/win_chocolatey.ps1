#!powershell

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# WANT_JSON
# POWERSHELL_COMMON

$ErrorActionPreference = 'Stop'

# As of chocolatey 0.9.10, non-zero success exit codes can be returned
# See https://github.com/chocolatey/choco/issues/512#issuecomment-214284461
$successexitcodes = (0, 1605, 1614, 1641, 3010)

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$verbosity = Get-AnsibleParam -obj $params -name "_ansible_verbosity" -type "int" -default 0

$package = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
$upgrade = Get-AnsibleParam -obj $params -name "upgrade" -type "bool" -default $false
$version = Get-AnsibleParam -obj $params -name "version" -type "str"
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$showlog = Get-AnsibleParam -obj $params -name "showlog" -type "bool" -default $false
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 2700 -aliases "execution_timeout"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","downgrade","latest","present","reinstalled"
$installargs = Get-AnsibleParam -obj $params -name "install_args" -type "str"
$packageparams = Get-AnsibleParam -obj $params -name "params" -type "str"
$allowemptychecksums = Get-AnsibleParam -obj $params -name "allow_empty_checksums" -type "bool" -default $false
$ignorechecksums = Get-AnsibleParam -obj $params -name "ignore_checksums" -type "bool" -default $false
$ignoredependencies = Get-AnsibleParam -obj $params -name "ignore_dependencies" -type "bool" -default $false
$skipscripts = Get-AnsibleParam -obj $params -name "skip_scripts" -type "bool" -default $false
$proxy_url = Get-AnsibleParam -obj $params -name "proxy_url" -type "str"
$proxy_username = Get-AnsibleParam -obj $params -name "proxy_username" -type "str"
$proxy_password = Get-AnsibleParam -obj $params -name "proxy_password" -type "str" -failifempty ($proxy_username -ne $null)

$result = @{
    changed = $false
}

if ($upgrade)
{
    Add-DeprecationWarning -obj $result -message "Parameter upgrade=yes is replaced with state=latest" -version 2.6
    if ($state -eq "present")
    {
        $state = "latest"
    }
}

Function Chocolatey-Install-Upgrade
{
    [CmdletBinding()]

    param()

    $ChocoAlreadyInstalled = Get-Command -Name "choco.exe" -ErrorAction SilentlyContinue
    if ($ChocoAlreadyInstalled -eq $null)
    {

        #We need to install chocolatey
        $wc = New-Object System.Net.WebClient;
        if ($proxy_url)
        {
            #We need to configure proxy
            $env:chocolateyProxyLocation = $proxy_url
            $wp = New-Object System.Net.WebProxy($proxy_url, $true);
            $wc.proxy = $wp;
            if ($proxy_username -and $proxy_password) {
                $env:chocolateyProxyUser = $proxy_username
                $env:chocolateyProxyPassword = $proxy_password
                $passwd = ConvertTo-SecureString $proxy_password -AsPlainText -Force
                $wp.Credentials = New-Object System.Management.Automation.PSCredential($proxy_username, $passwd)
            }
        }
        $install_output = $wc.DownloadString("https://chocolatey.org/install.ps1") | powershell -
        $result.rc = $LastExitCode
        $result.stdout = $install_output | Out-String
        if ($result.rc -ne 0) {
            # Deprecated below result output in v2.4, remove in v2.6
            $result.choco_bootstrap_output = $install_output
            Fail-Json -obj $result -message "Chocolatey bootstrap installation failed."
        }
        $result.changed = $true
        Add-Warning -obj $result -message "Chocolatey was missing from this system, so it was installed during this task run."

        # locate the newly installed choco.exe
        $command = Get-Command -Name "choco.exe" -ErrorAction SilentlyContinue
        if ($command)
        {
            $path = $command.Path
        }
        else
        {
            $env_value = $env:ChocolateyInstall
            if ($env_value)
            {
                $path = "$env_value\bin\choco.exe"
            }
            else
            {
                $path = "$env:SYSTEMDRIVE\ProgramData\Chocolatey\bin\choco.exe"
            }
        }
        if (-not (Test-Path -Path $path))
        {
            Fail-Json -obj $result -message "failed to find choco.exe, make sure it is added to the PATH or the env var ChocolateyInstall is set"
        }

        $script:executable = $path
    }
    else
    {

        $script:executable = "choco.exe"

        if ([Version](choco --version) -lt [Version]'0.10.5')
        {
            Add-Warning -obj $result -message "Chocolatey was older than v0.10.5, so it was upgraded during this task run."
            $script:options = @( "-dv" )
            Choco-Upgrade -package chocolatey  -proxy_url $proxy_url -proxy_username $proxy_username -proxy_password $proxy_password
        }
    }

    # set the default verbosity options
    if ($verbosity -gt 4) {
        Add-Warning -obj $result -message "Debug output enabled."
        $script:options = @( "-dv", "--no-progress" )
    } elseif ($verbosity -gt 3) {
        $script:options = @( "-v", "--no-progress" )
#    } elseif ($verbosity -gt 2) {
#        $script:options = @( "--no-progress" )
    } else {
        $script:options = @( "-r", "--no-progress" )
    }
}


Function Choco-IsInstalled
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true)]
        [string]$package
    )

    if ($package -eq "all") {
        return $true
    }

    $options = @( "--local-only", "--exact", $package )

    # NOTE: Chocolatey does not use stderr except for help output
    Try {
        $output = & $script:executable list $options
    } Catch {
        Fail-Json -obj $result -message "Error checking installation status for package 'package': $($_.Exception.Message)"
    }

    if ($LastExitCode -ne 0) {
        $result.rc = $LastExitCode
        $result.command =  "$script:executable list $options"
        $result.stdout = $output | Out-String
        # Deprecated below result output in v2.4, remove in v2.6
        $result.choco_error_cmd = $result.command
        $result.choco_error_log = $output
        Fail-Json -obj $result -message "Error checking installation status for $package 'package'"
    }

    If ("$output" -match "(\d+) packages installed.")
    {
        return $matches[1] -gt 0
    }

    return $false
}

Function Choco-Upgrade
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true)]
        [string] $package,
        [string] $version,
        [bool] $force,
        [int] $timeout,
        [bool] $skipscripts,
        [string] $source,
        [string] $installargs,
        [string] $packageparams,
        [bool] $allowemptychecksums,
        [bool] $ignorechecksums,
        [bool] $ignoredependencies,
        [bool] $allowdowngrade,
        [string] $proxy_url,
        [string] $proxy_username,
        [string] $proxy_password
    )

    if (-not (Choco-IsInstalled $package))
    {
        Fail-Json -obj @{} -message "Package '$package' is not installed, you cannot upgrade"
    }

    $options = @( "-y", $package, "--timeout", "$timeout", "--failonunfound" )

    if ($check_mode)
    {
        $options += "--whatif"
    }

    if ($version)
    {
        $options += "--version", $version
    }

    if ($source)
    {
        $options += "--source", $source
    }

    if ($force)
    {
        $options += "--force"
    }

    if ($installargs)
    {
        $options += "--installargs", $installargs
    }

    if ($packageparams)
    {
        $options += "--params", $packageparams
    }

    if ($allowemptychecksums)
    {
        $options += "--allow-empty-checksums"
    }

    if ($ignorechecksums)
    {
        $options += "--ignore-checksums"
    }

    if ($ignoredependencies)
    {
        $options += "--ignoredependencies"
    }

    if ($skipscripts)
    {
        $options += "--skip-scripts"
    }

    if ($allowdowngrade)
    {
        $options += "--allow-downgrade"
    }

    if ($proxy_url)
    {
        $options += "--proxy=`"'$proxy_url'`""
    }

    if ($proxy_username)
    {
        $options += "--proxy-user=`"'$proxy_username'`""
    }

    if ($proxy_password)
    {
        $options += "--proxy-password=`"'$proxy_password'`""
    }

    # NOTE: Chocolatey does not use stderr except for help output
    Try {
        $output = & $script:executable upgrade $script:options $options
    } Catch {
        Fail-Json -obj $result -message "Error upgrading package '$package': $($_.Exception.Message)"
    }

    $result.rc = $LastExitCode

    if ($result.rc -notin $successexitcodes) {
        $result.command =  "$script:executable upgrade $script:options $options"
        $result.stdout = $output | Out-String
        # Deprecated below result output in v2.4, remove in v2.6
        $result.choco_error_cmd = $result.command
        $result.choco_error_log = $output
        Fail-Json -obj $result -message "Error upgrading package '$package'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $output | Out-String
    }

    if ("$output" -match ' upgraded (\d+)/\d+ package')
    {
        if ($matches[1] -gt 0)
        {
            $result.changed = $true
        }
    }
    $result.failed = $false
}

Function Choco-Install
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true)]
        [string] $package,
        [string] $version,
        [bool] $force,
        [int] $timeout,
        [bool] $skipscripts,
        [string] $source,
        [string] $installargs,
        [string] $packageparams,
        [bool] $allowemptychecksums,
        [bool] $ignorechecksums,
        [bool] $ignoredependencies,
        [bool] $allowdowngrade,
        [string] $proxy_url,
        [string] $proxy_username,
        [string] $proxy_password
    )

    if (Choco-IsInstalled $package)
    {
        if ($state -in ("downgrade", "latest"))
        {
            Choco-Upgrade -package $package -version $version -force $force -timeout $timeout `
                -skipscripts $skipscripts -source $source -installargs $installargs `
                -packageparams $packageparams -allowemptychecksums $allowemptychecksums `
                -ignorechecksums $ignorechecksums -ignoredependencies $ignoredependencies `
                -allowdowngrade $allowdowngrade -proxy_url $proxy_url `
                -proxy_username $proxy_username -proxy_password $proxy_password
            return
        }
        elseif (-not $force)
        {
            return
        }
    }

    $options = @( "-y", $package, "--timeout", "$timeout", "--failonunfound" )

    if ($check_mode)
    {
        $options += "--whatif"
    }

    if ($version)
    {
        $options += "--version", $version
    }

    if ($source)
    {
        $options += "--source", $source
    }

    if ($force)
    {
        $options += "--force"
    }

    if ($installargs)
    {
        $options += "--installargs", $installargs
    }

    if ($packageparams)
    {
        $options += "--params", $packageparams
    }

    if ($allowemptychecksums)
    {
        $options += "--allow-empty-checksums"
    }

    if ($ignorechecksums)
    {
        $options += "--ignore-checksums"
    }

    if ($ignoredependencies)
    {
        $options += "--ignoredependencies"
    }

    if ($skipscripts)
    {
        $options += "--skip-scripts"
    }

    if ($proxy_url)
    {
        $options += "--proxy=`"'$proxy_url'`""
    }

    if ($proxy_username)
    {
        $options += "--proxy-user=`"'$proxy_username'`""
    }

    if ($proxy_password)
    {
        $options += "--proxy-password=`"'$proxy_password'`""
    }

    # NOTE: Chocolatey does not use stderr except for help output
    Try {
        $output = & $script:executable install $script:options $options
    } Catch {
        Fail-Json -obj $result -message "Error installing package '$package': $($_.Exception.Message)"
    }

    $result.rc = $LastExitCode

    if ($result.rc -notin $successexitcodes) {
        $result.command =  "$script:executable install $script:options $options"
        $result.stdout = $output | Out-String
        # Deprecated below result output in v2.4, remove in v2.6
        $result.choco_error_cmd = $result.command
        $result.choco_error_log = $output
        Fail-Json -obj $result -message "Error installing package '$package'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $output | Out-String
    }

    $result.changed = $true
    $result.failed = $false
}

Function Choco-Uninstall
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true)]
        [string] $package,
        [string] $version,
        [bool] $force,
        [int] $timeout,
        [bool] $skipscripts
    )

    if (-not (Choco-IsInstalled $package))
    {
        return
    }

    $options = @( "-y", $package, "--timeout", "$timeout" )

    if ($check_mode)
    {
        $options += "--whatif"
    }

    if ($version)
    {
        $options += "--version", $version
    }

    if ($force)
    {
        $options += "--force"
    }

    if ($packageparams)
    {
        $options += "--params", $packageparams
    }

    if ($skipscripts)
    {
        $options += "--skip-scripts"
    }

    # NOTE: Chocolatey does not use stderr except for help output
    Try {
        $output = & $script:executable uninstall $script:options $options
    } Catch {
        Fail-Json -obj $result -message "Error uninstalling package '$package': $($_.Exception.Message)"
    }

    $result.rc = $LastExitCode

    if ($result.rc -notin $successexitcodes) {
        $result.command =  "$script:executable uninstall $script:options $options"
        $result.stdout = $output | Out-String
        # Deprecated below result output in v2.4, remove in v2.6
        $result.choco_error_cmd = $result.command
        $result.choco_error_log = $output
        Fail-Json -obj $result -message "Error uninstalling package '$package'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $output | Out-String
    }

    $result.changed = $true
    $result.failed = $false
}

Chocolatey-Install-Upgrade

if ($state -in ("absent", "reinstalled")) {

    Choco-Uninstall -package $package -version $version -force $force -timeout $timeout `
        -skipscripts $skipscripts

}

if ($state -in ("downgrade", "latest", "present", "reinstalled")) {

    Choco-Install -package $package -version $version -force $force -timeout $timeout `
        -skipscripts $skipscripts -source $source -installargs $installargs `
        -packageparams $packageparams -allowemptychecksums $allowemptychecksums `
        -ignorechecksums $ignorechecksums -ignoredependencies $ignoredependencies `
        -allowdowngrade ($state -eq "downgrade") -proxy_url $proxy_url `
        -proxy_username $proxy_username -proxy_password $proxy_password
}

Exit-Json -obj $result
