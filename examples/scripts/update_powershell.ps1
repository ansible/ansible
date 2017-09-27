<#
.SYNOPSIS
    Used to upgrade powershell to the target version with the required
    pre-requisites list .NET Framework 4.5.2.
.DESCRIPTION
    The script will upgrade the powershell version to whatever is supplied as
    the 'target_version' on the host (see PARAMETER target_version for
    supported targets).

    This script can be run on the following OS'
        Windows Server 2008 (with SP2) - only supported target_version 3.0
        Windows Server 2008 R2 (with SP1)
        Windows Server 2012
        Windows Server 2012 R2
        Windows Server 2016

        Windows 7 (with SP1)
        Windows 8.1
        Windows 10
    
    All OS' can be upgraded to 5.1 except for Windows Server 2008. If running
    on Powershell 1.0 then this script will first upgrade the version to 2.0
    before running the checks. This is because a lot of the upgrade paths need
    this version installed as a baseline. If the .NET Framework version
    installed is less than 4.5.2, it will be upgraded to 4.5.2 as this is
    supported on all hosts and is required for v5.0.

    As multiple packages can be installed in this process, multiple reboots may
    be required to continue with the install. If a reboot is required the
    script will detech if the 'username' and 'password' parameters have been
    supplied. If they have been supplied it will automatically reboot and login
    to continue the install process until it is all complete. If these
    parameters are not set then it will prompt the user for a reboot and
    require the user to log back in manually after the reboot before
    continuing.

    A log of this process is created in
    $env:SystemDrive\temp\update_powershell.log which is usually C:\temp\. This
    log can used to see how the script faired after an automatic reboot.
.PARAMETER target_version
    [string] - The target powershell version to upgrade to. This can be;
        3.0,
        4.0, or
        5.1 (default)
    Depending on the circumstances, the process to reach the target version
    may require multiple reboots.
.PARAMETER username
    [string] - The username of a local admin user that will be automatically
    logged in after a reboot to continue the script install. The 'password'
    parameter is also required if this is set.
.PARAMETER password
    [string] - The password for 'username', this is required if the 'username'
    parameter is also set.
.PARAMETER Verbose
    [switch] - Whether to display Verbose logs on the console
.EXAMPLE
    # upgrade from powershell 1.0 to 3.0 with automatic login and reboots
    Set-ExecutionPolicy Unrestricted -Force
    &.\update_powershell.ps1 -target_version 3.0 -username "Administrator" -password "Password" -Verbose
.EXAMPLE
    # upgrade to 5.1 with defaults and manual login and reboots
    powershell.exe -ExecutionPolicy ByPass -File winrm_hotfix.ps1
.EXAMPLE
    # upgrade to powershell 4.0 with automatic login and reboots
    powershell.exe -ExecutionPolicy ByPass -File winrm_hotfix.ps1 -target_version 4.0 -username "Administrator" -password "Password" -Verbose
.NOTES
    Author: Jordan Borean <jborean93@gmail.com>
    Contributors:

    Version 1.0: 2017-09-27
        Initial script created
#>
Param(
    [string]$target_version = "5.1",
    [string]$username,
    [string]$password,
    [switch]$verbose = $false
)
$ErrorActionPreference = 'Stop'
if ($verbose) {
    $VerbosePreference = "Continue"
}

$tmp_dir = "$env:SystemDrive\temp"
if (-not (Test-Path -Path $tmp_dir)) {
    New-Item -Path $tmp_dir -ItemType Directory > $null
}

Function Write-Log($message, $level="INFO") {
    # Poor man's implementation of Log4Net
    $date_stamp = Get-Date -Format s
    $log_entry = "$date_stamp - $level - $message"
    $log_file = "$tmp_dir\update_powershell.log"
    Write-Verbose -Message $log_entry
    Add-Content -Path $log_file -Value $log_entry
}

Function Reboot-AndResume {
    Write-Log -message "adding script to run on next logon"
    $script_path = $script:MyInvocation.MyCommand.Path
    $ps_path = "$env:SystemDrive\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    $arguments = "-target_version $target_version"
    if ($username -and $password) {
        $arguments = "$arguments -username `"$username`" -password `"$password`""
    }
    if ($verbose) {
        $arguments = "$arguments -Verbose"
    }

    $command = "$ps_path -ExecutionPolicy ByPass -File $script_path $arguments"
    $reg_key = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
    $reg_property_name = "ps-upgrade"
    Set-ItemProperty -Path $reg_key -Name $reg_property_name -Value $command

    if ($username -and $password) {
        $reg_winlogon_path = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
        Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 1
        Set-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -Value $username
        Set-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -Value $password
        Write-Log -message "rebooting server to continue powershell upgrade"
    } else {
        Write-Log -message "need to reboot server to continue powershell upgrade"
        $reboot_confirmation = Read-Host -Prompt "need to reboot server to continue powershell upgrade, do you wish to proceed (y/n)"
        if ($reboot_confirmation -ne "y") {
            $error_msg = "please reboot server manually and login to continue upgrade process, the script will restart on the next login automatically"
            Write-Log -message $error_msg -level "ERROR"
            throw $error_msg
        }
    }

    if (Get-Command -Name Restart-Computer -ErrorAction SilentlyContinue) {
        Restart-Computer -Force
    } else {
        # PS v1 (Server 2008) doesn't have the cmdlet Restart-Computer, use el-traditional
        shutdown /r /t 0
    }
}

Function Run-Process($executable, $arguments) {
    $process = New-Object -TypeName System.Diagnostics.Process
    $psi = $process.StartInfo
    $psi.FileName = $executable
    $psi.Arguments = $arguments
    Write-Log -message "starting new process '$executable $arguments'"
    $process.Start() | Out-Null
    
    $process.WaitForExit() | Out-Null
    $exit_code = $process.ExitCode
    Write-Log -message "process completed with exit code '$exit_code'"

    return $exit_code
}

Function Download-File($url, $path) {
    Write-Log -message "downloading url '$url' to '$path'"
    $client = New-Object -TypeName System.Net.WebClient
    $client.DownloadFile($url, $path)
}

Function Clear-AutoLogon {
    $reg_winlogon_path = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
    Write-Log -message "clearing auto logon registry properties"
    Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 0
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -ErrorAction SilentlyContinue
}

Function Download-Wmf5Server2008($architecture) {
    if ($architecture -eq "x64") {
        $zip_url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/Win7AndW2K8R2-KB3191566-x64.zip"
        $file = "$tmp_dir\Win7AndW2K8R2-KB3191566-x64.msu"
    } else {
        $zip_url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/Win7-KB3191566-x86.zip"
        $file = "$tmp_dir\Win7-KB3191566-x86.msu"
    }
    if (Test-Path -Path $file) {
        return $file
    }

    $filename = $zip_url.Split("/")[-1]
    $zip_file = "$tmp_dir\$filename"
    Download-File -url $zip_url -path $zip_file

    Write-Log -message "extracting '$zip_file' to '$tmp_dir'"
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem > $null
        $legacy = $false
    } catch {
        $legacy = $true
    }

    if ($legacy) {
        $shell = New-Object -ComObject Shell.Application
        $zip_src = $shell.NameSpace($zip_file)
        $zip_dest = $shell.NameSpace($tmp_dir)
        $zip_dest.CopyHere($zip_src.Items(), 1044)
    } else {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zip_file, $tmp_dir)
    }

    return $file
}

Write-Log -message "starting script"
# on PS v1.0, upgrade to 2.0 and then run the script again
if ($PSVersionTable -eq $null) {
    Write-Log -message "upgrading powershell v1.0 to v2.0"
    $architecture = $env:PROCESSOR_ARCHITECTURE
    if ($architecture -eq "AMD64") {
        $url = "https://download.microsoft.com/download/2/8/6/28686477-3242-4E96-9009-30B16BED89AF/Windows6.0-KB968930-x64.msu"
    } else {
        $url = "https://download.microsoft.com/download/F/9/E/F9EF6ACB-2BA8-4845-9C10-85FC4A69B207/Windows6.0-KB968930-x86.msu"
    }
    $filename = $url.Split("/")[-1]
    $file = "$tmp_dir\$filename"
    Download-File -url $url -path $file
    $exit_code = Run-Process -executable $file -arguments "/quiet /norestart"
    if ($exit_code -ne 0 -and $exit_code -ne 3010) {
        $error_msg = "failed to update Powershell from 1.0 to 2.0: exit code $exit_code"
        Write-Log -message $error_msg -level "ERROR"
        throw $error_msg
    }
    Reboot-AndResume
}

# exit if the target version is the same as the actual version
$current_ps_version = [version]"$($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)"
if ($current_ps_version -eq [version]$target_version) {
    Write-Log -message "current and target PS version are the same, no action is required"
    Clear-AutoLogon
    exit 0
}

$os_version = [System.Environment]::OSVersion.Version
$architecture = $env:PROCESSOR_ARCHITECTURE
if ($architecture -eq "AMD64") {
    $architecture = "x64"
} else {
    $architecture = "x86"
}

$actions = @()
switch ($target_version) {
    "3.0" {
        $actions += "3.0"
        break
    }
    "4.0" {
        if ($os_version -lt [version]"6.1") {
            $error_msg = "cannot upgrade Server 2008 to Powershell v4, v3 is the latest supported"
            Write-Log -message $error_msg -level "ERROR"
            throw $error_msg
        }
        $actions += "4.0"
        break
    }
    "5.1" {
        if ($os_version -lt [version]"6.1") {
            $error_msg = "cannot upgrade Server 2008 to Powershell v5.1, v3 is the latest supported"
            Write-Log -message $error_msg -level "ERROR"
            throw $error_msg
        }
        # check if WMF 3 is installed, need to be uninstalled before 5.1
        if ($os_version.Minor -lt 2) {
            $wmf3_installed = Get-Hotfix -Id "KB2506143" -ErrorAction SilentlyContinue
            if ($wmf3_installed) {
                $actions += "remove-3.0"
            }
        }
        $actions += "5.1"
        break
    }
    default {
        $error_msg = "target_version '$target_version' is not supported in this upgrade script"
        Write-Log -message $error_msg -level "ERROR"
        throw $error_msg
    }
}

# detect if .NET 4.5.2 is not installed and add to the actions
$dotnet_path = "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full"
if (-not (Test-Path -Path $dotnet_path)) {
    $dotnet_upgrade_needed = $true
} else {
    $dotnet_version = Get-ItemProperty -Path $dotnet_path -Name Release -ErrorAction SilentlyContinue
    if ($dotnet_version) {
        # 379893 == 4.5.2
        if ($dotnet_version.Release -lt 379893) {
            $dotnet_upgrade_needed = $true
        }        
    } else {
        $dotnet_upgrade_needed = $true
    }
}
if ($dotnet_upgrade_needed) {
    $actions = @("dotnet") + $actions
}

Write-Log -message "The following actions will be performed: $($actions -join ", ")"
foreach ($action in $actions) {
    $url = $null
    $file = $null
    $arguments = "/quiet /norestart"

    switch ($action) {
        "dotnet" {
            Write-Log -message "running .NET update to 4.5.2"
            $url = "https://download.microsoft.com/download/E/2/1/E21644B5-2DF2-47C2-91BD-63C560427900/NDP452-KB2901907-x86-x64-AllOS-ENU.exe"
            $error_msg = "failed to update .NET to 4.5.2"
            $arguments = "/q /norestart"
            break
        }
        "remove-3.0" {
            # this is only run before a 5.1 install on Windows 7/2008 R2, the
            # install zip needs to be downloaded and extracted before
            # removing 3.0 as then the FileSystem assembly cannot be loaded
            Write-Log -message "downloading WMF/PS v5.1 and removing WMF/PS v3 before version 5.1 install"
            Download-Wmf5Server2008 -architecture $architecture > $null

            $file = "wusa.exe"
            $arguments = "/uninstall /KB:2506143 /quiet /norestart"
            break
        }
        "3.0" {
            Write-Log -message "running powershell update to version 3"    
            if ($os_version.Minor -eq 1) {
                $url = "https://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.1-KB2506143-$($architecture).msu"
            } else {
                $url = "https://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.0-KB2506146-$($architecture).msu"
            }
            $error_msg = "failed to update Powershell to version 3"
            break
        }
        "4.0" {
            Write-Log -message "running powershell update to version 4"
            if ($os_version.Minor -eq 1) {
                $url = "https://download.microsoft.com/download/3/D/6/3D61D262-8549-4769-A660-230B67E15B25/Windows6.1-KB2819745-$($architecture)-MultiPkg.msu"
            } else {
                $url = "https://download.microsoft.com/download/3/D/6/3D61D262-8549-4769-A660-230B67E15B25/Windows8-RT-KB2799888-x64.msu"
            }
            $error_msg = "failed to update Powershell to version 4"
            break
        }
        "5.1" {
            Write-Log -message "running powershell update to version 5.1"
            if ($os_version.Minor -eq 1) {
                # Server 2008 R2 and Windows 7, already downloaded in remove-3.0
                $file = Download-Wmf5Server2008 -architecture $architecture
            } elseif ($os_version.Minor -eq 2) {
                # Server 2012
                $url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/W2K12-KB3191565-x64.msu"
            } else {
                # Server 2012 R2 and Windows 8.1
                if ($architecture -eq "x64") {
                    $url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/Win8.1AndW2K12R2-KB3191564-x64.msu"
                } else {
                    $url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/Win8.1-KB3191564-x86.msu"
                }
            }
            break
        }
        default {
            $error_msg = "unknown action '$action'"
            Write-Log -message $error_msg -level "ERROR"
        }
    }

    if ($file -eq $null) {
        $filename = $url.Split("/")[-1]
        $file = "$tmp_dir\$filename"
    }
    if ($url -ne $null) {
        Download-File -url $url -path $file
    }
    
    $exit_code = Run-Process -executable $file -arguments $arguments
    if ($exit_code -ne 0 -and $exit_code -ne 3010) {
        $log_msg = "$($error_msg): exit code $exit_code"
        Write-Log -message $log_msg -level "ERROR"
        throw $log_msg
    }
    if ($exit_code -eq 3010) {
        Reboot-AndResume
        break
    }
}
