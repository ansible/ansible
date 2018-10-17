#!powershell

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.ArgvParser

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$arguments = Get-AnsibleParam -obj $params -name "arguments"
$expected_return_code = Get-AnsibleParam -obj $params -name "expected_return_code" -type "list" -default @(0, 3010)
$path = Get-AnsibleParam -obj $params -name "path" -type "str"
$product_id = Get-AnsibleParam -obj $params -name "product_id" -type "str" -aliases "productid"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present" -aliases "ensure"
$username = Get-AnsibleParam -obj $params -name "username" -type "str" -aliases "user_name"
$password = Get-AnsibleParam -obj $params -name "password" -type "str" -failifempty ($username -ne $null) -aliases "user_password"
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$creates_path = Get-AnsibleParam -obj $params -name "creates_path" -type "path"
$creates_version = Get-AnsibleParam -obj $params -name "creates_version" -type "str"
$creates_service = Get-AnsibleParam -obj $params -name "creates_service" -type "str"

$result = @{
    changed = $false
    reboot_required = $false
    restart_required = $false # deprecate in 2.8
}

if ($arguments -ne $null) {
    # convert a list to a string and escape the values
    if ($arguments -is [array]) {
        $arguments = Argv-ToString -arguments $arguments
    }
}

if (-not $validate_certs) {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
}

# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protcols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
if ([Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protcols = $security_protcols -bor [Net.SecurityProtocolType]::Tls11
}
if ([Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protcols = $security_protcols -bor [Net.SecurityProtocolType]::Tls12
}
[Net.ServicePointManager]::SecurityProtocol = $security_protcols

$credential = $null
if ($username -ne $null) {
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

if ($path -eq $null) {
    if (-not ($state -eq "absent" -and $product_id -ne $null)) {
        Fail-Json -obj $result -message "path can only be null when state=absent and product_id is not null"
    }
}

if ($creates_version -ne $null -and $creates_path -eq $null) {
    Fail-Json -obj $result -Message "creates_path must be set when creates_version is set"
}

$msi_tools = @"
using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible {
    public static class MsiTools {
        [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
        private static extern UInt32 MsiOpenPackageW(string szPackagePath, out IntPtr hProduct);

        [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
        private static extern uint MsiCloseHandle(IntPtr hAny);

        [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
        private static extern uint MsiGetPropertyW(IntPtr hAny, string name, StringBuilder buffer, ref int bufferLength);

        public static string GetPackageProperty(string msi, string property) {
            IntPtr MsiHandle = IntPtr.Zero;
            try {
                uint res = MsiOpenPackageW(msi, out MsiHandle);
                if (res != 0)
                    return null;
                
                int length = 256;
                var buffer = new StringBuilder(length);
                res = MsiGetPropertyW(MsiHandle, property, buffer, ref length);
                return buffer.ToString();
            } finally {
                if (MsiHandle != IntPtr.Zero)
                    MsiCloseHandle(MsiHandle);
            }
        }
    }
}
"@

Add-Type -TypeDefinition @"
public enum LocationType {
    Empty,
    Local,
    Unc,
    Http
}
"@

Function Download-File($url, $path) {
    $web_client = New-Object -TypeName System.Net.WebClient
    try {
        $web_client.DownloadFile($url, $path)
    } catch {
        Fail-Json -obj $result -message "failed to download $url to $($path): $($_.Exception.Message)"
    }
}

Function Test-RegistryProperty($path, $name) {
    # will validate if the registry key contains the property, returns true
    # if the property exists and false if the property does not
    try {
        $value = (Get-Item -Path $path).GetValue($name)
        # need to do it this way return ($value -eq $null) does not work
        if ($value -eq $null) {
            return $false
        } else {
            return $true
        }
    } catch [System.Management.Automation.ItemNotFoundException] {
        # key didn't exist so the property mustn't
        return $false
    }
}

Function Get-ProgramMetadata($state, $path, $product_id, $credential, $creates_path, $creates_version, $creates_service) {
    # will get some metadata about the program we are trying to install or remove
    $metadata = @{
        installed = $false
        product_id = $null
        location_type = $null
        msi = $false
        uninstall_string = $null
        path_error = $null
    }

    # set the location type and validate the path
    if ($path -ne $null) {
        if ($path.EndsWith(".msi", [System.StringComparison]::CurrentCultureIgnoreCase)) {
            $metadata.msi = $true
        } else {
            $metadata.msi = $false
        }

        if ($path.StartsWith("http")) {
            $metadata.location_type = [LocationType]::Http
            try {
                Invoke-WebRequest -Uri $path -DisableKeepAlive -UseBasicParsing -Method HEAD | Out-Null
            } catch {
                $metadata.path_error = "the file at the URL $path cannot be reached: $($_.Exception.Message)"
            }
        } elseif ($path.StartsWith("/") -or $path.StartsWith("\\")) {
            $metadata.location_type = [LocationType]::Unc
            if ($credential -ne $null) {
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
    } else {
        # should only occur when state=absent and product_id is not null, we can get the uninstall string from the reg value
        $metadata.location_type = [LocationType]::Empty
    }

    # try and get the product id
    if ($product_id -ne $null) {
        $metadata.product_id = $product_id
    } else {
        # we can get the product_id if the path is an msi and is either a local file or unc file with credential delegation
        if (($metadata.msi -eq $true) -and (($metadata.location_type -eq [LocationType]::Local) -or ($metadata.location_type -eq [LocationType]::Unc -and $credential -eq $null))) {
            Add-Type -TypeDefinition $msi_tools
            try {
                $metadata.product_id = [Ansible.MsiTools]::GetPackageProperty($path, "ProductCode")
            } catch {
                Fail-Json -obj $result -message "failed to get product_id from MSI at $($path): $($_.Exception.Message)"
            }
        } elseif ($creates_path -eq $null -and $creates_service -eq $null) {
            # we need to fail without the product id at this point
            Fail-Json $result "product_id is required when the path is not an MSI or the path is an MSI but not local"
        }
    }

    if ($metadata.product_id -ne $null) {
        $uninstall_key = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$($metadata.product_id)"
        $uninstall_key_wow64 = "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\$($metadata.product_id)"
        if (Test-Path -Path $uninstall_key) {
            $metadata.installed = $true
        } elseif (Test-Path -Path $uninstall_key_wow64) {
            $metadata.installed = $true
            $uninstall_key = $uninstall_key_wow64
        }

        # if the reg key exists, try and get the uninstall string and check if it is an MSI
        if ($metadata.installed -eq $true -and $metadata.location_type -eq [LocationType]::Empty) {
            if (Test-RegistryProperty -path $uninstall_key -name "UninstallString") {
                $metadata.uninstall_string = (Get-ItemProperty -Path $uninstall_key -Name "UninstallString").UninstallString
                if ($metadata.uninstall_string.StartsWith("MsiExec")) {
                    $metadata.msi = $true
                }
            }
        }
    }

    # use the creates_* to determine if the program is installed
    if ($creates_path -ne $null) {
        $path_exists = Test-Path -Path $creates_path
        $metadata.installed = $path_exists
        
        if ($creates_version -ne $null -and $path_exists -eq $true) {
            if (Test-Path -Path $creates_path -PathType Leaf) {
                $existing_version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($creates_path).FileVersion
                $version_matched = $creates_version -eq $existing_version
                $metadata.installed = $version_matched
            } else {
                Fail-Json -obj $result -message "creates_path must be a file not a directory when creates_version is set"
            }
        }
    }
    if ($creates_service -ne $null) {
        $existing_service = Get-Service -Name $creates_service -ErrorAction SilentlyContinue
        $service_exists = $existing_service -ne $null
        $metadata.installed = $service_exists
    }


    # finally throw error if path is not valid unless we want to uninstall the package and it already is
    if ($metadata.path_error -ne $null -and (-not ($state -eq "absent" -and $metadata.installed -eq $false))) {
        Fail-Json -obj $result -message $metadata.path_error
    }

    return $metadata
}

Function Convert-Encoding($string) {
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

$program_metadata = Get-ProgramMetadata -state $state -path $path -product_id $product_id -credential $credential -creates_path $creates_path -creates_version $creates_version -creates_service $creates_service
if ($state -eq "absent") {
    if ($program_metadata.installed -eq $true) {      
        # artifacts we create that must be cleaned up
        $cleanup_artifacts = @()
        try {
            # If path is on a network and we specify credentials or path is a
            # URL and not an MSI we need to get a temp local copy
            if ($program_metadata.location_type -eq [LocationType]::Unc -and $credential -ne $null) {
                $file_name = Split-Path -Path $path -Leaf
                $local_path = [System.IO.Path]::GetRandomFileName()
                Copy-Item -Path "win_package:\$file_name" -Destination $local_path -WhatIf:$check_mode
                $cleanup_artifacts += $local_path
            } elseif ($program_metadata.location_type -eq [LocationType]::Http -and $program_metadata.msi -ne $true) {
                $local_path = [System.IO.Path]::GetRandomFileName()

                if (-not $check_mode) {
                    Download-File -url $path -path $local_path
                }
                $cleanup_artifacts += $local_path
            } elseif ($program_metadata.location_type -eq [LocationType]::Empty -and $program_metadata.msi -ne $true) {
                # TODO validate the uninstall_string to see if there are extra args in there
                $local_path = $program_metadata.uninstall_string
            } else {
                $local_path = $path
            }

            if ($program_metadata.msi -eq $true) {
                # we are uninstalling an msi
                $temp_path = [System.IO.Path]::GetTempPath()
                $log_file = [System.IO.Path]::GetRandomFileName()
                $log_path = Join-Path -Path $temp_path -ChildPath $log_file
                $cleanup_artifacts += $log_path

                if ($program_metadata.product_id -ne $null) {
                    $id = $program_metadata.product_id
                } else {
                    $id = $local_path
                }

                $uninstall_arguments = @("$env:windir\system32\msiexec.exe", "/x", $id, "/L*V", $log_path, "/qn", "/norestart")
            } else {
                $log_path = $null
                $uninstall_arguments = @($local_path)
            }

            if (-not $check_mode) {
                $uninstall_command = Argv-ToString -arguments $uninstall_arguments
                if ($arguments -ne $null) {
                    $uninstall_command += " $arguments"
                }
                
                try {
                    $process_result = Run-Command -command $uninstall_command
                } catch {
                    Fail-Json -obj $result -message "failed to run uninstall process ($uninstall_command): $($_.Exception.Message)"
                }

                if (($log_path -ne $null) -and (Test-Path -Path $log_path)) {
                    $log_content = Get-Content -Path $log_path | Out-String
                } else {
                    $log_content = $null
                }

                $result.rc = $process_result.rc
                $result.exit_code = $process_result.rc # deprecate in 2.8
                if ($valid_return_codes -notcontains $process_result.rc) {
                    $result.stdout = Convert-Encoding -string $process_result.stdout
                    $result.stderr = Convert-Encoding -string $process_result.stderr
                    if ($log_content -ne $null) {
                        $result.log = $log_content
                    }
                    Fail-Json -obj $result -message "unexpected rc from uninstall $uninstall_exe $($uninstall_arguments): see rc, stdout and stderr for more details"
                } else {
                    $result.failed = $false
                }

                if ($process_result.rc -eq 3010) {
                    $result.reboot_required = $true
                    $result.restart_required = $true
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
} else {
    if ($program_metadata.installed -eq $false) {
        # artifacts we create that must be cleaned up
        $cleanup_artifacts = @()
        try {
            # If path is on a network and we specify credentials or path is a
            # URL and not an MSI we need to get a temp local copy
            if ($program_metadata.location_type -eq [LocationType]::Unc -and $credential -ne $null) {
                $file_name = Split-Path -Path $path -Leaf
                $local_path = [System.IO.Path]::GetRandomFileName()
                Copy-Item -Path "win_package:\$file_name" -Destination $local_path -WhatIf:$check_mode                                                
                $cleanup_artifacts += $local_path
            } elseif ($program_metadata.location_type -eq [LocationType]::Http -and $program_metadata.msi -ne $true) {
                $local_path = [System.IO.Path]::GetRandomFileName()

                if (-not $check_mode) {
                    Download-File -url $path -path $local_path
                }
                $cleanup_artifacts += $local_path
            } else {
                $local_path = $path
            }

            if ($program_metadata.msi -eq $true) {
                # we are installing an msi
                $temp_path = [System.IO.Path]::GetTempPath()
                $log_file = [System.IO.Path]::GetRandomFileName()
                $log_path = Join-Path -Path $temp_path -ChildPath $log_file
                
                $cleanup_artifacts += $log_path
                $install_arguments = @("$env:windir\system32\msiexec.exe", "/i", $local_path, "/L*V", $log_path, "/qn", "/norestart")
            } else {
                $log_path = $null                
                $install_arguments = @($local_path)
            }

            if (-not $check_mode) {
                $install_command = Argv-ToString -arguments $install_arguments
                if ($arguments -ne $null) {
                    $install_command += " $arguments"
                }
                
                try {
                    $process_result = Run-Command -command $install_command
                } catch {
                    Fail-Json -obj $result -message "failed to run install process ($install_command): $($_.Exception.Message)"
                }
                
                if (($log_path -ne $null) -and (Test-Path -Path $log_path)) {
                    $log_content = Get-Content -Path $log_path | Out-String
                } else {
                    $log_content = $null
                }

                $result.rc = $process_result.rc
                $result.exit_code = $process_result.rc # deprecate in 2.8
                if ($valid_return_codes -notcontains $process_result.rc) {
                    $result.stdout = Convert-Encoding -string $process_result.stdout
                    $result.stderr = Convert-Encoding -string $process_result.stderr
                    if ($log_content -ne $null) {
                        $result.log = $log_content
                    }
                    Fail-Json -obj $result -message "unexpected rc from install $install_exe $($install_arguments): see rc, stdout and stderr for more details"
                } else {
                    $result.failed = $false
                }

                if ($process_result.rc -eq 3010) {
                    $result.reboot_required = $true
                    $result.restart_required = $true
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
