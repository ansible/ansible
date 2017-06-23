#!powershell
# This file is part of Ansible
#
# Copyright 2017, Liran Nisanov <lirannis@gmail.com>
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

########

Function Remove-Pagefile($path) 
{
    Get-WmiObject Win32_PageFileSetting | WHERE { $_.Name -eq $path } | Remove-WmiObject
}

Function Get-Pagefile($path)
{
    Get-WmiObject Win32_PageFileSetting | WHERE { $_.Name -eq $path }
}

########

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name '_ansible_check_mode' -type 'bool' -default $false

$automatic = Get-AnsibleParam -obj $params -name "automatic" -type "bool"
$drive = Get-AnsibleParam -obj $params -name "drive" -type "str"
$fullPath = $drive + ":\pagefile.sys"
$initialSize = Get-AnsibleParam -obj $params -name "initial_size" -type "int"
$maximumSize = Get-AnsibleParam -obj $params -name "maximum_size" -type "int"
$override =  Get-AnsibleParam -obj $params -name "override" -type "bool" -default $true
$removeAll = Get-AnsibleParam -obj $params -name "remove_all" -type "bool" -default $false
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "query" -validateset "present","absent","query"
$systemManaged = Get-AnsibleParam -obj $params -name "system_managed" -type "bool" -default $false

$result = @{
    changed = $false
}

if ($removeAll) {
    $currentPageFiles = Get-WmiObject Win32_PageFileSetting
    if ($currentPageFiles -ne $null) {
        if (-not $check_mode) {
            $currentPageFiles | Remove-WmiObject | Out-Null
        }
        $result.changed = $true
    }
}

if ($automatic -ne $null) {
    # change autmoatic managed pagefile 
    try {
        $computerSystem = Get-WmiObject -Class win32_computersystem -EnableAllPrivileges
    
        if ($computerSystem.AutomaticManagedPagefile -ne $automatic) {
            $computerSystem.AutomaticManagedPagefile = $automatic
            if (-not $check_mode) {
            	$computerSystem.Put() | Out-Null
            }
            $result.changed = $true
        }
    } catch {
        Fail-Json $result "Failed to set AutomaticManagedPagefile $_.Exception.Message"
    }
}

if ($state -eq "absent") {
    # Remove pagefile
    if ((Get-Pagefile $fullPath) -ne $null)
    {
        try {
            if (-not $check_mode) {
                Remove-Pagefile $fullPath
            }
            $result.changed = $true
        } catch {
            Fail-Json $result "Failed to remove pagefile $_.Exception.Message"
        }
    }
} elseif ($state -eq "present") {   
    # Remove current pagefile
    if ($override) {
        if ((Get-Pagefile $fullPath) -ne $null)
        {
            try {
                if (-not $check_mode) {
                    Remove-Pagefile $fullPath
                }
                $result.changed = $true
            } catch {
                Fail-Json $result "Failed to remove current pagefile $_.Exception.Message"
            }
        }
    }

    # Make sure drive is accessible
    if (!(Test-Path "${drive}:")) {
        Fail-Json $result "Unable to access '${drive}:' drive"
    }

    # Set pagefile
    try {
        if ((Get-Pagefile $fullPath) -eq $null) {
            $pagefile = Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{name = $fullPath; InitialSize = 0; MaximumSize = 0}
            if (!$systemManaged) {
                $pagefile.InitialSize = $initialSize
                $pagefile.MaximumSize = $maximumSize
                if (-not $check_mode) {
                    $pagefile.Put() | out-null
                }
            }
            $result.changed = $true
        }
    } catch {
        Fail-Json $result "Failed to set pagefile $_.Exception.Message"
    }
} elseif ($state -eq "query") {
    try {

        $result.pagefiles = @()

        if ($drive -eq $null) {
            $pagefiles = Get-WmiObject Win32_PageFileSetting
        } else {
            $pagefiles = Get-Pagefile $fullPath
        }

        # Get all pagefiles
        foreach ($currentPagefile in $pagefiles) {
            $currentPagefileObject = @{
                name = $currentPagefile.Name
                initial_size = $currentPagefile.InitialSize
                maximum_size = $currentPagefile.MaximumSize
                caption = $currentPagefile.Caption
                description = $currentPagefile.Description
            }

            $result.pagefiles += $currentPagefileObject
        }

        # Get automatic managed pagefile state
        $result.automatic_managed_pagefiles = (Get-WmiObject -Class win32_computersystem).AutomaticManagedPagefile
    } catch {
        Fail-Json $result "Failed to query current pagefiles $_.Exception.Message"
    }
}
Exit-Json $result
