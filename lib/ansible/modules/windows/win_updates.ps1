#!powershell
# This file is part of Ansible
#
# Copyright 2015, Matt Davis <mdavis@rolpdog.com>
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
$FormatEnumerationLimit = -1 # prevent out-string et al from truncating collection dumps

<# Most of the Windows Update Agent API will not run under a remote token,
which a remote WinRM session always has. win_updates uses the Task Scheduler
to run the bulk of the update functionality under a local token. Powershell's
Scheduled-Job capability provides a decent abstraction over the Task Scheduler
and handles marshaling Powershell args in and output/errors/etc back. The
module schedules a single job that executes all interactions with the Update
Agent API, then waits for completion. A significant amount of hassle is
involved to ensure that only one of these jobs is running at a time, and to
clean up the various error conditions that can occur. #>

# define the ScriptBlock that will be passed to Register-ScheduledJob
$job_body = {
    Param(
    [hashtable]$boundparms=@{},
    [Object[]]$unboundargs=$()
    )

    Set-StrictMode -Version 2

    $ErrorActionPreference = "Stop"
    $DebugPreference = "Continue"
    $FormatEnumerationLimit = -1 # prevent out-string et al from truncating collection dumps

    # set this as a global for the Write-DebugLog function
    $log_path = $boundparms['log_path']

    Write-DebugLog "Scheduled job started with boundparms $($boundparms | out-string) and unboundargs $($unboundargs | out-string)"

    # FUTURE: elevate this to module arg validation once we have it
    Function MapCategoryNameToGuid {
        Param([string] $category_name)

        $category_guid = switch -exact ($category_name) {
            # as documented by TechNet @ https://technet.microsoft.com/en-us/library/ff730937.aspx
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
            default { throw "Unknown category_name $category_name, must be one of (Application,Connectors,CriticalUpdates,DefinitionUpdates,DeveloperKits,FeaturePacks,Guidance,SecurityUpdates,ServicePacks,Tools,UpdateRollups,Updates)" }
        }

        return $category_guid
    }

    Function DoWindowsUpdate {
        Param(
        [string[]]$category_names=@("CriticalUpdates","SecurityUpdates","UpdateRollups"),
        [ValidateSet("installed", "searched")]
        [string]$state="installed",
        [bool]$_ansible_check_mode=$false
        )

        $is_check_mode = $($state -eq "searched") -or $_ansible_check_mode

        $category_guids = $category_names | % { MapCategoryNameToGUID $_ }

        $update_status = @{ changed = $false }

        Write-DebugLog "Creating Windows Update session..."
        $session = New-Object -ComObject Microsoft.Update.Session

        Write-DebugLog "Create Windows Update searcher..."
        $searcher = $session.CreateUpdateSearcher()

        # OR is only allowed at the top-level, so we have to repeat base criteria inside
        # FUTURE: change this to client-side filtered?
        $criteriabase = "IsInstalled = 0"
        $criteria_list = $category_guids | % { "($criteriabase AND CategoryIDs contains '$_')" }

        $criteria = [string]::Join(" OR ", $criteria_list)

        Write-DebugLog "Search criteria: $criteria"

        Write-DebugLog "Searching for updates to install in category IDs $category_guids..."
        $searchresult = $searcher.Search($criteria)

        Write-DebugLog "Creating update collection..."
    
        $updates_to_install = New-Object -ComObject Microsoft.Update.UpdateColl

        Write-DebugLog "Found $($searchresult.Updates.Count) updates"

        $update_status.updates = @{ }

        # FUTURE: add further filtering options
        foreach($update in $searchresult.Updates) {
          if(-Not $update.EulaAccepted) {
            Write-DebugLog "Accepting EULA for $($update.Identity.UpdateID)"
            $update.AcceptEula()
          }

          if($update.IsHidden) {
            Write-DebugLog "Skipping hidden update $($update.Title)"
            continue
          }

          Write-DebugLog "Adding update $($update.Identity.UpdateID) - $($update.Title)"
          $res = $updates_to_install.Add($update)

          $update_status.updates[$update.Identity.UpdateID] = @{
            title = $update.Title
            # TODO: pluck the first KB out (since most have just one)?
            kb = $update.KBArticleIDs
            id = $update.Identity.UpdateID
            installed = $false
          }
        }

        Write-DebugLog "Calculating pre-install reboot requirement..."

        # calculate this early for check mode, and to see if we should allow updates to continue
        $sysinfo = New-Object -ComObject Microsoft.Update.SystemInfo
        $update_status.reboot_required = $sysinfo.RebootRequired
        $update_status.found_update_count = $updates_to_install.Count
        $update_status.installed_update_count = 0

        # bail out here for check mode  
        if($is_check_mode -eq $true) { 
          Write-DebugLog "Check mode; exiting..."
          Write-DebugLog "Return value: $($update_status | out-string)"

          if($updates_to_install.Count -gt 0) { $update_status.changed = $true }
          return $update_status 
        }

        if($updates_to_install.Count -gt 0) {   
          if($update_status.reboot_required) { 
            throw "A reboot is required before more updates can be installed."
          }
          else {
            Write-DebugLog "No reboot is pending..."
          }
          Write-DebugLog "Downloading updates..." 
        }

        foreach($update in $updates_to_install) {
            if($update.IsDownloaded) { 
                Write-DebugLog "Update $($update.Identity.UpdateID) already downloaded, skipping..."
                continue 
            }
            Write-DebugLog "Creating downloader object..."
            $dl = $session.CreateUpdateDownloader()
            Write-DebugLog "Creating download collection..."
            $dl.Updates = New-Object -ComObject Microsoft.Update.UpdateColl
            Write-DebugLog "Adding update $($update.Identity.UpdateID)"
            $res = $dl.Updates.Add($update)
            Write-DebugLog "Downloading update $($update.Identity.UpdateID)..."
            $download_result = $dl.Download()
            # FUTURE: configurable download retry
            if($download_result.ResultCode -ne 2) { # OperationResultCode orcSucceeded
                throw "Failed to download update $($update.Identity.UpdateID)"
            }
        }

        if($updates_to_install.Count -lt 1 ) { return $update_status }

        Write-DebugLog "Installing updates..."

        # install as a batch so the reboot manager will suppress intermediate reboots
        Write-DebugLog "Creating installer object..."
        $inst = $session.CreateUpdateInstaller()
        Write-DebugLog "Creating install collection..."
        $inst.Updates = New-Object -ComObject Microsoft.Update.UpdateColl

        foreach($update in $updates_to_install) {
            Write-DebugLog "Adding update $($update.Identity.UpdateID)"
            $res = $inst.Updates.Add($update)
        }

        # FUTURE: use BeginInstall w/ progress reporting so we can at least log intermediate install results
        Write-DebugLog "Installing updates..."
        $install_result = $inst.Install()

        $update_success_count = 0
        $update_fail_count = 0

        # WU result API requires us to index in to get the install results
        $update_index = 0

        foreach($update in $updates_to_install) {
          $update_result = $install_result.GetUpdateResult($update_index)
          $update_resultcode = $update_result.ResultCode
          $update_hresult = $update_result.HResult

          $update_index++

          $update_dict = $update_status.updates[$update.Identity.UpdateID]

          if($update_resultcode -eq 2) { # OperationResultCode orcSucceeded
            $update_success_count++
            $update_dict.installed = $true
            Write-DebugLog "Update $($update.Identity.UpdateID) succeeded"
          }
          else {
            $update_fail_count++
            $update_dict.installed = $false
            $update_dict.failed = $true
            $update_dict.failure_hresult_code = $update_hresult
            Write-DebugLog "Update $($update.Identity.UpdateID) failed resultcode $update_hresult hresult $update_hresult"
          }

        }

        if($update_fail_count -gt 0) {  
            $update_status.failed = $true
            $update_status.msg="Failed to install one or more updates"
        }
        else { $update_status.changed = $true }

        Write-DebugLog "Performing post-install reboot requirement check..."

        # recalculate reboot status after installs
        $sysinfo = New-Object -ComObject Microsoft.Update.SystemInfo
        $update_status.reboot_required = $sysinfo.RebootRequired
        $update_status.installed_update_count = $update_success_count
        $update_status.failed_update_count = $update_fail_count

        Write-DebugLog "Return value: $($update_status | out-string)"

        return $update_status
    }

    Try { 
        # job system adds a bunch of cruft to top-level dict, so we have to send a sub-dict
        return @{ job_output = DoWindowsUpdate @boundparms }
    }
    Catch {
        $excep = $_
        Write-DebugLog "Fatal exception: $($excep.Exception.Message) at $($excep.ScriptStackTrace)"
        return @{ job_output = @{ failed=$true;error=$excep.Exception.Message;location=$excep.ScriptStackTrace } }
    }
}

Function DestroyScheduledJob {
  Param([string] $job_name)

  # find a scheduled job with the same name (should normally fail)
  $schedjob = Get-ScheduledJob -Name $job_name -ErrorAction SilentlyContinue

  # nuke it if it's there
  If($schedjob -ne $null) {  
      Write-DebugLog "ScheduledJob $job_name exists, ensuring it's not running..."
      # can't manage jobs across sessions, so we have to resort to the Task Scheduler script object to kill running jobs
      $schedserv = New-Object -ComObject Schedule.Service
      Write-DebugLog "Connecting to scheduler service..."
      $schedserv.Connect()
      Write-DebugLog "Getting running tasks named $job_name"
      $running_tasks = @($schedserv.GetRunningTasks(0) | Where-Object { $_.Name -eq $job_name })

      Foreach($task_to_stop in $running_tasks) {
          Write-DebugLog "Stopping running task $($task_to_stop.InstanceGuid)..."
          $task_to_stop.Stop()
      }

      <# FUTURE: add a global waithandle for this to release any other waiters. Wait-Job 
      and/or polling will block forever, since the killed job object in the parent 
      session doesn't know it's been killed :( #>

      Unregister-ScheduledJob -Name $job_name
  }

}

Function RunAsScheduledJob {
  Param([scriptblock] $job_body, [string] $job_name, [scriptblock] $job_init, [Object[]] $job_arg_list=@())

  DestroyScheduledJob -job_name $job_name

  $rsj_args = @{
    ScriptBlock = $job_body
    Name = $job_name
    ArgumentList = $job_arg_list
    ErrorAction = "Stop"
    ScheduledJobOption = @{ RunElevated=$True }
  }

  if($job_init) { $rsj_args.InitializationScript = $job_init }

  Write-DebugLog "Registering scheduled job with args $($rsj_args | Out-String -Width 300)"
  $schedjob = Register-ScheduledJob @rsj_args

  # RunAsTask isn't available in PS3- fall back to a 2s future trigger
  if($schedjob | Get-Member -Name RunAsTask) {
    Write-DebugLog "Starting scheduled job (PS4 method)"
    $schedjob.RunAsTask()
  }
  else {
    Write-DebugLog "Starting scheduled job (PS3 method)"
    Add-JobTrigger -inputobject $schedjob -trigger $(New-JobTrigger -once -at $(Get-Date).AddSeconds(2))      
  }

  $sw = [System.Diagnostics.Stopwatch]::StartNew()

  $job = $null

  Write-DebugLog "Waiting for job completion..."

  # Wait-Job can fail for a few seconds until the scheduled task starts- poll for it...
  while ($job -eq $null) {
      start-sleep -Milliseconds 100
      if($sw.ElapsedMilliseconds -ge 30000) { # tasks scheduled right after boot on 2008R2 can take awhile to start...
        Throw "Timed out waiting for scheduled task to start"
      }

      # FUTURE: configurable timeout so we don't block forever?
      # FUTURE: add a global WaitHandle in case another instance kills our job, so we don't block forever
      $job = Wait-Job -Name $schedjob.Name -ErrorAction SilentlyContinue 
  }

  $sw = [System.Diagnostics.Stopwatch]::StartNew()

  # NB: output from scheduled jobs is delayed after completion (including the sub-objects after the primary Output object is available)
  While (($job.Output -eq $null -or -not ($job.Output | Get-Member -Name Keys -ErrorAction Ignore) -or -not $job.Output.Keys.Contains('job_output')) -and $sw.ElapsedMilliseconds -lt 15000) {
    Write-DebugLog "Waiting for job output to populate..."
    Start-Sleep -Milliseconds 500
  }

  # NB: fallthru on both timeout and success

  $ret = @{
      ErrorOutput = $job.Error
      WarningOutput = $job.Warning
      VerboseOutput = $job.Verbose
      DebugOutput = $job.Debug
  }

  If ($job.Output -eq $null -or -not $job.Output.Keys.Contains('job_output')) {
      $ret.Output = @{failed = $true; msg = "job output was lost"}
  }
  Else {
      $ret.Output = $job.Output.job_output # sub-object returned, can only be accessed as a property for some reason
  }

  Try { # this shouldn't be fatal, but can fail with both Powershell errors and COM Exceptions, hence the dual error-handling... 
      Unregister-ScheduledJob -Name $job_name -Force -ErrorAction Continue
  }
  Catch {
      Write-DebugLog "Error unregistering job after execution: $($_.Exception.ToString()) $($_.ScriptStackTrace)"
  }

  return $ret
}

Function Log-Forensics {
    Write-DebugLog "Arguments: $job_args | out-string"
    Write-DebugLog "OS Version: $([environment]::OSVersion.Version | out-string)"
    Write-DebugLog "Running as user: $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    Write-DebugLog "Powershell version: $($PSVersionTable | out-string)"
    # FUTURE: log auth method (kerb, password, etc)
}

# code shared between the scheduled job and the host script
$common_inject = {
    # FUTURE: capture all to a list, dump on error
    Function Write-DebugLog {
        Param(
        [string]$msg
        )

        $DebugPreference = "Continue"
        $ErrorActionPreference = "Continue"
        $date_str = Get-Date -Format u
        $msg = "$date_str $msg"

        Write-Debug $msg

        if($log_path -ne $null) {
            Add-Content $log_path $msg
        }
    }
}

# source the common code into the current scope so we can call it
. $common_inject

$job_args = Parse-Args $args $true

# set the log_path for the global log function we injected earlier
$log_path = $job_args['log_path']

Log-Forensics

Write-DebugLog "Starting scheduled job with args: $($job_args | Out-String -Width 300)"

# pass the common code as job_init so it'll be injected into the scheduled job script
$sjo = RunAsScheduledJob -job_init $common_inject -job_body $job_body -job_name ansible-win-updates -job_arg_list $job_args

Write-DebugLog "Scheduled job completed with output: $($sjo.Output | Out-String -Width 300)"

Exit-Json $sjo.Output