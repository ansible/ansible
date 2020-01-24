#!powershell

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$spec = @{
    options = @{
        arguments = @{ type = "raw" }
        expected_return_code = @{ type = "list"; elements = "int"; default = @(0, 3010) }
        path = @{ type = "str"}
        chdir = @{ type = "path" }
        product_id = @{ type = "str"; aliases = @(,"productid") }
        state = @{ type = "str"; default = "present"; choices = "absent", "present"; aliases = @(,"ensure") }
        username = @{ type = "str"; aliases = @(,"user_name") }
        password = @{ type = "str"; no_log = $true; aliases = @(,"user_password") }
        validate_certs = @{ type = "bool"; default = $true }
        creates_path = @{ type = "path" }
        creates_version = @{ type = "str" }
        creates_service = @{ type = "str" }
        log_path = @{ type = "path" }
    }
    required_by = @{
        creates_version = "creates_path"
    }
    required_if = @(
        @("state", "present", @("path")),
        @("state", "absent", @("path", "product_id"), $true)
    )
    required_together = @(,@("username", "password"))
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$check_mode = $module.CheckMode

$arguments = $module.Params.arguments
$expected_return_code = $module.Params.expected_return_code
$path = $module.Params.path
$chdir = $module.Params.chdir
$product_id = $module.Params.product_id
$state = $module.Params.state
$username = $module.Params.username
$password = $module.Params.password
$validate_certs = $module.Params.validate_certs
$creates_path = $module.Params.creates_path
$creates_version = $module.Params.creates_version
$creates_service = $module.Params.creates_service
$log_path = $module.Params.log_path

$module.Result.reboot_required = $false

if ($null -ne $arguments) {
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
if ($null -ne $username) {
    $sec_user_password = ConvertTo-SecureString -String $password -AsPlainText -Force
    $credential = New-Object -TypeName PSCredential -ArgumentList $username, $sec_user_password
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

Add-CSharpType -AnsibleModule $module -References @"
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
        $module.FailJson("failed to download $url to $($path): $($_.Exception.Message)", $_)
    }
}

Function Test-RegistryProperty($path, $name) {
    # will validate if the registry key contains the property, returns true
    # if the property exists and false if the property does not
    try {
        $value = (Get-Item -LiteralPath $path).GetValue($name)
        # need to do it this way return ($null -eq $value) does not work
        if ($null -eq $value) {
            return $false
        } else {
            return $true
        }
    } catch [System.Management.Automation.ItemNotFoundException] {
        # key didn't exist so the property mustn't
        return $false
    }
}

Function Get-ProgramMetadata($state, $path, $product_id, [PSCredential]$credential, $creates_path, $creates_version, $creates_service) {
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
    if ($null -ne $path) {
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
            if ($null -ne $credential) {
                # Test-Path doesn't support supplying -Credentials, need to create PSDrive before testing
                $file_path = Split-Path -Path $path
                $file_name = Split-Path -Path $path -Leaf
                try {
                    New-PSDrive -Name win_package -PSProvider FileSystem -Root $file_path -Credential $credential -Scope Script
                } catch {
                    $module.FailJson("failed to connect network drive with credentials: $($_.Exception.Message)", $_)
                }
                $test_path = "win_package:\$file_name"
            } else {
                # Someone is using an auth that supports credential delegation, at least it will fail otherwise
                $test_path = $path
            }

            $valid_path = Test-Path -LiteralPath $test_path -PathType Leaf
            if ($valid_path -ne $true) {
                $metadata.path_error = "the file at the UNC path $path cannot be reached, ensure the user_name account has access to this path or use an auth transport with credential delegation"
            }
        } else {
            $metadata.location_type = [LocationType]::Local
            $valid_path = Test-Path -LiteralPath $path -PathType Leaf
            if ($valid_path -ne $true) {
                $metadata.path_error = "the file at the local path $path cannot be reached"
            }
        }
    } else {
        # should only occur when state=absent and product_id is not null, we can get the uninstall string from the reg value
        $metadata.location_type = [LocationType]::Empty
    }

    # try and get the product id
    if ($null -ne $product_id) {
        $metadata.product_id = $product_id
    } else {
        # we can get the product_id if the path is an msi and is either a local file or unc file with credential delegation
        if (($metadata.msi -eq $true) -and (($metadata.location_type -eq [LocationType]::Local) -or ($metadata.location_type -eq [LocationType]::Unc -and $null -eq $credential))) {
            Add-CSharpType -AnsibleModule $module -References $msi_tools
            try {
                $metadata.product_id = [Ansible.MsiTools]::GetPackageProperty($path, "ProductCode")
            } catch {
                $module.FailJson("failed to get product_id from MSI at $($path): $($_.Exception.Message)", $_)
            }
        } elseif ($null -eq $creates_path -and $null -eq $creates_service) {
            # we need to fail without the product id at this point
            $module.FailJson("product_id is required when the path is not an MSI or the path is an MSI but not local")
        }
    }

    if ($null -ne $metadata.product_id) {
        $uninstall_key = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$($metadata.product_id)"
        $uninstall_key_wow64 = "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\$($metadata.product_id)"
        if (Test-Path -LiteralPath $uninstall_key) {
            $metadata.installed = $true
        } elseif (Test-Path -LiteralPath $uninstall_key_wow64) {
            $metadata.installed = $true
            $uninstall_key = $uninstall_key_wow64
        }

        # if the reg key exists, try and get the uninstall string and check if it is an MSI
        if ($metadata.installed -eq $true -and $metadata.location_type -eq [LocationType]::Empty) {
            if (Test-RegistryProperty -path $uninstall_key -name "UninstallString") {
                $metadata.uninstall_string = (Get-ItemProperty -LiteralPath $uninstall_key -Name "UninstallString").UninstallString
                if ($metadata.uninstall_string.StartsWith("MsiExec")) {
                    $metadata.msi = $true
                }
            }
        }
    }

    # use the creates_* to determine if the program is installed
    if ($null -ne $creates_path) {
        $path_exists = Test-Path -LiteralPath $creates_path
        $metadata.installed = $path_exists

        if ($null -ne $creates_version -and $path_exists -eq $true) {
            if (Test-Path -LiteralPath $creates_path -PathType Leaf) {
                $existing_version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($creates_path).FileVersion
                $version_matched = $creates_version -eq $existing_version
                $metadata.installed = $version_matched
            } else {
                $module.FailJson("creates_path must be a file not a directory when creates_version is set")
            }
        }
    }
    if ($null -ne $creates_service) {
        $existing_service = Get-Service -Name $creates_service -ErrorAction SilentlyContinue
        $service_exists = $null -ne $existing_service
        $metadata.installed = $service_exists
    }


    # finally throw error if path is not valid unless we want to uninstall the package and it already is
    if ($null -ne $metadata.path_error -and (-not ($state -eq "absent" -and $metadata.installed -eq $false))) {
        $module.FailJson($metadata.path_error)
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
            if ($program_metadata.location_type -eq [LocationType]::Unc -and $null -ne $credential) {
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
                if ( -Not $log_path ) {
                    $temp_path = [System.IO.Path]::GetTempPath()
                    $log_file = [System.IO.Path]::GetRandomFileName()
                    $log_path = Join-Path -Path $temp_path -ChildPath $log_file
                    $cleanup_artifacts += $log_path
                }

                if ($null -ne $program_metadata.product_id) {
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
                $command_args = @{
                    command = Argv-ToString -arguments $uninstall_arguments
                }
                if ($null -ne $arguments) {
                    $command_args['command'] += " $arguments"
                }
                if ($chdir) {
                    $command_args['working_directory'] = $chdir
                }

                try {
                    $process_result = Run-Command @command_args
                } catch {
                    $module.FailJson("failed to run uninstall process ($($command_args['command'])): $($_.Exception.Message)", $_)
                }

                if (($null -ne $log_path) -and (Test-Path -LiteralPath $log_path)) {
                    $log_content = Get-Content -Path $log_path | Out-String
                } else {
                    $log_content = $null
                }

                $module.Result.rc = $process_result.rc
                if ($expected_return_code -notcontains $process_result.rc) {
                    $module.Result.stdout = Convert-Encoding -string $process_result.stdout
                    $module.Result.stderr = Convert-Encoding -string $process_result.stderr
                    if ($null -ne $log_content) {
                        $module.Result.log = $log_content
                    }
                    $module.FailJson("unexpected rc from uninstall $uninstall_exe $($uninstall_arguments): see rc, stdout and stderr for more details")
                } else {
                    $module.Result.failed = $false
                }

                if ($process_result.rc -eq 3010) {
                    $module.Result.reboot_required = $true
                }
            }
        } finally {
            # make sure we cleanup any remaining artifacts
            foreach ($cleanup_artifact in $cleanup_artifacts) {
                if (Test-Path -LiteralPath $cleanup_artifact) {
                    Remove-Item -Path $cleanup_artifact -Recurse -Force -WhatIf:$check_mode
                }
            }
        }

        $module.Result.changed = $true
    }
} else {
    if ($program_metadata.installed -eq $false) {
        # artifacts we create that must be cleaned up
        $cleanup_artifacts = @()
        try {
            # If path is on a network and we specify credentials or path is a
            # URL and not an MSI we need to get a temp local copy
            if ($program_metadata.location_type -eq [LocationType]::Unc -and $null -ne $credential) {
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
                if ( -Not $log_path ) {
                    $temp_path = [System.IO.Path]::GetTempPath()
                    $log_file = [System.IO.Path]::GetRandomFileName()
                    $log_path = Join-Path -Path $temp_path -ChildPath $log_file
                    $cleanup_artifacts += $log_path
                }

                $install_arguments = @("$env:windir\system32\msiexec.exe", "/i", $local_path, "/L*V", $log_path, "/qn", "/norestart")
            } else {
                $log_path = $null
                $install_arguments = @($local_path)
            }

            if (-not $check_mode) {
                $command_args = @{
                    command = Argv-ToString -arguments $install_arguments
                }
                if ($null -ne $arguments) {
                    $command_args['command'] += " $arguments"
                }
                if ($chdir) {
                    $command_args['working_directory'] = $chdir
                }

                try {
                    $process_result = Run-Command @command_args
                } catch {
                    $module.FailJson("failed to run install process ($($command_args['command'])): $($_.Exception.Message)", $_)
                }

                if (($null -ne $log_path) -and (Test-Path -LiteralPath $log_path)) {
                    $log_content = Get-Content -Path $log_path | Out-String
                } else {
                    $log_content = $null
                }

                $module.Result.rc = $process_result.rc
                if ($expected_return_code -notcontains $process_result.rc) {
                    $module.Result.stdout = Convert-Encoding -string $process_result.stdout
                    $module.Result.stderr = Convert-Encoding -string $process_result.stderr
                    if ($null -ne $log_content) {
                        $module.Result.log = $log_content
                    }
                    $module.FailJson("unexpected rc from install $install_exe $($install_arguments): see rc, stdout and stderr for more details")
                } else {
                    $module.Result.failed = $false
                }

                if ($process_result.rc -eq 3010) {
                    $module.Result.reboot_required = $true
                }
            }
        } finally {
            # make sure we cleanup any remaining artifacts
            foreach ($cleanup_artifact in $cleanup_artifacts) {
                if (Test-Path -LiteralPath $cleanup_artifact) {
                    Remove-Item -Path $cleanup_artifact -Recurse -Force -WhatIf:$check_mode
                }
            }
        }

        $module.Result.changed = $true
    }
}

$module.ExitJson()

