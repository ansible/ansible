#!powershell

# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psmodule (Windows PowerShell modules Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$required_version = Get-AnsibleParam -obj $params -name "required_version" -type "str"
$minimum_version = Get-AnsibleParam -obj $params -name "minimum_version" -type "str"
$maximum_version = Get-AnsibleParam -obj $params -name "maximum_version" -type "str"
$repo = Get-AnsibleParam -obj $params -name "repository" -type "str"
$url = Get-AnsibleParam -obj $params -name "url" -type str
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent", "latest"
$allow_clobber = Get-AnsibleParam -obj $params -name "allow_clobber" -type "bool" -default $false
$skip_publisher_check = Get-AnsibleParam -obj $params -name "skip_publisher_check" -type "bool" -default $false
$allow_prerelease = Get-AnsibleParam -obj $params -name "allow_prerelease" -type "bool" -default $false

$result = @{changed = $false
            output = ""
            nuget_changed = $false
            repository_changed = $false}


# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::SystemDefault
if ([System.Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls11
}
if ([System.Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls12
}
[System.Net.ServicePointManager]::SecurityProtocol = $security_protocols


Function Install-NugetProvider {
    Param(
        [Bool]$CheckMode
    )
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object { ($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201") }
    if (-not($PackageProvider)){
        try {
            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -WhatIf:$CheckMode | out-null
            $result.changed = $true
            $result.nuget_changed = $true
        }
        catch [ System.Exception ] {
            $ErrorMessage = "Problems adding package provider: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Install-PrereqModule {
    Param(
        [Switch]$TestInstallationOnly,
        [Bool]$CheckMode
    )

    # Those are minimum required versions of modules.
    $PrereqModules = @{
        PackageManagement = '1.1.7'
        PowerShellGet = '1.6.0'
    }

    [Bool]$PrereqModulesInstalled = $true

    ForEach ( $Name in $PrereqModules.Keys ) {

        $ExistingPrereqModule = Get-Module -ListAvailable | Where-Object { ($_.name -eq $Name) -and ($_.version -ge $PrereqModules[$Name]) }

        if ( -not $ExistingPrereqModule ) {
            if ( $TestInstallationOnly ) {
                $PrereqModulesInstalled = $false
            }
            else {
                try {
                    $install_params = @{
                        Name = $Name
                        MinimumVersion = $PrereqModules[$Name]
                        Force = $true
                        WhatIf = $CheckMode
                    }
                    if ((Get-Command -Name Install-Module).Parameters.ContainsKey('SkipPublisherCheck')) {
                        $install_params.SkipPublisherCheck = $true
                    }

                    Install-Module @install_params > $null

                    if ( $Name -eq 'PowerShellGet' ) {
                        # An order has to be reverted due to dependency
                        Remove-Module -Name PowerShellGet, PackageManagement -Force
                        Import-Module -Name PowerShellGet, PackageManagement -Force
                    }

                    $result.changed = $true
                }
                catch [ System.Exception ] {
                    $ErrorMessage = "Problems adding a prerequisite module $Name $($_.Exception.Message)"
                    Fail-Json $result $ErrorMessage
                }
            }
        }
    }

    if ( $TestInstallationOnly ) {
        $PrereqModulesInstalled
    }
}

Function Get-PsModule {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [String]$RequiredVersion,
        [String]$MinimumVersion,
        [String]$MaximumVersion
    )

    $ExistingModule = @{
        Exists = $false
        Version = ""
    }

    $ExistingModules = Get-Module -Listavailable | Where-Object {($_.name -eq $Name)}
    $ExistingModulesCount = $($ExistingModules | Measure-Object).Count

    if ( $ExistingModulesCount -gt 0 ) {

        $ExistingModules | Add-Member -MemberType ScriptProperty -Name FullVersion -Value { if ( $null -ne ( $this.PrivateData ) ) { [String]"$($this.Version)-$(($this | Select-Object -ExpandProperty PrivateData).PSData.Prerelease)".TrimEnd('-') } else { [String]"$($this.Version)" } }

        if ( -not ($RequiredVersion -or
                $MinimumVersion -or
                $MaximumVersion) )  {

            $ReturnedModule = $ExistingModules | Select-Object -First 1
        }
        elseif ( $RequiredVersion ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $_.FullVersion -eq $RequiredVersion }
        }
        elseif ( $MinimumVersion -and $MaximumVersion ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $MinimumVersion -le $_.Version -and $MaximumVersion -ge $_.Version } | Select-Object -First 1
        }
        elseif ( $MinimumVersion ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $MinimumVersion -le $_.Version } | Select-Object -First 1
        }
        elseif ( $MaximumVersion ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $MaximumVersion -ge $_.Version } | Select-Object -First 1
        }
    }

    $ReturnedModuleCount = ($ReturnedModule | Measure-Object).Count

    if ( $ReturnedModuleCount -eq 1 ) {
        $ExistingModule.Exists = $true
        $ExistingModule.Version = $ReturnedModule.FullVersion
    }

    $ExistingModule
}

Function Add-DefinedParameter {
    Param (
        [Parameter(Mandatory=$true)]
        [Hashtable]$Hashtable,
        [Parameter(Mandatory=$true)]
        [String[]]$ParametersNames
    )

    ForEach ($ParameterName in $ParametersNames) {
        $ParameterVariable = Get-Variable -Name $ParameterName -ErrorAction SilentlyContinue
        if ( $ParameterVariable.Value -and $Hashtable.Keys -notcontains $ParameterName ){
                $Hashtable.Add($ParameterName,$ParameterVariable.Value)
        }
    }

    $Hashtable
}

Function Install-PsModule {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [String]$RequiredVersion,
        [String]$MinimumVersion,
        [String]$MaximumVersion,
        [String]$Repository,
        [Bool]$AllowClobber,
        [Bool]$SkipPublisherCheck,
        [Bool]$AllowPrerelease,
        [Bool]$CheckMode
    )

    $ExistingModuleBefore = Get-PsModule -Name $Name -RequiredVersion $RequiredVersion -MinimumVersion $MinimumVersion -MaximumVersion $MaximumVersion

    if ( -not $ExistingModuleBefore.Exists ) {
        try {
            # Install NuGet provider if needed.
            Install-NugetProvider -CheckMode $CheckMode

            $ht = @{
                Name = $Name
                WhatIf = $CheckMode
                Force = $true
            }

            [String[]]$ParametersNames = @("RequiredVersion","MinimumVersion","MaximumVersion","AllowPrerelease","AllowClobber","SkipPublisherCheck","Repository")

            $ht = Add-DefinedParameter -Hashtable $ht -ParametersNames $ParametersNames

            Install-Module @ht -ErrorVariable ErrorDetails | out-null

            $result.changed = $true
            $result.output = "Module $($Name) installed"
        }
        catch [ System.Exception ] {
            $ErrorMessage = "Problems installing $($Name) module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
    else {
        $result.output = "Module $($Name) already present"
    }
}

Function Remove-PsModule {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [String]$RequiredVersion,
        [String]$MinimumVersion,
        [String]$MaximumVersion,
        [Bool]$CheckMode
    )
    # If module is present, uninstalls it.
    if (Get-Module -Listavailable | Where-Object {$_.name -eq $Name}) {
        try {
            $ht = @{
                Name = $Name
                Confirm = $false
                Force = $true
            }

            $ExistingModuleBefore = Get-PsModule -Name $Name -RequiredVersion $RequiredVersion -MinimumVersion $MinimumVersion -MaximumVersion $MaximumVersion

            [String[]]$ParametersNames = @("RequiredVersion","MinimumVersion","MaximumVersion")

            $ht = Add-DefinedParameter -Hashtable $ht -ParametersNames $ParametersNames

            if ( -not ( $RequiredVersion -or $MinimumVersion -or $MaximumVersion ) ) {
                $ht.Add("AllVersions", $true)
            }

            if ( $ExistingModuleBefore.Exists) {
                # The Force parameter overwrite the WhatIf parameter
                if ( -not $CheckMode ) {
                    Uninstall-Module @ht -ErrorVariable ErrorDetails | out-null
                }
                $result.changed = $true
                $result.output = "Module $($Name) removed"
            }
        }
        catch [ System.Exception ] {
            $ErrorMessage = "Problems uninstalling $($Name) module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
    else {
        $result.output = "Module $($Name) removed"
    }
}

Function Find-LatestPsModule {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [String]$Repository,
        [Bool]$AllowPrerelease,
        [Bool]$CheckMode
    )

    try {
        $ht = @{
            Name = $Name
        }

        [String[]]$ParametersNames = @("AllowPrerelease","Repository")

        $ht = Add-DefinedParameter -Hashtable $ht -ParametersNames $ParametersNames

        $LatestModule = Find-Module @ht
        $LatestModuleVersion = $LatestModule.Version
    }
    catch [ System.Exception ] {
        $ErrorMessage = "Cant find the module $($Name): $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
    }

    $LatestModuleVersion
}

Function Install-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [Parameter(Mandatory=$true)]
        [string]$Url,
        [bool]$CheckMode
    )
    Add-DeprecationWarning -obj $result -message "Adding a repo with this module is deprecated, the repository parameter should only be used to select a repo. Use win_psrepository to manage repos" -version 2.12
    # Install NuGet provider if needed.
    Install-NugetProvider -CheckMode $CheckMode

    $Repos = (Get-PSRepository).SourceLocation

    # If repository isn't already present, try to register it as trusted.
    if ($Repos -notcontains $Url){
      try {
           if ( -not ($CheckMode) ) {
               Register-PSRepository -Name $Name -SourceLocation $Url -InstallationPolicy Trusted -ErrorAction Stop
           }
          $result.changed = $true
          $result.repository_changed = $true
      }
      catch {
        $ErrorMessage = "Problems registering $($Name) repository: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
      }
    }
}

Function Remove-Repository{
    Param(
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [bool]$CheckMode
    )
    Add-DeprecationWarning -obj $result -message "Removing a repo with this module is deprecated, use win_psrepository to manage repos" -version 2.12

    $Repo = (Get-PSRepository).Name

    # Try to remove the repository
    if ($Repo -contains $Name){
        try {
            if ( -not ($CheckMode) ) {
                Unregister-PSRepository -Name $Name -ErrorAction Stop
            }
            $result.changed = $true
            $result.repository_changed = $true
        }
        catch [ System.Exception ] {
            $ErrorMessage = "Problems unregistering $($Name)repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

# Check PowerShell version, fail if < 5.0 and required modules are not installed
$PsVersion = $PSVersionTable.PSVersion
if ($PsVersion.Major -lt 5 ) {
    $PrereqModulesInstalled = Install-PrereqModule -TestInstallationOnly
    if ( -not $PrereqModulesInstalled ) {
        $ErrorMessage = "Modules PowerShellGet and PackageManagement in versions 1.6.0 and 1.1.7 respectively have to be installed before using the win_psmodule."
        Fail-Json $result $ErrorMessage
    }
}

if ( $required_version -and ( $minimum_version -or $maximum_version ) ) {
       $ErrorMessage = "Parameters required_version and minimum/maximum_version are mutually exclusive."
       Fail-Json $result $ErrorMessage
}

if ( $allow_prerelease -and ( $minimum_version -or $maximum_version ) ) {
    $ErrorMessage = "Parameters minimum_version, maximum_version can't be used with the parameter allow_prerelease."
    Fail-Json $result $ErrorMessage
}

if ( $allow_prerelease -and $state -eq "absent" ) {
    $ErrorMessage = "The parameter allow_prerelease can't be used with state set to 'absent'."
    Fail-Json $result $ErrorMessage
}

if ( ($state -eq "latest") -and
    ( $required_version -or $minimum_version -or $maximum_version ) ) {
        $ErrorMessage = "When the parameter state is equal 'latest' you can use any of required_version, minimum_version, maximum_version."
        Fail-Json $result $ErrorMessage
}

if ( $repo -and (-not $url) ) {
    $RepositoryExists = Get-PSRepository -Name $repo -ErrorAction SilentlyContinue
    if ( $null -eq $RepositoryExists) {
        $ErrorMessage = "The repository $repo doesn't exist."
        Fail-Json $result $ErrorMessage
    }

}

if ( ($allow_clobber -or $allow_prerelease -or $skip_publisher_check -or
    $required_version -or $minimum_version -or $maximum_version) ) {
    # Update the PowerShellGet and PackageManagement modules.
    # It's required to support AllowClobber, AllowPrerelease parameters.
    Install-PrereqModule -CheckMode $check_mode
}

Import-Module -Name PackageManagement, PowerShellGet

if ($state -eq "present") {
    if (($repo) -and ($url)) {
        Install-Repository -Name $repo -Url $url -CheckMode $check_mode
    }
    else {
        $ErrorMessage = "Repository Name and Url are mandatory if you want to add a new repository"
    }

    if ($name) {
        $ht = @{
            Name = $name
            RequiredVersion = $required_version
            MinimumVersion = $minimum_version
            MaximumVersion = $maximum_version
            Repository = $repo
            AllowClobber = $allow_clobber
            SkipPublisherCheck = $skip_publisher_check
            AllowPrerelease = $allow_prerelease
            CheckMode = $check_mode
        }
        Install-PsModule @ht
    }
}
elseif ($state -eq "absent") {
    if ($repo) {
        Remove-Repository -Name $repo -CheckMode $check_mode
    }

    if ($name) {
        $ht = @{
            Name = $Name
            CheckMode = $check_mode
            RequiredVersion = $required_version
            MinimumVersion = $minimum_version
            MaximumVersion = $maximum_version
        }
        Remove-PsModule @ht
    }
}
elseif ( $state -eq "latest") {

    $ht = @{
        Name = $Name
        AllowPrerelease = $allow_prerelease
        Repository = $repo
        CheckMode = $check_mode
    }

    $LatestVersion = Find-LatestPsModule @ht

    $ExistingModule = Get-PsModule $Name

    if ( $LatestVersion.Version -ne $ExistingModule.Version ) {

        $ht = @{
            Name = $Name
            RequiredVersion = $LatestVersion
            Repository = $repo
            AllowClobber = $allow_clobber
            SkipPublisherCheck = $skip_publisher_check
            AllowPrerelease = $allow_prerelease
            CheckMode = $check_mode
        }
        Install-PsModule @ht
    }
}

Exit-Json $result
