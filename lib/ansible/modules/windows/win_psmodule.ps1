#!powershell
# This file is part of Ansible
#
# Copyright 2016, Daniele Lazzari <lazzari@mailup.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

# win_psmodule (Powershell modules Additions/Removal)

$params = Parse-Args $args -supports_check_mode $false

$name = Get-AnsibleParam -obj $params "name" -type "str" -failifempty $true
$repo = Get-AnsibleParam -obj $params "repository" -type "str" 
$url = Get-AnsibleParam -obj $params "url" -type "str"
$state = Get-AnsibleParam -obj $params "state" -type "str" -default "present" -validateset "present", "absent"
$result = @{"changed" = $false
            "output" = ""}


Function Install-NugetProvider {
  $PackageProvider = Get-PackageProvider -ListAvailable|?{($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201")}
  if (!($PackageProvider)){
      try{
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -ErrorAction Stop|out-null
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
    [string]$Url
    )
    $Repo = (Get-PSRepository).SourceLocation

    if ($Repo -notcontains $Url){ 
      try {
        Register-PSRepository -Name $Name -SourceLocation $Url -InstallationPolicy Trusted -ErrorAction Stop
      }
      catch {
        $ErrorMessage = "Problems adding $($name) repository: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
      }
    }
}

Function Remove-Repository{
    Param(
    [Parameter(Mandatory=$true)]
    [string]$Name
    )

    $Repo = (Get-PSRepository).SourceLocation

    if ($Repo -contains $name){
        try{
            Unregister-PSRepository -Name $name -ErrorAction Stop
        }
        catch{
            $ErrorMessage = "Problems removing $($name)repository: $($_.Exception.Message)"
            Fail-Json $result $ErrorMessage
        }
    }
}

Function Install-PsModule {
    param(
      [Parameter(Mandatory=$true)]
      [string]$Name
    )
    if (Get-Module -Listavailable|?{$_.name -eq $Name}){
        $result.output = "Module $($name) already present"
    }
    else {      
      try{
        Install-NugetProvider
        Install-Module -Name $Name -Force -ErrorAction Stop
        $result.output = "Module $($name) Installed"
        $result.changed = $true
      }
      catch{
        $ErrorMessage = "Problems installing $($name) module: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
      }
    }
}

Function Remove-PsModule {
    param(
      [Parameter(Mandatory=$true)]
      [string]$Name
    )
    if (Get-Module -Listavailable|?{$_.name -eq $Name}){
      try{
        Uninstall-Module -Name $Name -Confirm:$false -Force -ErrorAction Stop
        $result.changed = $true
        $result.output = "Module $($name) removed"

      }
      catch{
        $ErrorMessage = "Problems removing $($name) module: $($_.Exception.Message)"
        Fail-Json $result $ErrorMessage
      }

    }
    else{
      $result.output = "Module $($name) not present"
    }
}


if ($PSVersionTable.PSVersion.Major -lt 5){
  $ErrorMessage = "Powershell 5.0 or higher is needed"
  Fail-Json $result $ErrorMessage
}

if ($state -eq "present"){
    if (($repo) -and ($url)){
          Install-Repository -Name $repo -Url $url
        }
    else {
      $ErrorMessage = "Repository Name and Url are mandatory if you want to add a new repository"
    }
  Install-PsModule -Name $name
}
else{
  if (($repo) -and ($url)){
          Remove-Repository -Name $repo
        }
  Remove-PsModule -Name $name
}


Exit-Json $result
