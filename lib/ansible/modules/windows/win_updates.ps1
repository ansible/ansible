#!powershell

# Copyright: (c) 2015, Matt Davis <mdavis@rolpdog.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$category_names = Get-AnsibleParam -obj $params -name "category_names" -type "list" -default @("CriticalUpdates", "SecurityUpdates", "UpdateRollups")
$log_path = Get-AnsibleParam -obj $params -name "log_path" -type "path"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "installed" -validateset "installed", "searched", "downloaded"
$blacklist = Get-AnsibleParam -obj $params -name "blacklist" -type "list"
$whitelist = Get-AnsibleParam -obj $params -name "whitelist" -type "list"
$server_selection = Get-AnsibleParam -obj $params -name "server_selection" -type "string" -default "default" -validateset "default", "managed_server", "windows_update"

# For backwards compatibility
Function Get-CategoryMapping ($category_name) {
    switch -exact ($category_name) {
        "CriticalUpdates"   {return "Critical Updates"}
        "DefinitionUpdates" {return "Definition Updates"}
        "DeveloperKits"     {return "Developer Kits"}
        "FeaturePacks"      {return "Feature Packs"}
        "SecurityUpdates"   {return "Security Updates"}
        "ServicePacks"      {return "Service Packs"}
        "UpdateRollups"     {return "Update Rollups"}
        default             {return $category_name}
    }
}

$category_names = $category_names | ForEach-Object { Get-CategoryMapping -category_name $_ }

$common_functions = {
    Function Write-DebugLog($msg) {
        $date_str = Get-Date -Format u
        $msg = "$date_str $msg"

        Write-Debug -Message $msg
        if ($null -ne $log_path -and (-not $check_mode)) {
            Add-Content -Path $log_path -Value $msg
        }
    }
}

$update_script_block = {
    Param(
        [hashtable]$arguments
    )

    $ErrorActionPreference = "Stop"
    $DebugPreference = "Continue"

    Function Start-Updates {
        Param(
            $category_names,
            $log_path,
            $state,
            $blacklist,
            $whitelist,
            $server_selection
        )

        $result = @{
            changed = $false
            updates = @{}
            filtered_updates = @{}
        }

        Write-DebugLog -msg "Creating Windows Update session..."
        try {
            $session = New-Object -ComObject Microsoft.Update.Session
        } catch {
            $result.failed = $true
            $result.msg = "Failed to create Microsoft.Update.Session COM object: $($_.Exception.Message)"
            return $result
        }

        Write-DebugLog -msg "Create Windows Update searcher..."
        try {
            $searcher = $session.CreateUpdateSearcher()
        } catch {
            $result.failed = $true
            $result.msg = "Failed to create Windows Update search from session: $($_.Exception.Message)"
            return $result
        }

        Write-DebugLog -msg "Setting the Windows Update Agent source catalog..."
        Write-DebugLog -msg "Requested search source is '$($server_selection)'"
        try {
            $server_selection_value = switch ($server_selection) {
                "default" { 0 ; break }
                "managed_server" { 1 ; break }
                "windows_update" { 2 ; break }
            }
            $searcher.serverselection = $server_selection_value
            Write-DebugLog -msg "Search source set to '$($server_selection)' (ServerSelection = $($server_selection_value))"
        }
        catch {
            $result.failed = $true
            $result.msg = "Failed to set Windows Update Agent search source: $($_.Exception.Message)"
            return $result
        }

        Write-DebugLog -msg "Searching for updates to install"
        try {
            $search_result = $searcher.Search("IsInstalled = 0")
        } catch {
            $result.failed = $true
            $result.msg = "Failed to search for updates: $($_.Exception.Message)"
            return $result
        }
        Write-DebugLog -msg "Found $($search_result.Updates.Count) updates"

        Write-DebugLog -msg "Creating update collection..."
        try {
            $updates_to_install = New-Object -ComObject Microsoft.Update.UpdateColl
        } catch {
            $result.failed = $true
            $result.msg = "Failed to create update collection object: $($_.Exception.Message)"
            return $result
        }

        foreach ($update in $search_result.Updates) {
            $update_info = @{
                title = $update.Title
                # TODO: pluck the first KB out (since most have just one)?
                kb = $update.KBArticleIDs
                id = $update.Identity.UpdateId
                installed = $false
                categories = @($update.Categories | ForEach-Object { $_.Name })
            }

            # validate update again blacklist/whitelist/post_category_names/hidden
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
                $update_info.filtered_reason = "whitelist"
                $result.filtered_updates[$update_info.id] = $update_info
                continue
            }

            $blacklist_match = $false
            foreach ($blacklist_entry in $blacklist) {
                if ($update_info.title -imatch $blacklist_entry) {
                    $blacklist_match = $true
                    break
                }
                foreach ($kb in $update_info.kb) {
                    if ("KB$kb" -imatch $blacklist_entry) {
                        $blacklist_match = $true
                        break
                    }
                }
            }
            if ($blacklist_match) {
                Write-DebugLog -msg "Skipping update $($update_info.id) - $($update_info.title) as it was found in the blacklist"
                $update_info.filtered_reason = "blacklist"
                $result.filtered_updates[$update_info.id] = $update_info
                continue
            }

            if ($update.IsHidden) {
                Write-DebugLog -msg "Skipping update $($update_info.title) as it was hidden"
                $update_info.filtered_reason = "skip_hidden"
                $result.filtered_updates[$update_info.id] = $update_info
                continue
            }

            $category_match = $false
            foreach ($match_cat in $category_names) {
                if ($update_info.categories -ieq $match_cat) {
                    $category_match = $true
                    break
                }
            }
            if ($category_names.Length -gt 0 -and -not $category_match) {
                Write-DebugLog -msg "Skipping update $($update_info.id) - $($update_info.title) as it was not found in the category names filter"
                $update_info.filtered_reason = "category_names"
                $result.filtered_updates[$update_info.id] = $update_info
                continue
            }

            if (-not $update.EulaAccepted) {
                Write-DebugLog -msg "Accepting EULA for $($update_info.id)"
                try {
                    $update.AcceptEula()
                } catch {
                    $result.failed = $true
                    $result.msg = "Failed to accept EULA for update $($update_info.id) - $($update_info.title)"
                    return $result
                }
            }

            Write-DebugLog -msg "Adding update $($update_info.id) - $($update_info.title)"
            $updates_to_install.Add($update) > $null

            $result.updates[$update_info.id] = $update_info
        }

        Write-DebugLog -msg "Calculating pre-install reboot requirement..."

        # calculate this early for check mode, and to see if we should allow updates to continue
        $result.reboot_required = (New-Object -ComObject Microsoft.Update.SystemInfo).RebootRequired
        $result.found_update_count = $updates_to_install.Count
        $result.installed_update_count = 0

        # Early exit of check mode/state=searched as it cannot do more after this
        if ($check_mode -or $state -eq "searched") {
            Write-DebugLog -msg "Check mode: exiting..."
            Write-DebugLog -msg "Return value:`r`n$(ConvertTo-Json -InputObject $result -Depth 99)"

            if ($updates_to_install.Count -gt 0 -and ($state -ne "searched")) {
                $result.changed = $true
            }
            return $result
        }

        if ($updates_to_install.Count -gt 0) {
            if ($result.reboot_required) {
                Write-DebugLog -msg "FATAL: A reboot is required before more updates can be installed"
                $result.failed = $true
                $result.msg = "A reboot is required before more updates can be installed"
                return $result
            }
            Write-DebugLog -msg "No reboot is pending..."
        } else {
            # no updates to install exit here
            return $result
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
                $result.failed = $true
                $result.msg = "Failed to create downloader object: $($_.Exception.Message)"
                return $result
            }

            Write-DebugLog -msg "Creating download collection..."
            try {
                $dl.Updates = New-Object -ComObject Microsoft.Update.UpdateColl
            } catch {
                $result.failed = $true
                $result.msg = "Failed to create download collection object: $($_.Exception.Message)"
                return $result
            }

            Write-DebugLog -msg "Adding update $update_number $($update.Identity.UpdateId)"
            $dl.Updates.Add($update) > $null

            Write-DebugLog -msg "Downloading $update_number $($update.Identity.UpdateId)"
            try {
                $download_result = $dl.Download()
            } catch {
                $result.failed = $true
                $result.msg = "Failed to download update $update_number $($update.Identity.UpdateId) - $($update.Title): $($_.Exception.Message)"
                return $result
            }

            Write-DebugLog -msg "Download result code for $update_number $($update.Identity.UpdateId) = $($download_result.ResultCode)"
            # FUTURE: configurable download retry
            if ($download_result.ResultCode -ne 2) { # OperationResultCode orcSucceeded
                $result.failed = $true
                $result.msg = "Failed to download update $update_number $($update.Identity.UpdateId) - $($update.Title): Download Result $($download_result.ResultCode)"
                return $result
            }

            $result.changed = $true
            $update_index++
        }

        # Early exit for download-only
        if ($state -eq "downloaded") {
            Write-DebugLog -msg "Downloaded $($updates_to_install.Count) updates..."
            $result.failed = $false
            $result.msg = "Downloaded $($updates_to_install.Count) updates"
            return $result
        }

        Write-DebugLog -msg "Installing updates..."
        # install as a batch so the reboot manager will suppress intermediate reboots

        Write-DebugLog -msg "Creating installer object..."
        try {
            $installer = $session.CreateUpdateInstaller()
        } catch {
            $result.failed = $true
            $result.msg = "Failed to create Update Installer object: $($_.Exception.Message)"
            return $result
        }

        Write-DebugLog -msg "Creating install collection..."
        try {
            $installer.Updates = New-Object -ComObject Microsoft.Update.UpdateColl
        } catch {
            $result.failed = $true
            $result.msg = "Failed to create Update Collection object: $($_.Exception.Message)"
            return $result
        }

        foreach ($update in $updates_to_install) {
            Write-DebugLog -msg "Adding update $($update.Identity.UpdateID)"
            $installer.Updates.Add($update) > $null
        }

        # FUTURE: use BeginInstall w/ progress reporting so we can at least log intermediate install results
        try {
            $install_result = $installer.Install()
        } catch {
            $result.failed = $true
            $result.msg = "Failed to install update from Update Collection: $($_.Exception.Message)"
            return $result
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
                $result.failed = $true
                $result.msg = "Failed to get update result for update $update_number $($update.Identity.UpdateID) - $($update.Title): $($_.Exception.Message)"
                return $result
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
        $result.reboot_required = (New-Object -ComObject Microsoft.Update.SystemInfo).RebootRequired
        $result.installed_update_count = $update_success_count
        $result.failed_update_count = $update_fail_count

        if ($updates_success_count -gt 0) {
            $result.changed = $true
        }

        if ($update_fail_count -gt 0) {
            $result.failed = $true
            $result.msg = "Failed to install one or more updates"
            return $result
        }

        Write-DebugLog -msg "Return value:`r`n$(ConvertTo-Json -InputObject $result -Depth 99)"

        return $result
    }

    $check_mode = $arguments.check_mode
    try {
        return @{
            job_output = Start-Updates @arguments
        }
    } catch {
        Write-DebugLog -msg "Fatal exception: $($_.Exception.Message) at $($_.ScriptStackTrace)"
        return @{
            job_output = @{
                failed = $true
                msg = $_.Exception.Message
                location = $_.ScriptStackTrace
            }
        }
    }
}

Function Start-Natively($common_functions, $script) {
    $runspace_pool = [RunspaceFactory]::CreateRunspacePool()
    $runspace_pool.Open()

    try {
        $ps_pipeline = [PowerShell]::Create()
        $ps_pipeline.RunspacePool = $runspace_pool

        # add the common script functions
        $ps_pipeline.AddScript($common_functions) > $null

        # add the update script block and required parameters
        $ps_pipeline.AddStatement().AddScript($script) > $null
        $ps_pipeline.AddParameter("arguments", @{
            category_names = $category_names
            log_path = $log_path
            state = $state
            blacklist = $blacklist
            whitelist = $whitelist
            check_mode = $check_mode
            server_selection = $server_selection
        }) > $null

        $output = $ps_pipeline.Invoke()
    } finally {
        $runspace_pool.Close()
    }

    $result = $output[0].job_output
    if ($ps_pipeline.HadErrors) {
        $result.failed = $true

        # if the msg wasn't set, then add a generic error to at least tell the user something
        if (-not ($result.ContainsKey("msg"))) {
            $result.msg = "Unknown failure when executing native update script block"
            $result.errors = $ps_pipeline.Streams.Error
        }
    }

    Write-DebugLog -msg "Native job completed with output: $($result | Out-String -Width 300)"

    return ,$result
}

Function Remove-ScheduledJob($name) {
    $scheduled_job = Get-ScheduledJob -Name $name -ErrorAction SilentlyContinue

    if ($null -ne $scheduled_job) {
        Write-DebugLog -msg "Scheduled Job $name exists, ensuring it is not running..."
        $scheduler = New-Object -ComObject Schedule.Service
        Write-DebugLog -msg "Connecting to scheduler service..."
        $scheduler.Connect()
        Write-DebugLog -msg "Getting running tasks named $name"
        $running_tasks = @($scheduler.GetRunningTasks(0) | Where-Object { $_.Name -eq $name })

        foreach ($task_to_stop in $running_tasks) {
            Write-DebugLog -msg "Stopping running task $($task_to_stop.InstanceGuid)..."
            $task_to_stop.Stop()
        }

        <# FUTURE: add a global waithandle for this to release any other waiters. Wait-Job
        and/or polling will block forever, since the killed job object in the parent
        session doesn't know it's been killed :( #>
        Unregister-ScheduledJob -Name $name
    }
}

Function Start-AsScheduledTask($common_functions, $script) {
    $job_name = "ansible-win-updates"
    Remove-ScheduledJob -name $job_name

    $job_args = @{
        ScriptBlock = $script
        Name = $job_name
        ArgumentList = @(
            @{
                category_names = $category_names
                log_path = $log_path
                state = $state
                blacklist = $blacklist
                whitelist = $whitelist
                check_mode = $check_mode
                server_selection = $server_selection
            }
        )
        ErrorAction = "Stop"
        ScheduledJobOption = @{ RunElevated=$True; StartIfOnBatteries=$True; StopIfGoingOnBatteries=$False }
        InitializationScript = $common_functions
    }

    Write-DebugLog -msg "Registering scheduled job with args $($job_args | Out-String -Width 300)"
    $scheduled_job = Register-ScheduledJob @job_args

    # RunAsTask isn't available in PS3 - fall back to a 2s future trigger
    if ($scheduled_job | Get-Member -Name RunAsTask) {
        Write-DebugLog -msg "Starting scheduled job (PS4+ method)"
        $scheduled_job.RunAsTask()
    } else {
        Write-DebugLog -msg "Starting scheduled job (PS3 method)"
        Add-JobTrigger -InputObject $scheduled_job -trigger $(New-JobTrigger -Once -At $(Get-Date).AddSeconds(2))
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $job = $null

    Write-DebugLog -msg "Waiting for job completion..."

    # Wait-Job can fail for a few seconds until the scheduled task starts - poll for it...
    while ($null -eq $job) {
        Start-Sleep -Milliseconds 100
        if ($sw.ElapsedMilliseconds -ge 30000) { # tasks scheduled right after boot on 2008R2 can take awhile to start...
            Fail-Json -msg "Timed out waiting for scheduled task to start"
        }

        # FUTURE: configurable timeout so we don't block forever?
        # FUTURE: add a global WaitHandle in case another instance kills our job, so we don't block forever
        $job = Wait-Job -Name $scheduled_job.Name -ErrorAction SilentlyContinue
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # NB: output from scheduled jobs is delayed after completion (including the sub-objects after the primary Output object is available)
    while (($null -eq $job.Output -or -not ($job.Output | Get-Member -Name Key -ErrorAction Ignore) -or -not $job.Output.Key.Contains("job_output")) -and $sw.ElapsedMilliseconds -lt 15000) {
        Write-DebugLog -msg "Waiting for job output to populate..."
        Start-Sleep -Milliseconds 500
    }

    # NB: fallthru on both timeout and success
    $ret = @{
        ErrorOutput = $job.Error
        WarningOutput = $job.Warning
        VerboseOutput = $job.Verbose
        DebugOutput = $job.Debug
    }

    if ($null -eq $job.Output -or -not $job.Output.Keys.Contains('job_output')) {
        $ret.Output = @{failed = $true; msg = "job output was lost"}
    } else {
        $ret.Output = $job.Output.job_output # sub-object returned, can only be accessed as a property for some reason
    }

    try { # this shouldn't be fatal, but can fail with both Powershell errors and COM Exceptions, hence the dual error-handling...
        Unregister-ScheduledJob -Name $job_name -Force -ErrorAction Continue
    } catch {
        Write-DebugLog "Error unregistering job after execution: $($_.Exception.ToString()) $($_.ScriptStackTrace)"
    }
    Write-DebugLog -msg "Scheduled job completed with output: $($re.Output | Out-String -Width 300)"

    return $ret.Output
}

# source the common code into the current scope so we can call it
. $common_functions

<# Most of the Windows Update Agent API will not run under a remote token,
which a remote WinRM session always has. Using become can bypass this
limitation but it is not always an option with older hosts. win_updates checks
if WUA is available in the current logon process and does either of the below;

    * If become is used then it will run the windows update process natively
      without any of the scheduled task hackery
    * If become is not used then it will run the windows update process under
      a scheduled job.
#>
try {
    (New-Object -ComObject Microsoft.Update.Session).CreateUpdateInstaller().IsBusy > $null
    $wua_available = $true
} catch {
    $wua_available = $false
}

if ($wua_available) {
    Write-DebugLog -msg "WUA is available in current logon process, running natively"
    $result = Start-Natively -common_functions $common_functions -script $update_script_block
} else {
    Write-DebugLog -msg "WUA is not avialable in current logon process, running with scheduled task"
    $result = Start-AsScheduledTask -common_functions $common_functions -script $update_script_block
}

Exit-Json -obj $result
