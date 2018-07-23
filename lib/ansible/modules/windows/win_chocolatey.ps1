#!powershell

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

# As of chocolatey 0.9.10, non-zero success exit codes can be returned
# See https://github.com/chocolatey/choco/issues/512#issuecomment-214284461
$successexitcodes = (0, 1605, 1614, 1641, 3010)

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$verbosity = Get-AnsibleParam -obj $params -name "_ansible_verbosity" -type "int" -default 0

$name = Get-AnsibleParam -obj $params -name "name" -type "list" -failifempty $true

$allow_empty_checksums = Get-AnsibleParam -obj $params -name "allow_empty_checksums" -type "bool" -default $false
$allow_prerelease = Get-AnsibleParam -obj $params -name "allow_prerelease" -type "bool" -default $false
$architecture = Get-AnsibleParam -obj $params -name "architecture" -type "str" -default "default" -validateset "default", "x86"
$install_args = Get-AnsibleParam -obj $params -name "install_args" -type "str"
$ignore_checksums = Get-AnsibleParam -obj $params -name "ignore_checksums" -type "bool" -default $false
$ignore_dependencies = Get-AnsibleParam -obj $params -name "ignore_dependencies" -type "bool" -default $false
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
$package_params = Get-AnsibleParam -obj $params -name "package_params" -type "str" -aliases "params"
$proxy_url = Get-AnsibleParam -obj $params -name "proxy_url" -type "str"
$proxy_username = Get-AnsibleParam -obj $params -name "proxy_username" -type "str"
$proxy_password = Get-AnsibleParam -obj $params -name "proxy_password" -type "str" -failifempty ($null -ne $proxy_username)
$skip_scripts = Get-AnsibleParam -obj $params -name "skip_scripts" -type "bool" -default $false
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$source_username = Get-AnsibleParam -obj $params -name "source_username" -type "str"
$source_password = Get-AnsibleParam -obj $params -name "source_password" -type "str" -failifempty ($null -ne $source_username)
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","downgrade","latest","present","reinstalled"
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 2700 -aliases "execution_timeout"
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$version = Get-AnsibleParam -obj $params -name "version" -type "str"

$result = @{
    changed = $false
    rc = 0
}

if (-not $validate_certs) {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
}

Function Get-CommonChocolateyArguments {
    # uses global vars like check_mode and verbosity to control the common args
    # run with Chocolatey
    $arguments = [System.Collections.ArrayList]@("--yes", "--no-progress")
    # global vars that control the arguments
    if ($check_mode) {
        $arguments.Add("--what-if") > $null
    }
    if ($verbosity -gt 4) {
        $arguments.Add("--debug") > $null
        $arguments.Add("--verbose") > $null
    } elseif ($verbosity -gt 3) {
        $arguments.Add("--verbose") > $null
    } else {
        $arguments.Add("--limit-output") > $null
    }

    return ,$arguments
}

Function Get-InstallChocolateyArguments {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the cmdline, also using a SecureString here doesn't make sense considering the source is not secure")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    param(
        [bool]$allow_downgrade,
        [bool]$allow_empty_checksums,
        [bool]$allow_prerelease,
        [String]$architecture,
        [bool]$force,
        [bool]$ignore_dependencies,
        [String]$install_args,
        [String]$package_params,
        [String]$proxy_url,
        [String]$proxy_username,
        [String]$proxy_password,
        [bool]$skip_scripts,
        [String]$source,
        [String]$source_usename,
        [String]$source_password,
        [int]$timeout,
        [String]$version
    )
    # returns an ArrayList of common arguments for install/updated a Chocolatey
    # package
    $arguments = [System.Collections.ArrayList]@("--fail-on-unfound")
    $common_args = Get-CommonChocolateyArguments
    $arguments.AddRange($common_args)

    if ($allow_downgrade) {
        $arguments.Add("--allow-downgrade") > $null
    }
    if ($allow_empty_checksums) {
        $arguments.Add("--allow-empty-checksums") > $null
    }
    if ($allow_prerelease) {
        $arguments.Add("--prerelease") > $null
    }
    if ($architecture -eq "x86") {
        $arguments.Add("--x86") > $null
    }
    if ($force) {
        $arguments.Add("--force") > $null
    }
    if ($ignore_checksums) {
        $arguments.Add("--ignore-checksums") > $null
    }
    if ($ignore_dependencies) {
        $arguments.Add("--ignore-dependencies") > $null
    }
    if ($install_args) {
        $arguments.Add("--install-arguments") > $null
        $arguments.add($install_args) > $null
    }
    if ($package_params) {
        $arguments.Add("--package-parameters") > $null
        $arguments.Add($package_params) > $null
    }
    if ($proxy_url) {
        $arguments.Add("--proxy") > $null
        $arguments.Add($proxy_url) > $null
    }
    if ($proxy_username) {
        $arguments.Add("--proxy-user") > $null
        $arguments.Add($proxy_username) > $null
    }
    if ($proxy_password) {
        $arguments.Add("--proxy-password") > $null
        $arguments.Add($proxy_password) > $null
    }
    if ($skip_scripts) {
        $arguments.Add("--skip-scripts") > $null
    }
    if ($source) {
        $arguments.Add("--source") > $null
        $arguments.Add($source) > $null
    }
    if ($source_username) {
        $arguments.Add("--user") > $null
        $arguments.Add($source_username) > $null
        $arguments.Add("--password") > $null
        $arguments.Add($source_password) > $null
    }
    if ($null -ne $timeout) {
        $arguments.Add("--timeout") > $null
        $arguments.Add($timeout) > $null
    }
    if ($version) {
        $arguments.Add("--version") > $null
        $arguments.Add($version) > $null
    }

    return ,$arguments
}

Function Install-Chocolatey {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the env vars, also using a SecureString here doesn't make sense considering the source is not secure")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingConvertToSecureStringWithPlainText", "", Justification="See above")]
    param(
        [String]$proxy_url,
        [String]$proxy_username,
        [String]$proxy_password,
        [String]$source,
        [String]$source_username,
        [String]$source_password
    )

    $choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $choco_app) {
        # We need to install chocolatey
        # Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
        $security_protocols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
        if ([Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
            $security_protocols = $security_protcols -bor [Net.SecurityProtocolType]::Tls11
        }
        if ([Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
            $security_protocols = $security_protcols -bor [Net.SecurityProtocolType]::Tls12
        }
        [Net.ServicePointManager]::SecurityProtocol = $security_protocols

        $client = New-Object -TypeName System.Net.WebClient
        $environment = @{}
        if ($proxy_url) {
            # the env values are used in the install.ps1 script when getting
            # external dependencies
            $environment.chocolateyProxyLocation = $proxy_url
            $web_proxy = New-Object -TypeName System.Net.WebProxy -ArgumentList $proxy_url, $true
            $client.Proxy = $web_proxy
            if ($proxy_username -and $proxy_password) {
                $environment.chocolateyProxyUser = $proxy_username
                $environment.chocolateyProxyPassword = $proxy_password
                $sec_proxy_password = ConvertTo-SecureString -String $proxy_password -AsPlainText -Force
                $web_proxy.Credentials = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $proxy_username, $sec_proxy_password
            }
        }

        if ($source) {
            # check if the URL already contains the path to install.ps1
            if ($source.EndsWith("install.ps1")) {
                $script_url = $source
            } else {
                # chocolatey server automatically serves a script at
                # http://host/install.ps1, we rely on this behaviour when a
                # user specifies the choco source URL. If a custom URL or file
                # path is desired, they should use win_get_url/win_shell
                # manually
                # we need to strip the path off the URL and append install.ps1
                $uri_info = [System.Uri]$source
                $script_url = "$($uri_info.Scheme)://$($uri_info.Authority)/install.ps1"
            }
            if ($source_username) {
                # while the choco-server does not require creds on install.ps1,
                # Net.WebClient will only send the credentials if the initial
                # req fails so we will add the creds in case the source URL
                # is not choco-server and requires authentication
                $sec_source_password = ConvertTo-SecureString -String $source_password -AsPlainText -Force
                $client.Credentials = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $source_username, $sec_source_password
            }
        } else {
            $script_url = "https://chocolatey.org/install.ps1"
        }

        try {
            $install_script = $client.DownloadString($script_url)
        } catch {
            Fail-Json -obj $result -message "Failed to download Chocolatey script from '$script_url': $($_.Exception.Message)"
        }
        if (-not $check_mode) {
            $res = Run-Command -command "powershell.exe -" -stdin $install_script -environment $environment
            if ($res.rc -ne 0) {
                $result.rc = $res.rc
                $result.stdout = $res.stdout
                $result.stderr = $res.stderr
                Fail-Json -obj $result -message "Chocolatey bootstrap installation failed."
            }
            Add-Warning -obj $result -message "Chocolatey was missing from this system, so it was installed during this task run."
        }
        $result.changed = $true

        # locate the newly installed choco.exe
        $choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
        if ($null -eq $choco_app) {
            $choco_path = $env:ChocolateyInstall
            if ($null -ne $choco_path) {
                $choco_path = "$choco_path\bin\choco.exe"
            } else {
                $choco_path = "$env:SYSTEMDRIVE\ProgramData\Chocolatey\bin\choco.exe"
            }

            $choco_app = Get-Command -Name $choco_path -CommandType Application -ErrorAction SilentlyContinue
        }
    }
    if ($check_mode -and $null -eq $choco_app) {
        $result.skipped = $true
        $result.msg = "Skipped check mode run on win_chocolatey as choco.exe cannot be found on the system"
        Exit-Json -obj $result
    }

    if (-not (Test-Path -Path $choco_app.Path)) {
        Fail-Json -obj $result -message "Failed to find choco.exe, make sure it is added to the PATH or the env var 'ChocolateyInstall' is set"
    }

    $actual_version = Get-ChocolateyPackageVersion -choco_path $choco_app.Path -name chocolatey
    if ([Version]$actual_version -lt [Version]"0.10.5") {
        if ($check_mode) {
            $result.skipped = $true
            $result.msg = "Skipped check mode run on win_chocolatey as choco.exe is too old, a real run would have upgraded the executable. Actual: '$actual_version', Minimum Version: '0.10.5'"
            Exit-Json -obj $result
        }
        Add-Warning -obj $result -message "Chocolatey was older than v0.10.5 so it was upgraded during this task run."
        Update-ChocolateyPackage -choco_path $choco_app.Path -packages @("chocolatey") `
            -proxy_url $proxy_url -proxy_username $proxy_username `
            -proxy_password $proxy_password -source $source `
            -source_username $source_username -source_password $source_password
    }

    return $choco_app.Path
}

Function Get-ChocolateyPackageVersion {
    param(
        [Parameter(Mandatory=$true)][String]$choco_path,
        [Parameter(Mandatory=$true)][String]$name
    )
    # returns the package version or null if it isn't installed
    # all is a special case where we want to say it isn't installed, in choco
    # it means runs on all the packages installed
    if ($name -eq "all") {
        return $null
    }

    $command = Argv-ToString -arguments @($choco_path, "list", "--local-only", "--exact", "--limit-output", $name)
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        $result.command = $command
        $result.rc = $res.rc
        $result.stdout = $res.stdout
        $result.stderr = $res.stderr
        Fail-Json -obj $result -message "Error checking installation status for the package '$name'"
    }
    $stdout = $res.stdout.Trim()
    $version = $null
    if ($stdout) {
        # if a match occurs it is in the format of "package|version" we split
        # by the last | to get the version in case package contains a pipe char
        $pipe_index = $stdout.LastIndexOf("|")
        $version = $stdout.Substring($pipe_index + 1)
    }

    return $version
}

Function Update-ChocolateyPackage {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the cmdline, also using a SecureString here doesn't make sense considering the source is not secure")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    param(
        [Parameter(Mandatory=$true)][String]$choco_path,
        [Parameter(Mandatory=$true)][String[]]$packages,
        [bool]$allow_downgrade,
        [bool]$allow_empty_checksums,
        [bool]$allow_prerelease,
        [String]$architecture,
        [bool]$force,
        [bool]$ignore_checksums,
        [bool]$ignore_dependencies,
        [String]$install_args,
        [String]$package_params,
        [String]$proxy_url,
        [String]$proxy_username,
        [String]$proxy_password,
        [bool]$skip_scripts,
        [String]$source,
        [String]$source_username,
        [String]$source_password,
        [int]$timeout,
        [String]$version
    )

    $arguments = [System.Collections.ArrayList]@($choco_path, "upgrade")
    $arguments.AddRange($packages)
    $common_args = Get-InstallChocolateyArguments -allow_downgrade $allow_downgrade `
        -allow_empty_checksums $allow_empty_checksums -allow_prerelease $allow_prerelease `
        -architecture $architecture -force $force -ignore_checksums $ignore_checksums `
        -ignore_dependencies $ignore_dependencies -install_args $install_args `
        -package_params $package_params -proxy_url $proxy_url -proxy_username $proxy_username `
        -proxy_password $proxy_password -skip_scripts $skip_scripts -source $source `
        -source_username $source_username -source_password $source_password -timeout $timeout `
        -version $version
    $arguments.AddRange($common_args)

    $command = Argv-ToString -arguments $arguments
    $res = Run-Command -command $command
    $result.rc = $res.rc
    if ($res.rc -notin $successexitcodes) {
        $result.command = $command
        $result.stdout = $res.stdout
        $result.stderr = $res.stderr
        Fail-Json -obj $result -message "Error updating package(s) '$($packages -join ", ")'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $res.stdout
    }

    if ($res.stdout -match ' upgraded (\d+)/\d+ package') {
        if ($Matches[1] -gt 0) {
            $result.changed = $true
        }
    }
    # need to set to false in case the rc is not 0 and a failure didn't actually occur
    $result.failed = $false
}

Function Install-ChocolateyPackage {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the cmdline, also using a SecureString here doesn't make sense considering the source is not secure")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    param(
        [Parameter(Mandatory=$true)][String]$choco_path,
        [Parameter(Mandatory=$true)][String[]]$packages,
        [bool]$allow_downgrade,
        [bool]$allow_empty_checksums,
        [bool]$allow_prerelease,
        [String]$architecture,
        [bool]$force,
        [bool]$ignore_checksums,
        [bool]$ignore_dependencies,
        [String]$install_args,
        [String]$package_params,
        [String]$proxy_url,
        [String]$proxy_username,
        [String]$proxy_password,
        [bool]$skip_scripts,
        [String]$source,
        [String]$source_username,
        [String]$source_password,
        [int]$timeout,
        [String]$version
    )

    $arguments = [System.Collections.ArrayList]@($choco_path, "install")
    $arguments.AddRange($packages)
    $common_args = Get-InstallChocolateyArguments -allow_downgrade $allow_downgrade `
        -allow_empty_checksums $allow_empty_checksums -allow_prerelease $allow_prerelease `
        -architecture $architecture -force $force -ignore_checksums $ignore_checksums `
        -ignore_dependencies $ignore_dependencies -install_args $install_args `
        -package_params $package_params -proxy_url $proxy_url -proxy_username $proxy_username `
        -proxy_password $proxy_password -skip_scripts $skip_scripts -source $source `
        -source_username $source_username -source_password $source_password -timeout $timeout `
        -version $version
    $arguments.AddRange($common_args)

    $command = Argv-ToString -arguments $arguments
    $res = Run-Command -command $command
    $result.rc = $res.rc
    if ($res.rc -notin $successexitcodes) {
        $result.command = $command
        $result.stdout = $res.stdout
        $result.stderr = $res.stderr
        Fail-Json -obj $result -message "Error installing package(s) '$($packages -join ', ')'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $res.stdout
    }

    $result.changed = $true
    # need to set to false in case the rc is not 0 and a failure didn't actually occur
    $result.failed = $false
}

Function Uninstall-ChocolateyPackage {
    param(
        [Parameter(Mandatory=$true)][String]$choco_path,
        [Parameter(Mandatory=$true)][String[]]$packages,
        [bool]$force,
        [String]$package_params,
        [bool]$skip_scripts,
        [int]$timeout,
        [String]$version
    )

    $arguments = [System.Collections.ArrayList]@($choco_path, "uninstall")
    $arguments.AddRange($packages)
    $common_args = Get-CommonChocolateyArguments
    $arguments.AddRange($common_args)

    if ($force) {
        $arguments.Add("--force") > $null
    }
    if ($package_params) {
        $arguments.Add("--package-params") > $null
        $arguments.Add($package_params) > $null
    }
    if ($skip_scripts) {
        $arguments.Add("--skip-scripts") > $null
    }
    if ($null -ne $timeout) {
        $arguments.Add("--timeout") > $null
        $arguments.Add($timeout) > $null
    }
    if ($version) {
        $arguments.Add("--version") > $null
        $arguments.Add($version) > $null
    }

    $command = Argv-ToString -arguments $arguments
    $res = Run-Command -command $command
    $result.rc = $res.rc
    if ($res.rc -notin $successexitcodes) {
        $result.command = $command
        $result.stdout = $res.stdout
        $result.stderr = $res.stderr
        Fail-Json -obj $result -message "Error uninstalling package(s) '$($packages -join ", ")'"
    }

    if ($verbosity -gt 1) {
        $result.stdout = $res.stdout
    }
    $result.changed = $true
    # need to set to false in case the rc is not 0 and a failure didn't actually occur
    $result.failed = $false
}

# get the full path to choco.exe, otherwise install/upgrade to at least 0.10.5
$choco_path = Install-Chocolatey -proxy_url $proxy_url -proxy_username $proxy_username `
    -proxy_password $proxy_password -source $source -source_username $source_username `
    -source_password $source_password

# get the version of all specified packages
$package_info = @{}
foreach ($package in $name) {
    $package_version = Get-ChocolateyPackageVersion -choco_path $choco_path -name $package
    $package_info.$package = $package_version
}

if ($state -in "absent", "reinstalled") {
    $installed_packages = ($package_info.GetEnumerator() | Where-Object { $null -ne $_.Value }).Key
    if ($null -ne $installed_packages) {
        Uninstall-ChocolateyPackage -choco_path $choco_path -packages $installed_packages `
            -force $force -package_params $package_params -skip_scripts $skip_scripts `
            -timeout $timeout -version $version
    }

    # ensure the package info for the uninstalled versions has been removed
    # so state=reinstall will install them in the next step
    foreach ($package in $installed_packages) {
        $package_info.$package = $null
    }
}

if ($state -in @("downgrade", "latest", "present", "reinstalled")) {
    if ($state -eq "present" -and $force) {
        # when present and force, we just run the install step with the packages specified
        $missing_packages = $name
    } else {
        # otherwise only install the packages that are not installed
        $missing_packages = ($package_info.GetEnumerator() | Where-Object { $null -eq $_.Value }).Key
    }

    # if version is specified and installed version does not match, throw error
    # ignore this if force or is set
    if ($state -eq "present" -and $null -ne $version -and -not $force) {
        foreach ($package in $name) {
            $package_version = ($package_info.GetEnumerator() | Where-Object { $name -eq $_.Key -and $null -ne $_.Value }).Value
            if ($null -ne $package_version -and $package_version -ne $version) {
                Fail-Json -obj $result -message "Chocolatey package '$package' is already installed at version '$package_version' but was expecting '$version'. Either change the expected version, set state=latest, set allow_multiple_versions=yes, or set force=yes to continue"
            }
        }
    }
    $common_args = @{
        choco_path = $choco_path
        allow_downgrade = ($state -eq "downgrade")
        allow_empty_checksums = $allow_empty_checksums
        allow_prerelease = $allow_prerelease
        architecture = $architecture
        force = $force
        ignore_checksums = $ignore_checksums
        ignore_dependencies = $ignore_dependencies
        install_args = $install_args
        package_params = $package_params
        proxy_url = $proxy_url
        proxy_username = $proxy_username
        proxy_password = $proxy_password
        skip_scripts = $skip_scripts
        source = $source
        source_username = $source_username
        source_password = $source_password
        timeout = $timeout
        version = $version
    }

    if ($null -ne $missing_packages) {
        Install-ChocolateyPackage -packages $missing_packages @common_args
    }

    if ($state -eq "latest" -or ($state -eq "downgrade" -and $null -ne $version)) {
        # when in a downgrade/latest situation, we want to run choco upgrade on
        # the remaining packages that were already installed, don't run this if
        # state=downgrade and a version isn't specified (this will actually
        # upgrade a package)
        $installed_packages = ($package_info.GetEnumerator() | Where-Object { $null -ne $_.Value }).Key
        if ($null -ne $installed_packages) {
            Update-ChocolateyPackage -packages $installed_packages @common_args
        }
    }
}

Exit-Json -obj $result
