#!powershell

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psmodule (Powershell modules Additions/Removal)

$params = Parse-Args -arguments $args -supports_check_mode $true

$name = Get-AnsibleParam -obj $params -name "name" -type "str"
$required_version = Get-AnsibleParam -obj $params -name "required_version" -type "str"
$minimum_version = Get-AnsibleParam -obj $params -name "minimum_version" -type "str"
$maximum_version = Get-AnsibleParam -obj $params -name "maximum_version" -type "str"
$repo = Get-AnsibleParam -obj $params -name "repository" -type "str"
$url = Get-AnsibleParam -obj $params -name "url" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent", "latest"
$allow_clobber = Get-AnsibleParam -obj $params -name "allow_clobber" -type "bool" -default $false
$skip_publisher_check = Get-AnsibleParam -obj $params -nam "skip_publisher_check" -type "bool" -default $false
$allow_prerelease = Get-AnsibleParam -obj $params -name "allow_prerelease" -type "bool" -default $false
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$result = @{"changed" = $false
            "output" = ""
            "module_version" = ""
            "nuget_changed" = $false
            "repository_changed" = $false
            "powershellget_changed" = $false
            "packagemanagement_changed" = $false}

Function Install-NugetProvider {
    Param(
        [Bool]$CheckMode
    )
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object {($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201")}
    if (-not($PackageProvider)){
        try{
            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -ErrorAction Stop -WhatIf:$CheckMode | out-null
            $result.changed = $true
            $result.nuget_changed = $true
        }
        catch{
            $ErrorMessage = "Problems adding package provider: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Install-PackageManagement {
    Param(
        [Bool]$CheckMode
    )
    $PackageManagement = Get-Module -ListAvailable | Where-Object {($_.name -eq 'PackageManagement') -and ($_.version -ge "1.1.7.0")}

    if ( -not ($PackageManagement)) {
        try {
            Install-Module -Name PackageManagement -MinimumVersion 1.1.7.0 -Force -ErrorAction Stop -WhatIf:$CheckMode | out-null
            $result.changed = $true
            $result.packagemanagement_changed = $true
        }
        catch{
            $ErrorMessage = "Problems adding module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Install-PowerShellGet {
    Param(
        [Bool]$CheckMode
    )
    $PowerShellGet = Get-Module -ListAvailable | Where-Object {($_.name -eq 'PowerShellGet') -and ($_.version -ge "1.6.0")}

    if ( -not ($PowerShellGet) ) {
        try {
            Install-Module -Name PowerShellGet -MinimumVersion 1.6.0 -Force -ErrorAction Stop -WhatIf:$CheckMode | out-null
            $result.changed = $true
            $result.powershellget_changed = $true

            Remove-Module -Name PowerShellGet, PackageManagement -Force -ErrorAction Stop
            Import-Module -Name PowerShellGet, PackageManagement -Force -ErrorAction Stop
        }
        catch{
            $ErrorMessage = "Problems adding module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Install-Repository {
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [Parameter(Mandatory=$true)]
        [String]$Url,
        [Bool]$CheckMode
    )
    $Repo = (Get-PSRepository).SourceLocation

    # If repository isn't already present, try to register it as trusted.
    if ($Repo -notcontains $Url){
        try {
            if (-not($CheckMode)) {
               Register-PSRepository -Name $Name -SourceLocation $Url -InstallationPolicy Trusted -ErrorAction Stop
            }
            $result.changed = $true
            $result.repository_changed = $true
        }
        catch {
            $ErrorMessage = "Problems adding $($Name) repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Remove-Repository{
    Param(
        [Parameter(Mandatory=$true)]
        [String]$Name,
        [Bool]$CheckMode
    )
    $Repo = (Get-PSRepository).SourceLocation

    # Try to remove the repository
    if ($Repo -contains $Name){
        try {
            if (-not ($CheckMode)) {
                Unregister-PSRepository -Name $Name -ErrorAction Stop
            }
            $result.changed = $true
            $result.repository_changed = $true
        }
        catch {
            $ErrorMessage = "Problems removing $($Name)repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
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

    $props = @{
        'Exists' = $false
        'Version' = ""
        'Versions' = @("")
    }
    $ExistingModule = New-Object -TypeName psobject -Property $props

    $ExistingModules = Get-Module -Listavailable | Where-Object {($_.name -eq $Name)}
    $ExistingModulesCount = $($ExistingModules | Measure-Object).Count

    if ( $ExistingModulesCount -gt 0 ) {

        $ExistingModules | Add-Member -MemberType ScriptProperty -Name FullVersion -Value { "$($this.Version)-$(($this | Select-Object -ExpandProperty PrivateData).PSData.Prerelease)".TrimEnd('-') }

        $ExistingModule.Versions = $ExistingModules.FullVersion

        if ( [String]::IsNullOrEmpty($RequiredVersion) -and
                [String]::IsNullOrEmpty($MinimumVersion) -and
                [String]::IsNullOrEmpty($MaximumVersion))  {

            $ReturnedModule = $ExistingModules | Select-Object -First 1
        }
        elseif ( -not ([String]::IsNullOrEmpty($RequiredVersion)) ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $_.FullVersion -eq $RequiredVersion }
        }
        elseif ( (-not ([String]::IsNullOrEmpty($MinimumVersion))) -and
                (-not ([String]::IsNullOrEmpty($MaximumVersion))) ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $_.Version -ge $MinimumVersion -and $_.Version -le $MaximumVersion } | Select-Object -First 1
        }
        elseif ( -not ([String]::IsNullOrEmpty($MinimumVersion)) ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $_.Version -ge $MinimumVersion } | Select-Object -First 1
        }
        elseif ( -not ([String]::IsNullOrEmpty($MaximumVersion)) ) {
            $ReturnedModule = $ExistingModules | Where-Object -FilterScript { $_.Version -le $MaximumVersion } | Select-Object -First 1
        }
    }

    $ReturnedModuleCount = ($ReturnedModule | Measure-Object).Count

    if ( $ReturnedModuleCount -eq 1 ) {
        $ExistingModule.Exists = $true
        $ExistingModule.Version = $ReturnedModule.FullVersion
    }

    $ExistingModule
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

    if ( $ExistingModuleBefore.Exists ) {
        $result.output = "Module $($Name) already present."
        $result.module_version = $($ExistingModuleBefore.Version).ToString()
    }
    else {
        try{
            # Install NuGet provider if needed
            Install-NugetProvider -CheckMode $CheckMode

            if ( $AllowClobber -or $AllowPrerelease ) {
                # Update the PowerShellGet and PackageManagement modules
                # it's required to support AllowClobber, AllowPrerelease parameters
                Install-PackageManagement -CheckMode $CheckMode
                Install-PowerShellGet -CheckMode $CheckMode
            }

            $ht = @{
                "Name" = $Name
                "AllowClobber" = $AllowClobber
                "SkipPublisherCheck" = $SkipPublisherCheck
                "WhatIf" = $CheckMode
                "ErrorAction" = "Stop"
                "Force" = $true
            }

            [String[]]$VersionParameters = @("RequiredVersion","MinimumVersion","MaximumVersion")

            ForEach ($VersionParameterString in $VersionParameters) {
                $VersionParameterVariable = Get-Variable -Name $VersionParameterString
                if ( -not([String]::IsNullOrEmpty($VersionParameterVariable.Value)) ){
                        $ht.Add($VersionParameterString,$VersionParameterVariable.Value)
                }
            }

            if ( $AllowPrerelease ) {
                $ht.Add("AllowPrerelease",$AllowPrerelease)
            }

            # If specified, use repository name to select module source
            if ( -not([String]::IsNullOrEmpty($Repository)) ) {
                $ht.Add("Repository", "$Repository")
            }

            Install-Module @ht | out-null

            $ExistingModuleAfter = Get-PsModule -Name $Name

            $VersionInstalled = Compare-Object -ReferenceObject $ExistingModuleBefore.Versions -DifferenceObject $ExistingModuleAfter.Versions -PassThru

            $result.output = "Module $($Name) installed."

            Get-Member -InputObject $VersionInstalled

            $result.module_version = $($VersionInstalled.GetEnumerator() -Join ',').Trim().Replace(' ','')
            $result.changed = $true
        }
        catch{
            $ErrorMessage = "Problems installing $($Name) module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
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
    if (Get-Module -Listavailable | Where-Object {$_.name -eq $Name}){
        try{
            $ht = @{
                "Name" = $Name
                "Confirm" = $false
                "WhatIf" = $CheckMode
                "ErrorAction" = "Stop"
                "Force" = $true
            }

            $ExistingModuleBefore = Get-PsModule -Name $Name -RequiredVersion $RequiredVersion -MinimumVersion $MinimumVersion -MaximumVersion $MaximumVersion

            [String[]]$VersionParameters = @("RequiredVersion","MinimumVersion","MaximumVersion")

            ForEach ($VersionParameterString in $VersionParameters) {
                $VersionParameterVariable = Get-Variable -Name $VersionParameterString
                if ( -not([String]::IsNullOrEmpty($VersionParameterVariable.Value)) ){
                        $ht.Add($VersionParameterString,$VersionParameterVariable.Value)
                }
            }

            if ( $ExistingModuleBefore.Exists) {

                Uninstall-Module @ht | out-null

                $ExistingModuleAfter = Get-PsModule -Name $Name

                $VersionUninstalled = Compare-Object -ReferenceObject $ExistingModuleAfter.Versions -DifferenceObject $ExistingModuleBefore.Versions -PassThru

                $result.output = "Module $($Name) removed."
                $result.module_version = $($VersionUninstalled.GetEnumerator() -Join ',').Trim().Replace(' ','')
                $result.changed = $true
            }
            else {
                $result.output = "Module $($Name) already absent."
            }
        }
        catch{
            $ErrorMessage = "Problems removing $($Name) module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
    else{
        $result.output = "Module $($Name) not present"
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
            "Name" = $Name
            "ErrorAction" = "Stop"
        }

        if ( $AllowPrerelease ) {
            # Update the PowerShellGet and PackageManagement modules
            # it's required to support AllowPrerelease parameters
            Install-PackageManagement -CheckMode $CheckMode
            Install-PowerShellGet -CheckMode $CheckMode

            $ht.Add("AllowPrerelease",$AllowPrerelease)
        }

        # If specified, use repository name to select module source
        if ( -not([String]::IsNullOrEmpty($Repository)) ) {
            $ht.Add("Repository", "$Repository")
        }

        $LatestModule = Find-Module @ht
        $LatestModuleVersion = $LatestModule.Version
    }
    catch {
        $ErrorMessage = "Cant find the module $($Name): $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
    }

    $LatestModuleVersion
}

# Check powershell version, fail if < 5.0
$PsVersion = $PSVersionTable.PSVersion
if ($PsVersion.Major -lt 5){
    $ErrorMessage = "Powershell 5.0 or higher is needed"
    Fail-Json $result $ErrorMessage
}

# You can separately make operations on modules or repositories
# but one of them is required, fails if not
if ( [String]::IsNullOrEmpty($name) -and [String]::IsNullOrEmpty($repo) ) {
    $ErrorMessage = "The value of name and repo can't be both empty."
    Fail-Json $result $ErrorMessage
}

if ( -not ( [String]::IsNullOrEmpty($required_version) ) -and
   ( -not ([String]::IsNullOrEmpty($minimum_version)) -or -not ([String]::IsNullOrEmpty($maximum_version))  ) ) {
       $ErrorMessage = "Parameters required_version and minimum/maximum_version are mutually exclusive."
       Fail-Json $result $ErrorMessage
}

if ( $allow_prerelease -and ( (-not ([String]::IsNullOrEmpty($minimum_version))) -or (-not ([String]::IsNullOrEmpty($maximum_version))) ) ) {
    $ErrorMessage = "Parameters minimum_version, maximum_version can't be used with the parameter allow_prerelease."
    Fail-Json $result $ErrorMessage
}

if ( $allow_prerelease -and $state -eq "absent" ) {
    $ErrorMessage = "The parameter allow_prerelease can't be used with state set to 'absent'."
    Fail-Json $result $ErrorMessage
}

if ( ($state -eq "latest") -and
    ( -not ( [String]::IsNullOrEmpty($required_version) ) -or
      -not ([String]::IsNullOrEmpty($minimum_version)) -or
     -not ([String]::IsNullOrEmpty($maximum_version) ) ) ) {
        $ErrorMessage = "When the parameter state is equal 'latest' you can use any of required_version, minimum_version, maximum_version."
        Fail-Json $result $ErrorMessage
}

if ($state -eq "present") {
    if ( -not $([String]::IsNullOrEmpty($repo)) -and -not $([String]::IsNullOrEmpty($url)) ) {
        Install-Repository -Name $repo -Url $url -CheckMode $check_mode
    }
    else {
        $ErrorMessage = "Repository Name and Url are mandatory if you want to add a new repository"
    }

    if ( -not $([String]::IsNullOrEmpty($name)) ) {
        $ht = @{
            "Name" = $name
            "RequiredVersion" = $required_version
            "MinimumVersion" = $minimum_version
            "MaximumVersion" = $maximum_version
            "Repository" = $repo
            "AllowClobber" = $allow_clobber
            "SkipPublisherCheck" = $skip_publisher_check
            "AllowPrerelease" = $allow_prerelease
            "CheckMode" = $check_mode
        }
        Install-PsModule @ht
    }
    else {
        $ErrorMessage = "Module Name is mandatory."
        Fail-Json $result $ErrorMessage
    }
}
elseif ($state -eq "absent") {
    if ( -not([String]::IsNullOrEmpty($Repository)) ) {
        Remove-Repository -Name $repo -CheckMode $check_mode
    }

    if ( -not([String]::IsNullOrEmpty($name)) ) {
        $ht = @{
            "Name" = $Name
            "CheckMode" = $check_mode
            "RequiredVersion" = $required_version
            "MinimumVersion" = $minimum_version
            "MaximumVersion" = $maximum_version
        }
        Remove-PsModule @ht
    }

}
elseif ( $state -eq "latest") {

    $ht = @{
        "Name" = $Name
        "AllowPrerelease" = $allow_prerelease
        "Repository" = $repo
        "CheckMode" = $check_mode
    }

    $LatestVersion = Find-LatestPsModule @ht

    $ExistingModule = Get-PsModule $Name

    if ( $LatestVersion.Version -ne $ExistingModule.Version ) {

        $ht = @{
            "Name" = $Name
            "RequiredVersion" = $LatestVersion
            "Repository" = $repo
            "AllowClobber" = $allow_clobber
            "SkipPublisherCheck" = $skip_publisher_check
            "AllowPrerelease" = $allow_prerelease
            "CheckMode" = $check_mode
        }
        Install-PsModule @ht
    }
}

Exit-Json $result
