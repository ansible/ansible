#!powershell

# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psmodule (Powershell modules Additions/Removal)

$params = Parse-Args $args -supports_check_mode $true

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$repo = Get-AnsibleParam -obj $params -name "repository" -type "str"
$url = Get-AnsibleParam -obj $params -name "url" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$allow_clobber = Get-AnsibleParam -obj $params -name "allow_clobber" -type "bool" -default $false
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$result = @{"changed" = $false
            "output" = ""
            "nuget_changed" = $false
            "repository_changed" = $false}

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
      [bool]$CheckMode
    )
    if (Get-Module -Listavailable|?{$_.name -eq $Name}){
        $result.output = "Module $($Name) already present"
    }
    else {      
      try{
        # Install NuGet Provider if needed
        Install-NugetProvider -CheckMode $CheckMode;

        $ht = @{
            Name      = $Name;
            WhatIf    = $CheckMode;
            ErrorAction = "Stop";
            Force     = $true;
        };

        # If specified, use repository name to select module source
        if ($Repository) {
            $ht["Repository"] = "$Repository";
        }

        # Check Powershell Version (-AllowClobber was introduced in PowerShellGet 1.6.0)
        if ("AllowClobber" -in ((Get-Command PowerShellGet\Install-Module | Select -ExpandProperty Parameters).Keys)) {
          $ht['AllowClobber'] = $AllowClobber;
        }
        
        Install-Module @ht | out-null;
        
        $result.output = "Module $($Name) installed"
        $result.changed = $true
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
        Uninstall-Module -Name $Name -Confirm:$false -Force -ErrorAction Stop -WhatIf:$CheckMode | out-null
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

    Install-PsModule -Name $Name -Repository $repo -CheckMode $check_mode -AllowClobber $allow_clobber;
}
else {  
    if ($repo) {   
        Remove-Repository -Name $repo -CheckMode $check_mode
    }
    Remove-PsModule -Name $Name -CheckMode $check_mode
}

Exit-Json $result
