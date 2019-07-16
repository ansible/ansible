#!powershell

# Copyright: (c) 2014, Chris Hoffman <choffman@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name '_ansible_check_mode' -type 'bool' -default $false

$dependencies = Get-AnsibleParam -obj $params -name 'dependencies' -type 'list' -default $null
$dependency_action = Get-AnsibleParam -obj $params -name 'dependency_action' -type 'str' -default 'set' -validateset 'add','remove','set'
$description = Get-AnsibleParam -obj $params -name 'description' -type 'str'
$desktop_interact = Get-AnsibleParam -obj $params -name 'desktop_interact' -type 'bool' -default $false
$display_name = Get-AnsibleParam -obj $params -name 'display_name' -type 'str'
$force_dependent_services = Get-AnsibleParam -obj $params -name 'force_dependent_services' -type 'bool' -default $false
$name = Get-AnsibleParam -obj $params -name 'name' -type 'str' -failifempty $true
$password = Get-AnsibleParam -obj $params -name 'password' -type 'str'
$path = Get-AnsibleParam -obj $params -name 'path'
$start_mode = Get-AnsibleParam -obj $params -name 'start_mode' -type 'str' -validateset 'auto','manual','disabled','delayed'
$state = Get-AnsibleParam -obj $params -name 'state' -type 'str' -validateset 'started','stopped','restarted','absent','paused'
$username = Get-AnsibleParam -obj $params -name 'username' -type 'str'

$result = @{
    changed = $false
}

# parse the username to SID and back so we get the full username with domain in a way WMI understands
if ($null -ne $username) {
    if ($username -eq "LocalSystem") {
        $username_sid = "S-1-5-18"
    } else {
        $username_sid = Convert-ToSID -account_name $username
    }

    # the SYSTEM account is a special beast, Win32_Service Change requires StartName to be LocalSystem
    # to specify LocalSystem/NT AUTHORITY\SYSTEM
    if ($username_sid -eq "S-1-5-18") {
        $username = "LocalSystem"
        $password = $null
    } else {
        # Win32_Service, password must be "" and not $null when setting to LocalService or NetworkService
        if ($username_sid -in @("S-1-5-19", "S-1-5-20")) {
            $password = ""
        }
        $username = Convert-FromSID -sid $username_sid
    }
}
if ($null -ne $password -and $null -eq $username) {
    Fail-Json $result "The argument 'username' must be supplied with 'password'"
}
if ($desktop_interact -eq $true -and (-not ($username -eq "LocalSystem" -or $null -eq $username))) {
    Fail-Json $result "Can only set 'desktop_interact' to true when 'username' equals 'LocalSystem'"
}
if ($null -ne $path) {
    $path = [System.Environment]::ExpandEnvironmentVariables($path)
}

Function Get-ServiceInfo($name) {
    # Need to get new objects so we have the latest info
    $svc = Get-Service | Where-Object { $_.Name -eq $name -or $_.DisplayName -eq $name }
    $wmi_svc = Get-CimInstance -ClassName Win32_Service -Filter "name='$($svc.Name)'"

    # Delayed start_mode is in reality Automatic (Delayed), need to check reg key for type
    $delayed = Get-DelayedStatus -name $svc.Name
    $actual_start_mode = $wmi_svc.StartMode.ToString().ToLower()
    if ($delayed -and $actual_start_mode -eq 'auto') {
        $actual_start_mode = 'delayed'
    }

    $existing_dependencies = @()
    $existing_depended_by = @()
    if ($svc.ServicesDependedOn.Count -gt 0) {
        foreach ($dependency in $svc.ServicesDependedOn.Name) {
            $existing_dependencies += $dependency
        }
    }
    if ($svc.DependentServices.Count -gt 0) {
        foreach ($dependency in $svc.DependentServices.Name) {
            $existing_depended_by += $dependency
        }
    }
    $description = $wmi_svc.Description
    if ($null -eq $description) {
        $description = ""
    }

    $result.exists = $true
    $result.name = $svc.Name
    $result.display_name = $svc.DisplayName
    $result.state = $svc.Status.ToString().ToLower()
    $result.start_mode = $actual_start_mode
    $result.path = $wmi_svc.PathName
    $result.description = $description
    $result.username = $wmi_svc.StartName
    $result.desktop_interact = $wmi_svc.DesktopInteract
    $result.dependencies = $existing_dependencies
    $result.depended_by = $existing_depended_by
    $result.can_pause_and_continue = $svc.CanPauseAndContinue
}

Function Get-WmiErrorMessage($return_value) {
    # These values are derived from https://msdn.microsoft.com/en-us/library/aa384901(v=vs.85).aspx
    switch ($return_value) {
        1 { "Not Supported: The request is not supported" }
        2 { "Access Denied: The user did not have the necessary access" }
        3 { "Dependent Services Running: The service cannot be stopped because other services that are running are dependent on it" }
        4 { "Invalid Service Control: The requested control code is not valid, or it is unacceptable to the service" }
        5 { "Service Cannot Accept Control: The requested control code cannot be sent to the service because the state of the service (Win32_BaseService.State property) is equal to 0, 1, or 2" }
        6 { "Service Not Active: The service has not been started" }
        7 { "Service Request Timeout: The service did not respond to the start request in a timely fashion" }
        8 { "Unknown Failure: Unknown failure when starting the service" }
        9 { "Path Not Found: The directory path to the service executable file was not found" }
        10 { "Service Already Running: The service is already running" }
        11 { "Service Database Locked: The database to add a new service is locked" }
        12 { "Service Dependency Deleted: A dependency this service relies on has been removed from the system" }
        13 { "Service Dependency Failure: The service failed to find the service needed from a dependent service" }
        14 { "Service Disabled: The service has been disabled from the system" }
        15 { "Service Logon Failed: The service does not have the correct authentication to run on the system" }
        16 { "Service Marked For Deletion: This service is being removed from the system" }
        17 { "Service No Thread: The service has no execution thread" }
        18 { "Status Circular Dependency: The service has circular dependencies when it starts" }
        19 { "Status Duplicate Name: A service is running under the same name" }
        20 { "Status Invalid Name: The service name has invalid characters" }
        21 { "Status Invalid Parameter: Invalid parameters have been passed to the service" }
        22 { "Status Invalid Service Account: The account under which this service runs is either invalid or lacks the permissions to run the service" }
        23 { "Status Service Exists: The service exists in the database of services available from the system" }
        24 { "Service Already Paused: The service is currently paused in the system" }
        default { "Other Error" }
    }
}

Function Get-DelayedStatus($name) {
    $delayed_key = "HKLM:\System\CurrentControlSet\Services\$name"
    try {
        $delayed = ConvertTo-Bool ((Get-ItemProperty -LiteralPath $delayed_key).DelayedAutostart)
    } catch {
        $delayed = $false
    }

    $delayed
}

Function Set-ServiceStartMode($svc, $start_mode) {
    if ($result.start_mode -ne $start_mode) {
        try {
            $delayed_key = "HKLM:\System\CurrentControlSet\Services\$($svc.Name)"
            # Original start up type was auto (delayed) and we want auto, need to removed delayed key
            if ($start_mode -eq 'auto' -and $result.start_mode -eq 'delayed') {
                Set-ItemProperty -LiteralPath $delayed_key -Name "DelayedAutostart" -Value 0 -WhatIf:$check_mode
            # Original start up type was auto and we want auto (delayed), need to add delayed key
            } elseif ($start_mode -eq 'delayed' -and $result.start_mode -eq 'auto') {
                Set-ItemProperty -LiteralPath $delayed_key -Name "DelayedAutostart" -Value 1 -WhatIf:$check_mode
            # Original start up type was not auto or auto (delayed), need to change to auto and add delayed key
            } elseif ($start_mode -eq 'delayed') {
                $svc | Set-Service -StartupType "auto" -WhatIf:$check_mode
                Set-ItemProperty -LiteralPath $delayed_key -Name "DelayedAutostart" -Value 1 -WhatIf:$check_mode
            # Original start up type was not what we were looking for, just change to that type
            } else {
                $svc | Set-Service -StartupType $start_mode -WhatIf:$check_mode
            }
        } catch {
            Fail-Json $result $_.Exception.Message
        }

        $result.changed = $true
    }
}

Function Set-ServiceAccount($wmi_svc, $username_sid, $username, $password) {
    if ($result.username -eq "LocalSystem") {
        $actual_sid = "S-1-5-18"
    } else {
        $actual_sid = Convert-ToSID -account_name $result.username
    }

    if ($actual_sid -ne $username_sid) {
        $change_arguments = @{
            StartName = $username
            StartPassword = $password
            DesktopInteract = $result.desktop_interact
        }
        # need to disable desktop interact when not using the SYSTEM account
        if ($username_sid -ne "S-1-5-18") {
            $change_arguments.DesktopInteract = $false
        }

        #WMI.Change doesn't support -WhatIf, cannot fully test with check_mode
        if (-not $check_mode) {
            $return = $wmi_svc | Invoke-CimMethod -MethodName Change -Arguments $change_arguments
            if ($return.ReturnValue -ne 0) {
                $error_msg = Get-WmiErrorMessage -return_value $result.ReturnValue
                Fail-Json -obj $result -message "Failed to set service account to $($username): $($return.ReturnValue) - $error_msg"
            }
        }

        $result.changed = $true
    }
}

Function Set-ServiceDesktopInteract($wmi_svc, $desktop_interact) {
    if ($result.desktop_interact -ne $desktop_interact) {
        if (-not $check_mode) {
            $return = $wmi_svc | Invoke-CimMethod -MethodName Change -Arguments @{DesktopInteract = $desktop_interact}
            if ($return.ReturnValue -ne 0) {
                $error_msg = Get-WmiErrorMessage -return_value $return.ReturnValue
                Fail-Json -obj $result -message "Failed to set desktop interact $($desktop_interact): $($return.ReturnValue) - $error_msg"
            }
        }

        $result.changed = $true
    }
}

Function Set-ServiceDisplayName($svc, $display_name) {
    if ($result.display_name -ne $display_name) {
        try {
            $svc | Set-Service -DisplayName $display_name -WhatIf:$check_mode
        } catch {
            Fail-Json $result $_.Exception.Message
        }

        $result.changed = $true
    }
}

Function Set-ServiceDescription($svc, $description) {
    if ($result.description -ne $description) {
        try {
            $svc | Set-Service -Description $description -WhatIf:$check_mode
        } catch {
            Fail-Json $result $_.Exception.Message
        }

        $result.changed = $true
    }
}

Function Set-ServicePath($name, $path) {
    if ($result.path -ne $path) {
        try {
            Set-ItemProperty -LiteralPath "HKLM:\System\CurrentControlSet\Services\$name" -Name ImagePath -Value $path -WhatIf:$check_mode
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
        foreach ($dependency in $dependencies) {
            $new_dependencies.Add($dependency)
        }
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
            $return = $wmi_svc | Invoke-CimMethod -MethodName Change -Arguments @{ServiceDependencies = $new_dependencies}
            if ($return.ReturnValue -ne 0) {
                $error_msg = Get-WmiErrorMessage -return_value $return.ReturnValue
                $dep_string = $new_dependencies -join ", "
                Fail-Json -obj $result -message "Failed to set service dependencies $($dep_string): $($return.ReturnValue) - $error_msg"
            }
        }

        $result.changed = $true
    }
}

Function Set-ServiceState($svc, $wmi_svc, $state) {
    if ($state -eq "started" -and $result.state -ne "running") {
        if ($result.state -eq "paused") {
            try {
                $svc | Resume-Service -WhatIf:$check_mode
            } catch {
                Fail-Json $result "failed to start service from paused state $($svc.Name): $($_.Exception.Message)"
            }
        } else {
            try {
                $svc | Start-Service -WhatIf:$check_mode
            } catch {
                Fail-Json $result $_.Exception.Message
            }
        }

        $result.changed = $true
    }

    if ($state -eq "stopped" -and $result.state -ne "stopped") {
        try {
            $svc | Stop-Service -Force:$force_dependent_services -WhatIf:$check_mode
        } catch {
            Fail-Json $result $_.Exception.Message
        }

        $result.changed = $true
    }

    if ($state -eq "restarted") {
        try {
            $svc | Restart-Service -Force:$force_dependent_services -WhatIf:$check_mode
        } catch {
            Fail-Json $result $_.Exception.Message
        }

        $result.changed = $true
    }

    if ($state -eq "paused" -and $result.state -ne "paused") {
        # check that we can actually pause the service
        if ($result.can_pause_and_continue -eq $false) {
            Fail-Json $result "failed to pause service $($svc.Name): The service does not support pausing"
        }

        try {
            $svc | Suspend-Service -WhatIf:$check_mode
        } catch {
            Fail-Json $result "failed to pause service $($svc.Name): $($_.Exception.Message)"
        }
        $result.changed = $true
    }

    if ($state -eq "absent") {
        try {
            $svc | Stop-Service -Force:$force_dependent_services -WhatIf:$check_mode
        } catch {
            Fail-Json $result $_.Exception.Message
        }
        if (-not $check_mode) {
            $return = $wmi_svc | Invoke-CimMethod -MethodName Delete
            if ($return.ReturnValue -ne 0) {
                $error_msg = Get-WmiErrorMessage -return_value $return.ReturnValue
                Fail-Json -obj $result -message "Failed to delete service $($svc.Name): $($return.ReturnValue) - $error_msg"
            }
        }

        $result.changed = $true
    }
}

Function Set-ServiceConfiguration($svc) {
    $wmi_svc = Get-CimInstance -ClassName Win32_Service -Filter "name='$($svc.Name)'"
    Get-ServiceInfo -name $svc.Name
    if ($desktop_interact -eq $true -and (-not ($result.username -eq 'LocalSystem' -or $username -eq 'LocalSystem'))) {
        Fail-Json $result "Can only set desktop_interact to true when service is run with/or 'username' equals 'LocalSystem'"
    }

    if ($null -ne $start_mode) {
        Set-ServiceStartMode -svc $svc -start_mode $start_mode
    }

    if ($null -ne $username) {
        Set-ServiceAccount -wmi_svc $wmi_svc -username_sid $username_sid -username $username -password $password
    }

    if ($null -ne $display_name) {
        Set-ServiceDisplayName -svc $svc -display_name $display_name
    }

    if ($null -ne $desktop_interact) {
        Set-ServiceDesktopInteract -wmi_svc $wmi_svc -desktop_interact $desktop_interact
    }

    if ($null -ne $description) {
        Set-ServiceDescription -svc $svc -description $description
    }

    if ($null -ne $path) {
        Set-ServicePath -name $svc.Name -path $path
    }

    if ($null -ne $dependencies) {
        Set-ServiceDependencies -wmi_svc $wmi_svc -dependency_action $dependency_action -dependencies $dependencies
    }

    if ($null -ne $state) {
        Set-ServiceState -svc $svc -wmi_svc $wmi_svc -state $state
    }
}

# need to use Where-Object as -Name doesn't work with [] in the service name
# https://github.com/ansible/ansible/issues/37621
$svc = Get-Service | Where-Object { $_.Name -eq $name -or $_.DisplayName -eq $name }
if ($svc) {
    Set-ServiceConfiguration -svc $svc
} else {
    $result.exists = $false
    if ($state -ne 'absent') {
        # Check if path is defined, if so create the service
        if ($null -ne $path) {
            try {
                New-Service -Name $name -BinaryPathname $path -WhatIf:$check_mode
            } catch {
                Fail-Json $result $_.Exception.Message
            }
            $result.changed = $true

            $svc = Get-Service | Where-Object { $_.Name -eq $name }
            Set-ServiceConfiguration -svc $svc
        } else {
            # We will only reach here if the service is installed and the state is not absent
            # Will check if any of the default actions are set and fail as we cannot action it
            if ($null -ne $start_mode -or
                $null -ne $state -or
                $null -ne $username -or
                $null -ne $password -or
                $null -ne $display_name -or
                $null -ne $description -or
                $desktop_interact -ne $false -or
                $null -ne $dependencies -or
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
    $result = @{
        changed = $changed
        exists = $false
    }
} elseif ($null -ne $svc) {
    Get-ServiceInfo -name $name
}

Exit-Json -obj $result
