#!powershell

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#win_psmodule (Powershell modules Additions/Removal)

$params = Parse-Args $args -supports_check_mode $true

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true 
$repo = Get-AnsibleParam -obj $params -name "repository" -type "str"
$url = Get-AnsibleParam -obj $params -name "url" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$allow_clobber = Get-AnsibleParam -obj $params -name "allow_clobber" -type "bool" -default $false
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false
$latest = Get-AnsibleParam -obj $params -name "latest" -type "bool" -default $false
$required_version = Get-AnsibleParam -obj $params -name "required_version" -type "str"
$force_required_version = Get-AnsibleParam -obj $params -name "force_required_version" -type "bool" -default $false

$result = @{"changed" = $false
            "output" = ""
            "nuget_changed" = $false
            "repository_changed" = $false}

If (($latest -eq $true) -and ($required_version -ne $null)) {
    Fail-Json $result "latest and required_version are mutually exclusive but have both been set"
}

If (($force_required_version -eq $true) -and ($required_version -eq $null)) {
    Fail-Json $result "force_required_version can be used only when required_version is set"
}

Function Install-NugetProvider {
  param(
    [bool]$CheckMode
    )
  $PackageProvider = Get-PackageProvider -ListAvailable|?{($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201")}
  if (!($PackageProvider)){
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

Function Install-Repository {
    Param(
    [Parameter(Mandatory=$true)]
    [string]$Name,
    [Parameter(Mandatory=$true)]
    [string]$Url,
    [bool]$CheckMode
    )
    $Repo = (Get-PSRepository).SourceLocation

    # If repository isn't already present, try to register it as trusted.
    if ($Repo -notcontains $Url){ 
      try {
           if (!($CheckMode)) {
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
    [string]$Name,
    [bool]$CheckMode
    )

    $Repo = (Get-PSRepository).SourceLocation

    # Try to remove the repository
    if ($Repo -contains $Name){
        try {         
            if (!($CheckMode)) {
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

Function Install-PsModule {
    param(
      [Parameter(Mandatory=$true)]
      [string]$Name,
      [string]$Repository,
      [bool]$AllowClobber,
      [bool]$CheckMode,
      [bool]$Latest,
      [string]$RequiredVersion,
      [bool]$ForceRequiredVersion
    )
    $need_update = $false
    $module_version_current = $null
    $ht = @{
        Name      = $Name;
        WhatIf    = $CheckMode;
        ErrorAction = "Stop";
        Force     = $true;
    };

    $ht_find_module = @{
        Name      = $Name;
        ErrorAction = "Stop";
    }

    # If specified, use repository name to select module source
    if ($Repository) {
        $ht["Repository"] = "$Repository";
        $ht_find_module["Repository"] = "$Repository";
    }
    # If specified set required version
    if ($RequiredVersion) {
        $ht_find_module["RequiredVersion"] = "$RequiredVersion";
        $ht["RequiredVersion"] = "$RequiredVersion"
    }

    # Check Powershell Version (-AllowClobber was introduced in PowerShellGet 1.6.0)
    if ("AllowClobber" -in ((Get-Command PowerShellGet\Install-Module | Select -ExpandProperty Parameters).Keys)) {
        $ht['AllowClobber'] = $AllowClobber;
    }

    #Check if module present and save to variable
    $module = Get-Module -Listavailable|?{$_.name -eq $Name}
    #If module present, save info about latest version
    if ($module){
        $module_version_current = $module.version | select -First 1
    }

    #search for latest or required version
    try {
        $search_result = Find-Module @ht_find_module
    }
    catch {
        $ErrorMessage = "Problems searching $($Name) module in repository: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
    }
    #Saving old logic: if module present, and no new parameters - do nothing, no matter which version
    if ($module -and ($Latest -eq $false) -and !($RequiredVersion)){
        $result.output = "Module $($Name) already present"
    }
    #If module present and latest version needed
    elseif ($module -and $Latest -eq $true) {
        if ($module_version_current -lt $search_result.version) {
            $need_update = $true
        }
        elseif ($module_version_current -eq $search_result.version) {
            $result.output = "Module $($Name):$($module_version_current) already present"
        }
        #when repository has lower version than target computer. Just to be safe
        else {
            $ErrorMessage = "Installed version of module $($Name):$($module_version_current) higher than in repository:$($search_result.version)"
            Fail-Json $result $ErrorMessage
        }    
    }
    #If module present and version is required
    elseif ($module -and $RequiredVersion) {    
        if ($module_version_current -ne $search_result.version) {
            #if current version higher than required
            if ($module_version_current -gt $search_result.version) {
                # remove all versions and install required when forced
                if ($force_required_version -eq $true){
                    $need_remove = $true
                    $need_update = $true
                }      
                else {
                    Add-Warning -obj $result -message "Current version $($module_version_current) higher than required $($RequiredVersion). No changes have been made. Use force_required_version parameter to downgrade"
                }
            }
            #if current version lower than required - install required
            if ($module_version_current -lt $search_result.version){
                $need_update = $true
            }
        }
        #Required version already in use
        else {
            $result.output = "Module $($Name):$($RequiredVersion) already present"
        }
    }
    
    #if no module installed or update needed
    if (!($module) -or $need_update -eq $true){
        try{
            # Install NuGet Provider if needed
            Install-NugetProvider -CheckMode $CheckMode;
            #remove module if needed 
            if ($need_remove -eq $true){
                try {
                    Uninstall-Module -Name $Name -Confirm:$false -ErrorAction Stop -AllVersions -WhatIf:$CheckMode | out-null
                }
                catch {
                    $ErrorMessage = "Problems uninstalling $($Name) module: $($_.Exception.Message)"
                    Fail-Json $result $ErrorMessage
                }
            }
            Install-Module @ht | out-null;

            $result.output = "Module $($Name) installed"
            $result.changed = $true
            if ($module_version_current -eq $null){
                $module_version_current = 'none'
            }
            $result.version = "$module_version_current => $($search_result.version)"
        }
        catch{
            $ErrorMessage = "Problems installing $($Name) module: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }   
    }           
}

Function Remove-PsModule {
    param(
      [Parameter(Mandatory=$true)]
      [string]$Name,
      [bool]$CheckMode
    )
    # If module is present, unistalls it.
    if (Get-Module -Listavailable|?{$_.name -eq $Name}){
      try{
        #remove all versions, because now we can have multiple versions installed
        Uninstall-Module -Name $Name -Confirm:$false -Force -ErrorAction Stop -AllVersions -WhatIf:$CheckMode | out-null
        $result.output = "Module $($Name) removed"
        $result.changed = $true
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

# Check powershell version, fail if < 5.0
$PsVersion = $PSVersionTable.PSVersion
if ($PsVersion.Major -lt 5){
  $ErrorMessage = "Powershell 5.0 or higher is needed"
  Fail-Json $result $ErrorMessage
}

if ($state -eq "present") {
    if (($repo) -and ($url)) {
        Install-Repository -Name $repo -Url $url -CheckMode $check_mode 
    }
    else {
        $ErrorMessage = "Repository Name and Url are mandatory if you want to add a new repository"
    }

    Install-PsModule -Name $Name -Repository $repo -CheckMode $check_mode -Latest $latest -RequiredVersion $required_version -AllowClobber $allow_clobber -ForceRequiredVersion $force_required_version;
}
else {  
    if ($repo) {   
        Remove-Repository -Name $repo -CheckMode $check_mode
    }
    Remove-PsModule -Name $Name -CheckMode $check_mode
}

Exit-Json $result

