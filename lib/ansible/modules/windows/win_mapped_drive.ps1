#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$letter = Get-AnsibleParam -obj $params -name "letter" -type "str" -failifempty $true
$path = Get-AnsibleParam -obj $params -name "path" -type "path"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$username = Get-AnsibleParam -obj $params -name "username" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"

$result = @{
    changed = $false
}

if ($diff_mode) {
    $result.diff = @{}
}

if ($letter -notmatch "^[a-zA-z]{1}$") {
    Fail-Json $result "letter must be a single letter from A-Z, was: $letter"
}

Function Get-MappedDriveTarget($letter) {
    # Get-PSDrive and Get-CimInstance doesn't work through WinRM
    $target = $null
    if (Test-Path -Path HKCU:\Network\$letter) {
        $target = (Get-ItemProperty -Path HKCU:\Network\$letter -Name RemotePath).RemotePath
    }

    return $target
}

Function Remove-MappedDrive($letter) {
    # Remove-PSDrive doesn't work through WinRM as it cannot view the mapped drives for the user
    if (-not $check_mode) {
        try {
            &cmd.exe /c net use "$($letter):" /delete
        } catch {
            Fail-Json $result "failed to removed mapped drive $($letter): $($_.Exception.Message)"
        }
    }
}

$existing_target = Get-MappedDriveTarget -letter $letter

if ($state -eq "absent") {
    if ($existing_target -ne $null) {
        if ($path -ne $null) {
            if ($existing_target -eq $path) {
                Remove-MappedDrive -letter $letter
            } else {
                Fail-Json $result "did not delete mapped drive $letter, the target path is pointing to a different location at $existing_target"
            }
        } else {
            Remove-MappedDrive -letter $letter
        }

        $result.changed = $true
        if ($diff_mode) {
            $result.diff.prepared = "-$($letter): $existing_target"
        }
    }
} else {
    if ($path -eq $null) {
        Fail-Json $result "path must be set when creating a mapped drive"
    }

    $extra_args = @{}
    if ($username -ne $null) {
        $sec_password = ConvertTo-SecureString -String $password -AsPlainText -Force
        $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $sec_password
        $extra_args.Credential = $credential
    }

    $physical_drives = Get-PSDrive -PSProvider "FileSystem"
    if ($letter -in $physical_drives.Name) {
        Fail-Json $result "failed to create mapped drive $letter, this letter is in use and is pointing to a non UNC path"
    }

    if ($existing_target -ne $null) {
        if ($existing_target -ne $path -or ($username -ne $null)) {
            # the source path doesn't match or we are putting in a credential
            Remove-MappedDrive -letter $letter
            $result.changed = $true

            try {
                New-PSDrive -Name $letter -PSProvider "FileSystem" -root $path -Persist -WhatIf:$check_mode @extra_args | Out-Null
            } catch {
                Fail-Json $result "failed to create mapped drive $letter pointed to $($path): $($_.Exception.Message)"
            }

            if ($diff_mode) {
                $result.diff.prepared = "-$($letter): $existing_target`n+$($letter): $path"
            }
        }
    } else {
        try {
            New-PSDrive -Name $letter -PSProvider "FileSystem" -Root $path -Persist -WhatIf:$check_mode @extra_args | Out-Null
        } catch {
            Fail-Json $result "failed to create mapped drive $letter pointed to $($path): $($_.Exception.Message)"
        }

        $result.changed = $true
        if ($diff_mode) {
            $result.diff.prepared = "+$($letter): $path"
        }
    }
}

Exit-Json $result
