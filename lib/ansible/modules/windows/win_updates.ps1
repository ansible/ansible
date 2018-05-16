#!powershell
# This file is part of Ansible

# Copyright 2015, Matt Davis <mdavis@rolpdog.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

<# Most of the Windows Update API will not run under a remote token, which a
remote WinRM session always has. We set the below AnsibleRequires flag to
require become being used when executing the module to bypass this restriction.
This means we don't have to mess around with scheduled tasks. #>

#AnsibleRequires -Become

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$category_names = Get-AnsibleParam -obj $params -name "category_names" -type "list" -default @("CriticalUpdates", "SecurityUpdates", "UpdateRollups")
$log_path = Get-AnsibleParam -obj $params -name "log_path" -type "path"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "installed" -validateset "installed", "searched"
$blacklist = Get-AnsibleParam -obj $params -name "blacklist" -type "list"
$whitelist = Get-AnsibleParam -obj $params -name "whitelist" -type "list"

$result = @{
    changed = $false
    updates = @{}
    filtered_updates = @{}
}

Function Write-DebugLog($msg) {
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug -Message $msg
    if ($log_path -ne $null -and (-not $check_mode)) {
        Add-Content -Path $log_path -Value $msg
    }
}

Function Get-CategoryGuid($category_name) {
    $guid = switch -exact ($category_name) {
        "Application" {"5C9376AB-8CE6-464A-B136-22113DD69801"}
        "Connectors" {"434DE588-ED14-48F5-8EED-A15E09A991F6"}
        "CriticalUpdates" {"E6CF1350-C01B-414D-A61F-263D14D133B4"}
        "DefinitionUpdates" {"E0789628-CE08-4437-BE74-2495B842F43B"}
        "DeveloperKits" {"E140075D-8433-45C3-AD87-E72345B36078"}
        "FeaturePacks" {"B54E7D24-7ADD-428F-8B75-90A396FA584F"}
        "Guidance" {"9511D615-35B2-47BB-927F-F73D8E9260BB"}
        "SecurityUpdates" {"0FA1201D-4330-4FA8-8AE9-B877473B6441"}
        "ServicePacks" {"68C5B0A3-D1A6-4553-AE49-01D3A7827828"}
        "Tools" {"B4832BD8-E735-4761-8DAF-37F882276DAB"}
        "UpdateRollups" {"28BC880E-0592-4CBF-8F95-C79B17911D5F"}
        "Updates" {"CD5FFD1E-E932-4E3A-BF74-18BF0B1BBD83"}
        default { Fail-Json -obj $result -message "Unknown category_name $category_name, must be one of (Application,Connectors,CriticalUpdates,DefinitionUpdates,DeveloperKits,FeaturePacks,Guidance,SecurityUpdates,ServicePacks,Tools,UpdateRollups,Updates)" }
    }
    return $guid
}

Function Get-RebootStatus() {
    try {
        $system_info = New-Object -ComObject Microsoft.Update.SystemInfo
    } catch {
        Fail-Json -obj $result -message "Failed to create Microsoft.Update.SystemInfo COM object for reboot status: $($_.Exception.Message)"
    }

    return $system_info.RebootRequired
}

$category_guids = $category_names | ForEach-Object { Get-CategoryGuid -category_name $_ }

Write-DebugLog -msg "Creating Windows Update session..."
try {
    $session = New-Object -ComObject Microsoft.Update.Session
} catch {
    Fail-Json -obj $result -message "Failed to create Microsoft.Update.Session COM object: $($_.Exception.Message)"
}

Write-DebugLog -msg "Create Windows Update searcher..."
try {
    $searcher = $session.CreateUpdateSearcher()
} catch {
    Fail-Json -obj $result -message "Failed to create Windows Update search from session: $($_.Exception.Message)"
}

# OR is only allowed at the top-level, so we have to repeat base criteria inside
# FUTURE: change this to client-side filtered?
$criteria_base = "IsInstalled = 0"
$criteria_list = $category_guids | ForEach-Object { "($criteria_base AND CategoryIds contains '$_') " }
$criteria = [string]::Join(" OR", $criteria_list)
Write-DebugLog -msg "Search criteria: $criteria"

Write-DebugLog -msg "Searching for updates to install in category Ids $category_guids..."
try {
    $search_result = $searcher.Search($criteria)
} catch {
    Fail-Json -obj $result -message "Failed to search for updates with criteria '$criteria': $($_.Exception.Message)"
}
Write-DebugLog -msg "Found $($search_result.Updates.Count) updates"

Write-DebugLog -msg "Creating update collection..."
try {
    $updates_to_install = New-Object -ComObject Microsoft.Update.UpdateColl
} catch {
    Fail-Json -obj $result -message "Failed to create update collection object: $($_.Exception.Message)"
}

foreach ($update in $search_result.Updates) {
    $update_info = @{
        title = $update.Title
        # TODO: pluck the first KB out (since most have just one)?
        kb = $update.KBArticleIDs
        id = $update.Identity.UpdateId
        installed = $false
    }

    # validate update again blacklist/whitelist
    $skipped = $false
    $whitelist_match = $false
    foreach ($whitelist_entry in $whitelist) {
        if ($update_info.title -imatch $whitelist_entry) {
            $whitelist_match = $true
            break
        }
        foreach ($kb in $update_info.kb) {
            if ("KB$kb" -imatch $whitelist_entry) {
                $whitelist_match = $true
                break
            }
        }
    }
    if ($whitelist.Length -gt 0 -and -not $whitelist_match) {
        Write-DebugLog -msg "Skipping update $($update_info.id) - $($update_info.title) as it was not found in the whitelist"
        $skipped = $true
    }

    foreach ($blacklist_entry in $blacklist) {
        $kb_match = $false
        foreach ($kb in $update_info.kb) {
            if ("KB$kb" -imatch $blacklist_entry) {
                $kb_match = $true
            }
        }
        if ($kb_match -or $update_info.title -imatch $blacklist_entry) {
            Write-DebugLog -msg "Skipping update $($update_info.id) - $($update_info.title) as it was found in the blacklist"
            $skipped = $true
            break
        }
    }
    if ($skipped) {
        $result.filtered_updates[$update_info.id] = $update_info
        continue
    }


    if (-not $update.EulaAccepted) {
        Write-DebugLog -msg "Accepting EULA for $($update_info.id)"
        try {
            $update.AcceptEula()
        } catch {
            Fail-Json -obj $result -message "Failed to accept EULA for update $($update_info.id) - $($update_info.title)"
        }
    }

    if ($update.IsHidden) {
        Write-DebugLog -msg "Skipping hidden update $($update_info.title)"
        continue
    }

    Write-DebugLog -msg "Adding update $($update_info.id) - $($update_info.title)"
    $updates_to_install.Add($update) > $null

    $result.updates[$update_info.id] = $update_info
}

Write-DebugLog -msg "Calculating pre-install reboot requirement..."

# calculate this early for check mode, and to see if we should allow updates to continue
$result.reboot_required = Get-RebootStatus
$result.found_update_count = $updates_to_install.Count
$result.installed_update_count = 0

# Early exit of check mode/state=searched as it cannot do more after this
if ($check_mode -or $state -eq "searched") {
    Write-DebugLog -msg "Check mode: exiting..."
    Write-DebugLog -msg "Return value:`r`n$(ConvertTo-Json -InputObject $result -Depth 99)"

    if ($updates_to_install.Count -gt 0 -and ($state -ne "searched")) {
        $result.changed = $true
    }
    Exit-Json -obj $result
}

if ($updates_to_install.Count -gt 0) {
    if ($result.reboot_required) {
        Write-DebugLog -msg "FATAL: A reboot is required before more updates can be installed"
        Fail-Json -obj $result -message "A reboot is required before more updates can be installed"
    }
    Write-DebugLog -msg "No reboot is pending..."    
} else {
    # no updates to install exit here
    Exit-Json -obj $result
}

Write-DebugLog -msg "Downloading updates..."
$update_index = 1
foreach ($update in $updates_to_install) {
    $update_number = "($update_index of $($updates_to_install.Count))"
    if ($update.IsDownloaded) {
        Write-DebugLog -msg "Update $update_number $($update.Identity.UpdateId) already downloaded, skipping..."
        $update_index++
        continue
    }

    Write-DebugLog -msg "Creating downloader object..."
    try {
        $dl = $session.CreateUpdateDownloader()
    } catch {
        Fail-Json -obj $result -message "Failed to create downloader object: $($_.Exception.Message)"
    }

    Write-DebugLog -msg "Creating download collection..."
    try {
        $dl.Updates = New-Object -ComObject Microsoft.Update.UpdateColl
    } catch {
        Fail-Json -obj $result -message "Failed to create download collection object: $($_.Exception.Message)"
    }

    Write-DebugLog -msg "Adding update $update_number $($update.Identity.UpdateId)"
    $dl.Updates.Add($update) > $null

    Write-DebugLog -msg "Downloading $update_number $($update.Identity.UpdateId)"
    try {
        $download_result = $dl.Download()
    } catch {
        Fail-Json -obj $result -message "Failed to download update $update_number $($update.Identity.UpdateId) - $($update.Title): $($_.Exception.Message)"
    }
    
    Write-DebugLog -msg "Download result code for $update_number $($update.Identity.UpdateId) = $($download_result.ResultCode)"
    # FUTURE: configurable download retry
    if ($download_result.ResultCode -ne 2) { # OperationResultCode orcSucceeded
        Fail-Json -obj $result -message "Failed to download update $update_number $($update.Identity.UpdateId) - $($update.Title): Download Result $($download_result.ResultCode)"
    }

    $result.changed = $true
    $update_index++
}

Write-DebugLog -msg "Installing updates..."

# install as a batch so the reboot manager will suppress intermediate reboots
Write-DebugLog -msg "Creating installer object..."
try {
    $installer = $session.CreateUpdateInstaller()
} catch {
    Fail-Json -obj $result -message "Failed to create Update Installer object: $($_.Exception.Message)"
}

Write-DebugLog -msg "Creating install collection..."
try {
    $installer.Updates = New-Object -ComObject Microsoft.Update.UpdateColl
} catch {
    Fail-Json -obj $result -message "Failed to create Update Collection object: $($_.Exception.Message)"
}

foreach ($update in $updates_to_install) {
    Write-DebugLog -msg "Adding update $($update.Identity.UpdateID)"
    $installer.Updates.Add($update) > $null
}

# FUTURE: use BeginInstall w/ progress reporting so we can at least log intermediate install results
try {
    $install_result = $installer.Install()
} catch {
    Fail-Json -obj $result -message "Failed to install update from Update Collection: $($_.Exception.Message)"
}

$update_success_count = 0
$update_fail_count = 0

# WU result API requires us to index in to get the install results
$update_index = 0
foreach ($update in $updates_to_install) {
    $update_number = "($($update_index + 1) of $($updates_to_install.Count))"
    try {
        $update_result = $install_result.GetUpdateResult($update_index)
    } catch {
        Fail-Json -obj $result -message "Failed to get update result for update $update_number $($update.Identity.UpdateID) - $($update.Title): $($_.Exception.Message)"
    }
    $update_resultcode = $update_result.ResultCode
    $update_hresult = $update_result.HResult

    $update_index++

    $update_dict = $result.updates[$update.Identity.UpdateID]
    if ($update_resultcode -eq 2) { # OperationResultCode orcSucceeded
        $update_success_count++
        $update_dict.installed = $true
        Write-DebugLog -msg "Update $update_number $($update.Identity.UpdateID) succeeded"
    } else {
        $update_fail_count++
        $update_dict.installed = $false
        $update_dict.failed = $true
        $update_dict.failure_hresult_code = $update_hresult
        Write-DebugLog -msg "Update $update_number $($update.Identity.UpdateID) failed, resultcode: $update_resultcode, hresult: $update_hresult"
    }
}

Write-DebugLog -msg "Performing post-install reboot requirement check..."
$result.reboot_required = Get-RebootStatus
$result.installed_update_count = $update_success_count
$result.failed_update_count = $update_fail_count

if ($update_fail_count -gt 0) {
    Fail-Json -obj $result -msg "Failed to install one or more updates"
}

Write-DebugLog -msg "Return value:`r`n$(ConvertTo-Json -InputObject $result -Depth 99)"

Exit-Json $result

