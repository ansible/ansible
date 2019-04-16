#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$hotfix_kb = Get-AnsibleParam -obj $params -name "hotfix_kb" -type "str"
$hotfix_identifier = Get-AnsibleParam -obj $params -name "hotfix_identifier" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "state" -default "present" -validateset "absent","present"
$source = Get-AnsibleParam -obj $params -name "source" -type "path"

$result = @{
    changed = $false
    reboot_required = $false
}

if (Get-Module -Name DISM -ListAvailable) {
    Import-Module -Name DISM
} else {
    # Server 2008 R2 doesn't have the DISM module installed on the path, check the Windows ADK path
    $adk_root = [System.Environment]::ExpandEnvironmentVariables("%PROGRAMFILES(X86)%\Windows Kits\*\Assessment and Deployment Kit\Deployment Tools\amd64\DISM")
    if (Test-Path -Path $adk_root) {
        Import-Module -Name (Get-Item -Path $adk_root).FullName
    } else {
        Fail-Json $result "The DISM PS module needs to be installed, this can be done through the windows-adk chocolately package"
    }
}


Function Extract-MSU($msu) {
    $temp_path = [IO.Path]::GetTempPath()
    $temp_foldername = [Guid]::NewGuid()
    $output_path = Join-Path -Path $temp_path -ChildPath $temp_foldername
    New-Item -Path $output_path -ItemType Directory | Out-Null

    $expand_args = @($msu, $output_path, "-F:*")

    try {
        &expand.exe $expand_args | Out-NUll
    } catch {
        Fail-Json $result "failed to run expand.exe $($expand_args): $($_.Exception.Message)"
    }
    if ($LASTEXITCODE -ne 0) {
        Fail-Json $result "failed to run expand.exe $($expand_args): RC = $LASTEXITCODE"
    }
    
    return $output_path
}

Function Get-HotfixMetadataFromName($name) {
    try {
        $dism_package_info = Get-WindowsPackage -Online -PackageName $name
    } catch {
        # build a basic stub for a missing result
        $dism_package_info = @{
            PackageState = "NotPresent"
            Description = ""
            PackageName = $name
        }
    }

    if ($dism_package_info.Description -match "(KB\d*)") {
        $hotfix_kb = $Matches[0]
    } else {
        $hotfix_kb = "UNKNOWN"
    }

    $metadata = @{
        name = $dism_package_info.PackageName
        state = $dism_package_info.PackageState
        kb = $hotfix_kb
    }

    return $metadata
}

Function Get-HotfixMetadataFromFile($extract_path) {
    # MSU contents https://support.microsoft.com/en-us/help/934307/description-of-the-windows-update-standalone-installer-in-windows
    $metadata_path = Get-ChildItem -Path $extract_path | Where-Object { $_.Extension -eq ".xml" }
    if ($metadata_path -eq $null) {
        Fail-Json $result "failed to get metadata xml inside MSU file, cannot get hotfix metadata required for this task"
    }
    [xml]$xml = Get-Content -Path $metadata_path.FullName
    
    $cab_source_filename = $xml.unattend.servicing.package.source.GetAttribute("location")
    $cab_source_filename = Split-Path -Path $cab_source_filename -Leaf
    $cab_file = Join-Path -Path $extract_path -ChildPath $cab_source_filename

    try {
        $dism_package_info = Get-WindowsPackage -Online -PackagePath $cab_file
    } catch {
        Fail-Json $result "failed to get DISM package metadata from path $($extract_path): $($_.Exception.Message)"
    }
    if ($dism_package_info.Applicable -eq $false) {
        Fail-Json $result "hotfix package is not applicable for this server"
    }

    $package_properties_path = Get-ChildItem -Path $extract_path | Where-Object { $_.Extension -eq ".txt" }
    if ($package_properties_path -eq $null) {
        $hotfix_kb = "UNKNOWN"
    } else {
        $package_ini = Get-Content -Path $package_properties_path.FullName
        $entry = $package_ini | Where-Object { $_.StartsWith("KB Article Number") }
        if ($entry -eq $null) {
            $hotfix_kb = "UNKNOWN"
        } else {
            $hotfix_kb = ($entry -split '=')[-1]
            $hotfix_kb = "KB$($hotfix_kb.Substring(1, $hotfix_kb.Length - 2))"
        }
    }

    $metadata = @{
        path = $cab_file
        name = $dism_package_info.PackageName
        state = $dism_package_info.PackageState
        kb = $hotfix_kb
    }

    return $metadata
}

Function Get-HotfixMetadataFromKB($kb) {
    # I really hate doing it this way
    $packages = Get-WindowsPackage -Online
    $identifier = $packages | Where-Object { $_.PackageName -like "*$kb*" }

    if ($identifier -eq $null) {
        # still haven't found the KB, need to loop through the results and check the description
        foreach ($package in $packages) {
            $raw_metadata = Get-HotfixMetadataFromName -name $package.PackageName
            if ($raw_metadata.kb -eq $kb) {
                $identifier = $raw_metadata
                break
            }
        }

        # if we still haven't found the package then we need to throw an error
        if ($metadata -eq $null) {
            Fail-Json $result "failed to get DISM package from KB, to continue specify hotfix_identifier instead"
        }
    } else {
        $metadata = Get-HotfixMetadataFromName -name $identifier.PackageName
    }

    return $metadata
}

if ($state -eq "absent") {
    # uninstall hotfix
    # this is a pretty poor way of doing this, is there a better way?

    if ($hotfix_identifier -ne $null) {
        $hotfix_metadata = Get-HotfixMetadataFromName -name $hotfix_identifier
    } elseif ($hotfix_kb -ne $null) {
        $hotfix_install_info = Get-Hotfix -Id $hotfix_kb -ErrorAction SilentlyContinue
        if ($hotfix_install_info -ne $null) {
            $hotfix_metadata = Get-HotfixMetadataFromKB -kb $hotfix_kb
        } else {
            $hotfix_metadata = @{state = "NotPresent"}
        }
    } else {
        Fail-Json $result "either hotfix_identifier or hotfix_kb needs to be set when state=absent"
    }

    # how do we want to deal with the other states?
    if ($hotfix_metadata.state -eq "UninstallPending") {
        $result.identifier = $hotfix_metadata.name
        $result.kb = $hotfix_metadata.kb
        $result.reboot_required = $true
    } elseif ($hotfix_metadata.state -eq "Installed") {
        $result.identifier = $hotfix_metadata.name
        $result.kb = $hotfix_metadata.kb

        if (-not $check_mode) {
            try {
                $remove_result = Remove-WindowsPackage -Online -PackageName $hotfix_metadata.name -NoRestart
            } catch {
                Fail-Json $result "failed to remove package $($hotfix_metadata.name): $($_.Exception.Message)"
            }
            $result.reboot_required = $remove_Result.RestartNeeded
        }
        
        $result.changed = $true
    }    
} else {
    if ($source -eq $null) {
        Fail-Json $result "source must be set when state=present"
    }
    if (-not (Test-Path -Path $source -PathType Leaf)) {
        Fail-Json $result "the path set for source $source does not exist or is not a file"
    }

    # while we do extract the file in check mode we need to do so for valid checking
    $extract_path = Extract-MSU -msu $source
    try {
        $hotfix_metadata = Get-HotfixMetadataFromFile -extract_path $extract_path

        # validate the hotfix matches if the hotfix id has been passed in
        if ($hotfix_identifier -ne $null) {
            if ($hotfix_metadata.name -ne $hotfix_identifier) {
                Fail-Json $result "the hotfix identifier $hotfix_identifier does not match with the source msu identifier $($hotfix_metadata.name), please omit or specify the correct identifier to continue"
            }
        }
        if ($hotfix_kb -ne $null) {
            if ($hotfix_metadata.kb -ne $hotfix_kb) {
                Fail-Json $result "the hotfix KB $hotfix_kb does not match with the source msu KB $($hotfix_metadata.kb), please omit or specify the correct KB to continue"
            }
        }

        $result.identifier = $hotfix_metadata.name
        $result.kb = $hotfix_metadata.kb

        # how do we want to deal with other states
        if ($hotfix_metadata.state -eq "InstallPending") {
            # return the reboot required flag, should we fail here instead
            $result.reboot_required = $true
        } elseif ($hotfix_metadata.state -ne "Installed") {
            if (-not $check_mode) {
                try {
                    $install_result = Add-WindowsPackage -Online -PackagePath $hotfix_metadata.path -NoRestart
                } catch {
                    Fail-Json $result "failed to add windows package from path $($hotfix_metadata.path): $($_.Exception.Message)"
                }
                $result.reboot_required = $install_result.RestartNeeded
            }
            $result.changed = $true
        }
    } finally {
        Remove-Item -Path $extract_path -Force -Recurse
    }
}

Exit-Json $result
