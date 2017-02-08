#!powershell
# This file is part of Ansible
#
# Copyright 2014, Chris Hoffman <choffman@chathamfinancial.com>
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

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params "_ansible_check_mode" -type "bool" -default $false

$dependencies = Get-AnsibleParam -obj $params -name 'dependencies' -failifempty $false -default $null
$dependency_action = Get-AnsibleParam -obj $params -name 'dependency_action' -failifempty $false -ValidateSet 'add', 'remove', 'set' -default 'set'
$description = Get-AnsibleParam -obj $params -name 'description' -failifempty $false -default $null
$desktop_interact = Get-AnsibleParam -obj $params -name 'desktop_interact' -type "bool" -failifempty $false -default $false
$display_name = Get-AnsibleParam -obj $params -name 'display_name' -failifempty $false -default $null
$name = Get-AnsibleParam -obj $params -name 'name' -failifempty $true
$password = Get-AnsibleParam -obj $params -name 'password' -failifempty $false -default $null
$path = Get-AnsibleParam -obj $params -name 'path' -failifempty $false -default $null
$start_mode = Get-AnsibleParam -obj $params -name 'start_mode' -failifempty $false -ValidateSet 'auto', 'manual', 'disabled', 'delayed'
$state = Get-AnsibleParam -obj $params -name 'state' -failifempty $false -ValidateSet 'started', 'stopped', 'restarted', 'absent'
$username = Get-AnsibleParam -obj $params -name 'username' -failifempty $false -default $null

$result = @{
    changed = $false
    warnings = @()
}

# Check if dependencies is a string and convert to a list
if ($dependencies -is [System.String]) {
    $dependencies = @($dependencies)
}

if ($username -ne $null -and $password -eq $null) {
    Fail-Json $result "The argument 'password' must be supplied with 'username'"
}
if ($password -ne $null -and $username -eq $null) {
    Fail-Json $result "The argument 'username' must be supplied with 'password'"
}
if ($desktop_interact -eq $true -and (-not ($username -eq "LocalSystem" -or $username -eq $null))) {
    Fail-Json $result "Can only set 'desktop_interact' to true when 'username' equals 'LocalSystem'"
}

Function Get-ServiceInfo($name) {
    # Need to get new objects so we have the latest info
    $svc = Get-Service -Name $name
    $wmi_svc = Get-WmiObject Win32_Service | Where-Object { $_.Name -eq $svc.Name }

    # Delayed start_mode is in reality Automatic (Delayed), need to check reg key for type
    $delayed = Get-DelayedStatus -name $svc.Name
    $actual_start_mode = $wmi_svc.StartMode.ToString().ToLower() 
    if ($delayed -and $actual_start_mode -eq 'auto') {
        $actual_start_mode = 'delayed'
    }

    $existing_depenencies = @()
    $existing_depended_by = @()
    if ($svc.ServicesDependedOn.Count -gt 0) {
        foreach ($dependency in $svc.ServicesDependedOn.Name) {
            $existing_depenencies += $dependency
        }
    }
    if ($svc.DependentServices.Count -gt 0) {
        foreach ($dependency in $svc.DependentServices.Name) {
            $existing_depended_by += $dependency
        }
    }

    $result.exists = $true
    $result.name = $svc.Name
    $result.display_name = $svc.DisplayName
    $result.state = $svc.Status.ToString().ToLower()
    $result.start_mode = $actual_start_mode
    $result.path = $wmi_svc.PathName
    $result.description = $wmi_svc.Description
    $result.username = $wmi_svc.startname
    $result.desktop_interact = (ConvertTo-Bool $wmi_svc.DesktopInteract)
    $result.dependencies = $existing_depenencies
    $result.depended_by = $existing_depended_by
}

Function Get-WmiErrorMessage($return_value) {
    # These values are derived from https://msdn.microsoft.com/en-us/library/aa384901(v=vs.85).aspx
    switch ($return_value) {
        1 { "Not Supported: The request is not supported" }
        2 { "Access Denied: The user did not have the necessary access" }
        3 { "Dependent Servies Running: The service cannot be stopped because other services that are running are dependent on it" }
        4 { "Invalid Service Control: Thre requested control code is not valid, or it is unacceptable to the service" }
        5 { "The requested control code cannot be sent to the service because the state of the service is equal to 0, 1, or 2" }
        6 { "Service Not Ative: The service has not been started" }
        7 { "Service Request Timeout: The service did not response to the start request in a timely fashion" }
        8 { "Unknown Failure: Unknown failure when starting the service" }
        9 { "Path Not Found: THe directory path to the service executable file was not found" }
        10 { "Service Already Running: The service is already running" }
        11 { "Service Database Locked: The database to add a new service is locked" }
        12 { "Service Dependency Deleted: A dependency this service relies on has been removed from the system" }
        13 { "Service Dependency Failure: The service failed to find the service needed from a dependent service" }
        14 { "Servoce Disabled: The service has been disbaled from the system" }
        15 { "Service Logon Failed: The service does not have the correct authentication to run on this system" }
        16 { "Service Marked For Deletion: This service is being removed from the system" }
        17 { "Service No Thread: The service has no execution thread" }
        18 { "Status Circular Dependecy: The service has circular dependencies when it starts" }
        19 { "Status Duplicate Name: A service is running under the same name" }
        20 { "Status Invalid Name: The service name has invalide characters" }
        21 { "Status Invalid Paramter: Invalid paramters have been passed to the service" }
        22 { "Status Invalid Service Account: The account under which this service runs is either invalid or lacks the permissions to run the service" }
        23 { "Status Service Exists: The service exists in the database of services available from the system" }
        24 { "Service Already Paused: The service is currently paused in the system" }
        default { "Other Error" }
    }
}

Function Get-DelayedStatus($name) {
    $delayed_key = "HKLM:\System\CurrentControlSet\Services\$name"
    try {
        $delayed = ConvertTo-Bool ((Get-ItemProperty -Path $delayed_key).DelayedAutostart)
    } catch {
        $delayed = $false
    }

    $delayed
}

Function Set-ServiceStartMode($svc, $start_mode) {
    if ($result.start_mode -ne $start_mode) {
        try {
            $delayed_key = "HKLM:\System\CurrentControlSet\Services\$($svc.Name)"

            if ($check_mode) {
                # Original start up type was auto (delayed) and we want auto, need to removed delayed key
                if ($start_mode -eq 'auto' -and $result.start_mode -eq 'delayed') {
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 0 -Type DWORD -WhatIf
                # Original start up type was auto and we want auto (delayed), need to add delayed key
                } elseif ($start_mode -eq 'delayed' -and $result.start_mode -eq 'auto') {
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 1 -Type DWORD -WhatIf
                # Original start up type was not auto or auto (delayed), need to change to auto and add delayed key
                } elseif ($start_mode -eq 'delayed') {
                    $svc | Set-Service -StartupType "auto" -WhatIf
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 1 -Type DWORD -WhatIf
                # Original start up type was not what we were looking for, just change to that type
                } else {
                    $svc | Set-Service -StartupType $start_mode -WhatIf
                }
            } else {
                if ($start_mode -eq 'auto' -and $result.start_mode -eq 'delayed') {
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 0 -Type DWORD
                } elseif ($start_mode -eq 'delayed' -and $result.start_mode -eq 'auto') {
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 1 -Type DWORD
                } elseif ($start_mode -eq 'delayed') {
                    $svc | Set-Service -StartupType "auto"
                    Set-ItemProperty -Path $delayed_key -Name "DelayedAutostart" -Value 1 -Type DWORD
                } else {
                    $svc | Set-Service -StartupType $start_mode
                }
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }
}

Function Set-ServiceAccount($wmi_svc, $username, $password) {
    if ($result.username -ne $username) {
        #WMI.Change doesn't support -WhatIf, cannot fully test with check_mode
        if (-not $check_mode) {
            $return = $wmi_svc.Change($null,$null,$null,$null,$null,$false,$username,$password,$null,$null,$null)
            if ($return.ReturnValue -ne 0) {
                Fail-Json $result "$($return.ReturnValue): $(Get-WmiErrorMessage -return_value $return.ReturnValue)"
            }
        }        

        $result.changed = $true
    }
}

Function Set-ServiceDesktopInteract($wmi_svc, $desktop_interact) {
    if ($result.desktop_interact -ne $desktop_interact) {
        if (-not $check_mode) {
            $return = $wmi_svc.Change($null,$null,$null,$null,$null,$desktop_interact,$null,$null,$null,$null,$null) 
            if ($return.ReturnValue -ne 0) {
                Fail-Json $result "$($return.ReturnValue): $(Get-WmiErrorMessage -return_value $return.ReturnValue)"
            }
        }

        $result.changed = $true
    }
}

Function Set-ServiceDisplayName($svc, $display_name) {
    if ($result.display_name -ne $display_name) {
        try {
            if ($check_mode) {
                $svc | Set-Service -DisplayName $display_name -WhatIf
            } else {
                $svc | Set-Service -DisplayName $display_name
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }
}

Function Set-ServiceDescription($svc, $description) {
    if ($result.description -ne $description) {
        try {
            if ($check_mode) {
                $svc | Set-Service -Description $description -WhatIf
            } else {
                $svc | Set-Service -Description $description
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }
}

Function Set-ServicePath($name, $path) {
    if ($result.path -ne $path) {
        try {
            if ($check_mode) {
                Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Services\$name" -Name ImagePath -Value $path -WhatIf
            } else {
                Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Services\$name" -Name ImagePath -Value $path
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }
}

Function Set-ServiceDependencies($wmi_svc, $dependency_action, $dependencies) {
    $existing_dependencies = $result.dependencies
    [System.Collections.ArrayList]$new_dependencies = @()

    if ($dependency_action -eq 'set') {
        $new_dependencies = $dependencies
    } else {
        $new_dependencies = $existing_dependencies
        foreach ($dependency in $dependencies) {
            if ($dependency_action -eq 'remove') {
                if ($new_dependencies -contains $dependency) {
                    $new_dependencies.Remove($dependency)
                }
            } elseif ($dependency_action -eq 'add') {
                if ($new_dependencies -notcontains $dependency) {
                    $new_dependencies.Add($dependency)
                }
            }
        }
    }

    $will_change = $false
    foreach ($dependency in $new_dependencies) {
        if ($existing_dependencies -notcontains $dependency) {
            $will_change = $true
        }
    }
    foreach ($dependency in $existing_dependencies) {
        if ($new_dependencies -notcontains $dependency) {
            $will_change = $true
        }
    }

    if ($will_change -eq $true) {
        if (-not $check_mode) {
            $return = $wmi_svc.Change($null,$null,$null,$null,$null,$null,$null,$null,$null,$null,$new_dependencies)
            if ($return.ReturnValue -ne 0) {
                Fail-Json $result "$($return.ReturnValue): $(Get-WmiErrorMessage -return_value $return.ReturnValue)"
            }
        }
        
        $result.changed = $true
    }
}

Function Set-ServiceState($svc, $wmi_svc, $state) {
    if ($state -eq "started" -and $result.state -ne "running") {
        try {
            if ($check_mode) {
                Start-Service -Name $svc.Name -WhatIf
            } else {
                Start-Service -Name $svc.Name
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }

    if ($state -eq "stopped" -and $result.state -ne "stopped") {
        try {
            if ($check_mode) {
                Stop-Service -Name $svc.Name -Force -WhatIf
            } else {
                Stop-Service -Name $svc.Name -Force
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }

    if ($state -eq "restarted") {
        try {
            if ($check_mode) {
                Restart-Service -Name $svc.Name -Force -WhatIf
            } else {
                Restart-Service -Name $svc.Name -Force
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        
        $result.changed = $true
    }

    if ($state -eq "absent") {
        try {
            if ($check_mode) {
                Stop-Service -Name $svc.Name -Force -WhatIf
            } else {
                Stop-Service -Name $svc.Name -Force
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        if (-not $check_mode) {
            $return = $wmi_svc.Delete()
            if ($return.ReturnValue -ne 0) {
                Fail-Json $result "$($return.ReturnValue): $(Get-WmiErrorMessage -return_value $return.ReturnValue)"
            }
        }
        
        $result.changed = $true
    }
}

Function Set-ServiceConfiguration($svc) {
    $wmi_svc = Get-WmiObject Win32_Service | Where-Object { $_.Name -eq $svc.Name }
    Get-ServiceInfo -name $svc.Name
    if ($desktop_interact -eq $true -and (-not ($result.username -eq 'LocalSystem' -or $username -eq 'LocalSystem'))) {
        Fail-Json $result "Can only set desktop_interact to true when service is run with or 'username' equals 'LocalSystem'"
    }

    if ($start_mode -ne $null) {
        Set-ServiceStartMode -svc $svc -start_mode $start_mode
    }

    if ($username -ne $null) {
        Set-ServiceAccount -wmi_svc $wmi_svc -username $username -password $password
    }

    if ($display_name -ne $null) {
        Set-ServiceDisplayName -svc $svc -display_name $display_name
    }

    if ($desktop_interact -ne $null) {
        Set-ServiceDesktopInteract -wmi_svc $wmi_svc -desktop_interact $desktop_interact
    }

    if ($description -ne $null) {
        Set-ServiceDescription -svc $svc -description $description
    }

    if ($path -ne $null) {
        Set-ServicePath -name $svc.Name -path $path
    }

    if ($dependencies -ne $null) {
        Set-ServiceDependencies -wmi_svc $wmi_svc -dependency_action $dependency_action -dependencies $dependencies
    }

    if ($state -ne $null) {
        Set-ServiceState -svc $svc -wmi_svc $wmi_svc -state $state
    }
}

$svc = Get-Service -Name $name -ErrorAction SilentlyContinue
if ($svc) {
    Set-ServiceConfiguration -svc $svc
} else {
    $result.exists = $false
    if ($state -ne 'absent') {
        # Check if path is defined, if so create the service
        if ($path -ne $null) {
            try {
                if ($check_mode) {
                    New-Service -Name $name -BinaryPathname $path -WhatIf
                } else {
                    New-Service -Name $name -BinaryPathname $path
                }
            } catch {
                Fail-Json $result $_.Exception.Message
            }
            $result.changed = $true

            $svc = Get-Service -Name $name
            Set-ServiceConfiguration -svc $svc
        } else {
            # We will only reach here if the service is installed and the state is not absent
            # Will check if any of the default actions are set and fail as we cannot action it
            if ($start_mode -ne $null -or
                $state -ne $null -or
                $username -ne $null -or
                $password -ne $null -or
                $display_name -ne $null -or
                $description -ne $null -or
                $desktop_interact -ne $false -or
                $dependencies -ne $null -or
                $dependency_action -ne 'set') {
                    Fail-Json $result "Service '$name' is not installed, need to set 'path' to create a new service"
            }
        }
    }
}

# After making a change, let's get the service info again unless we deleted it
if ($state -eq 'absent') {
    # Recreate result so it doesn't have the extra meta data now that is has been deleted
    $changed = $result.changed
    $warnings = $result.warnings
    $result = @{
        changed = $changed
        warnings = $warnings
        exists = $false
    }
} elseif ($svc -ne $null) {
    Get-ServiceInfo -name $name
}

Exit-Json $result
