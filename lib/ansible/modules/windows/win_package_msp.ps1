#!powershell

# Copyright: (c) 2018, Rodric Vos <rodric@vosenterprises.eu>, and others
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.ArgvParser

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$expected_return_code = Get-AnsibleParam -obj $params -name "expected_return_code" -type "list" -default @(0, 3010)
$path = Get-AnsibleParam -obj $params -name "path" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$username = Get-AnsibleParam -obj $params -name "username" -type "str" -aliases "user_name"
$password = Get-AnsibleParam -obj $params -name "password" -type "str" -failifempty ($null -ne $username) -aliases "user_password"
$product_id = Get-AnsibleParam -obj $params -name "product_id" -type "str" -failifempty ($state -eq "absent") -aliases "productid"
$patch_id = Get-AnsibleParam -obj $params -name "patch_id" -type "str" -failifempty ($state -eq "absent") -aliases "patchid"
$patch_guid = Get-AnsibleParam -obj $params -name "patch_guid" -type "str" -failifempty ($state -eq "absent") -aliases "patchguid"

$result = @{
    changed = $false
    reboot_required = $false
}

$credential = $null
if ($null -ne $username) {
    $sec_user_password = ConvertTo-SecureString -String $password -AsPlainText -Force
    $credential = New-Object -TypeName PSCredential -ArgumentList $username, $sec_user_password
}

$valid_return_codes = @()
foreach ($rc in ($expected_return_code)) {
    try {
        $int_rc = [Int32]::Parse($rc)
        $valid_return_codes += $int_rc
    } catch {
        Fail-Json -obj $result -message "failed to parse expected return code $rc as an integer"
    }
}

if ($state -eq "absent") {
    if (-not $product_id -or -not $patch_id) {
        Fail-Json -obj $result -message "product_id and patch_id cannot be empty when state is absent"
    }
}

Add-Type -TypeDefinition @"
public enum LocationType {
    Empty,
    Local,
    Unc
}
"@

Add-Type -TypeDefinition @"
public enum ActionState {
    AbsentAndInstalled,
    AbsentAndNotInstalled,
    PresentAndInstalled,
    PresentAndNotInstalled
}
"@

function Get-ProgramMetadata {
    param(
        [string]$state,
        [string]$path,
        [string]$product_id,
        [string]$patch_id,
        [System.Management.Automation.PSCredential]
        [System.Management.Automation.Credential()]$credential
    )
    # will get some metadata about the program we are trying to install or remove
    $metadata = @{
        installed = $false
        location_type = $null
        path_error = $null
        action_state = $null
    }

    $drive = $null
    try {
        $drive = New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT
        $patchguid_key = "HKCR:\Installer\Patches\$patch_id"
        if (Test-Path -Path $patchguid_key) {
            $metadata.installed = $true
        }
    }
    catch {
        Fail-Json -obj $result -message "failed to lookup $patchguid_key in the Windows Registry: $($_.Exception.Message)"
    }
    finally {
        if ($drive) {
            Remove-PSDrive -Name $drive.Name
        }
    }

    switch($state)
    {
        "absent"
        {
            if ($metadata.installed) {
                $metadata.action_state = [ActionState]::AbsentAndInstalled
            } else {
                $metadata.action_state = [ActionState]::AbsentAndNotInstalled
            }
        }

        "present"
        {
            if ($metadata.installed) {
                $metadata.action_state = [ActionState]::PresentAndInstalled
            } else {
                $metadata.action_state = [ActionState]::PresentAndNotInstalled
                # set the location type and validate the path
                if ($path.StartsWith("/") -or $path.StartsWith("\\")) {
                    $metadata.location_type = [LocationType]::Unc
                    if ($credential) {
                        # Test-Path doesn't support supplying -Credentials, need to create PSDrive before testing
                        $file_path = Split-Path -Path $path
                        $file_name = Split-Path -Path $path -Leaf
                        try {
                            New-PSDrive -Name win_package -PSProvider FileSystem -Root $file_path -Credential $credential -Scope Script
                        } catch {
                            Fail-Json -obj $result -message "failed to connect network drive with credentials: $($_.Exception.Message)"
                        }
                        $test_path = "win_package:\$file_name"
                    } else {
                        # Someone is using an auth that supports credential delegation, at least it will fail otherwise
                        $test_path = $path
                    }

                    $valid_path = Test-Path -Path $test_path -PathType Leaf
                    if ($valid_path -ne $true) {
                        $metadata.path_error = "the file at the UNC path $path cannot be reached, ensure the user_name account has access to this path or use an auth transport with credential delegation"
                    }
                } else {
                    $metadata.location_type = [LocationType]::Local
                    $valid_path = Test-Path -Path $path -PathType Leaf
                    if ($valid_path -ne $true) {
                        $metadata.path_error = "the file at the local path $path cannot be reached"
                    }
                }

                # throw error if path is not valid
                if ($metadata.path_error) {
                    Fail-Json -obj $result -message $metadata.path_error
                }
            }
        }
    }

    return $metadata
}

function Convert-Encoding($string) {
    # this will attempt to detect UTF-16 encoding and convert to UTF-8 for
    # processes like msiexec
    $bytes = ([System.Text.Encoding]::Default).GetBytes($string)
    $is_utf16 = $true
    for ($i = 0; $i -lt $bytes.Count; $i = $i + 2) {
        $char = $bytes[$i + 1]
        if ($char -ne [byte]0) {
            $is_utf16 = $false
            break
        }
    }

    if ($is_utf16 -eq $true) {
        return ([System.Text.Encoding]::Unicode).GetString($bytes)
    } else {
        return $string
    }
}

$program_metadata = Get-ProgramMetadata -state $state -path $path -product_id $product_id -patch_id $patch_id -credential $credential

switch($program_metadata.action_state)
{
    "AbsentAndInstalled"
    {
        $temp_path = [System.IO.Path]::GetTempPath()
        $log_file = [System.IO.Path]::GetRandomFileName()
        $log_path = Join-Path -Path $temp_path -ChildPath $log_file

        $uninstall_arguments = @("$env:windir\system32\msiexec.exe", "/package", $product_id, "MSIPATCHREMOVE=$patch_guid", "/L*V", $log_path, "/qn", "/norestart")

        if (-not $check_mode) {
            $uninstall_command = Argv-ToString -arguments $uninstall_arguments

            try {
                $process_result = Run-Command -command $uninstall_command
            } catch {
                Fail-Json -obj $result -message "failed to run uninstall process ($uninstall_command): $($_.Exception.Message)"
            }

            if (($null -ne $log_path) -and (Test-Path -Path $log_path)) {
                $log_content = Get-Content -Path $log_path | Out-String
            } else {
                $log_content = $null
            }

            $result.rc = $process_result.rc
            $result.exit_code = $process_result.rc # deprecate in 2.8
            if ($valid_return_codes -notcontains $process_result.rc) {
                $result.stdout = Convert-Encoding -string $process_result.stdout
                $result.stderr = Convert-Encoding -string $process_result.stderr
                if ($null -ne $log_content) {
                    $result.log = $log_content
                }
                Fail-Json -obj $result -message "unexpected rc from uninstall $uninstall_exe $($uninstall_arguments): see rc, stdout and stderr for more details"
            } else {
                $result.failed = $false
            }

            if ($process_result.rc -eq 3010) {
                $result.reboot_required = $true
            }
        }

        $result.changed = $true
    }

    "AbsentAndNotInstalled"
    {
        # We're all good. Nothing changed.
    }

    "PresentAndInstalled"
    {
        # We're all good. Nothing changed.
    }

    "PresentAndNotInstalled"
    {
        $cleanup_artifacts = @()
        try {
            # If path is on a network and we specify credentials or path is a
            # URL and not an MSI we need to get a temp local copy
            if ($program_metadata.location_type -eq [LocationType]::Unc -and $null -ne $credential) {
                $file_name = Split-Path -Path $path -Leaf
                $local_path = [System.IO.Path]::GetRandomFileName()
                Copy-Item -Path "win_package:\$file_name" -Destination $local_path -WhatIf:$check_mode                                                
                $cleanup_artifacts += $local_path
            } else {
                $local_path = $path
            }

            $temp_path = [System.IO.Path]::GetTempPath()
            $log_file = [System.IO.Path]::GetRandomFileName()
            $log_path = Join-Path -Path $temp_path -ChildPath $log_file

            $cleanup_artifacts += $log_path
            $install_arguments = @("$env:windir\system32\msiexec.exe", "/p", $local_path, "/L*V", $log_path, "/qn", "/norestart")

            if (-not $check_mode) {
                $install_command = Argv-ToString -arguments $install_arguments

                try {
                    $process_result = Run-Command -command $install_command
                } catch {
                    Fail-Json -obj $result -message "failed to run install process ($install_command): $($_.Exception.Message)"
                }

                if (($null -ne $log_path) -and (Test-Path -Path $log_path)) {
                    $log_content = Get-Content -Path $log_path | Out-String
                } else {
                    $log_content = $null
                }

                $result.rc = $process_result.rc
                $result.exit_code = $process_result.rc # deprecate in 2.8
                if ($valid_return_codes -notcontains $process_result.rc) {
                    $result.stdout = Convert-Encoding -string $process_result.stdout
                    $result.stderr = Convert-Encoding -string $process_result.stderr
                    if ($null -ne $log_content) {
                        $result.log = $log_content
                    }
                    Fail-Json -obj $result -message "unexpected rc from install $install_exe $($install_arguments): see rc, stdout and stderr for more details"
                } else {
                    $result.failed = $false
                }

                if ($process_result.rc -eq 3010) {
                    $result.reboot_required = $true
                }
            }
        } finally {
            # make sure we cleanup any remaining artifacts
            foreach ($cleanup_artifact in $cleanup_artifacts) {
                if (Test-Path -Path $cleanup_artifact) {
                    Remove-Item -Path $cleanup_artifact -Recurse -Force -WhatIf:$check_mode
                }
            }
        }

        $result.changed = $true
    }
}

Exit-Json -obj $result