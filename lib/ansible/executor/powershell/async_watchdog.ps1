# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Payload
)

# help with debugging errors as we don't have visibility of this running process
trap {
    $watchdog_path = "$($env:TEMP)\ansible-async-watchdog-error-$(Get-Date -Format "yyyy-MM-ddTHH-mm-ss.ffffZ").txt"
    $error_msg = "Error while running the async exec wrapper`r`n$(Format-AnsibleException -ErrorRecord $_)"
    Set-Content -Path $watchdog_path -Value $error_msg
    break
}

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting async_watchdog" "async_watchdog"

# pop 0th action as entrypoint
$payload.actions = $payload.actions[1..99]

$actions = $Payload.actions
$entrypoint = $payload.($actions[0])
$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))

$resultfile_path = $payload.async_results_path
$max_exec_time_sec = $payload.async_timeout_sec

Write-AnsibleLog "INFO - deserializing existing result file args at: '$resultfile_path'" "async_watchdog"
if (-not (Test-Path -Path $resultfile_path)) {
    $msg = "result file at '$resultfile_path' does not exist"
    Write-AnsibleLog "ERROR - $msg" "async_watchdog"
    throw $msg
}
$result_json = Get-Content -Path $resultfile_path -Raw
Write-AnsibleLog "INFO - result file json is: $result_json" "async_watchdog"
$result = ConvertFrom-AnsibleJson -InputObject $result_json

Write-AnsibleLog "INFO - creating async runspace" "async_watchdog"
$rs = [RunspaceFactory]::CreateRunspace()
$rs.Open()

Write-AnsibleLog "INFO - creating async PowerShell pipeline" "async_watchdog"
$ps = [PowerShell]::Create()
$ps.Runspace = $rs

# these functions are set in exec_wrapper
Write-AnsibleLog "INFO - adding global functions to PowerShell pipeline script" "async_watchdog"
$ps.AddScript($script:common_functions).AddStatement() > $null
$ps.AddScript($script:wrapper_functions).AddStatement() > $null
$function_params = @{
    Name = "common_functions"
    Value = $script:common_functions
    Scope = "script"
}
$ps.AddCommand("Set-Variable").AddParameters($function_params).AddStatement() > $null

Write-AnsibleLog "INFO - adding $($actions[0]) to PowerShell pipeline script" "async_watchdog"
$ps.AddScript($entrypoint).AddArgument($payload) > $null

Write-AnsibleLog "INFO - async job start, calling BeginInvoke()" "async_watchdog"
$job_async_result = $ps.BeginInvoke()

Write-AnsibleLog "INFO - waiting '$max_exec_time_sec' seconds for async job to complete" "async_watchdog"
$job_async_result.AsyncWaitHandle.WaitOne($max_exec_time_sec * 1000) > $null
$result.finished = 1

if ($job_async_result.IsCompleted) {
    Write-AnsibleLog "INFO - async job completed, calling EndInvoke()" "async_watchdog"

    $job_output = $ps.EndInvoke($job_async_result)
    $job_error = $ps.Streams.Error

    Write-AnsibleLog "INFO - raw module stdout:`r`n$($job_output | Out-String)" "async_watchdog"
    if ($job_error) {
        Write-AnsibleLog "WARN - raw module stderr:`r`n$($job_error | Out-String)" "async_watchdog"
    }

    # write success/output/error to result object
    # TODO: cleanse leading/trailing junk
    try {
        Write-AnsibleLog "INFO - deserializing Ansible stdout" "async_watchdog"
        $module_result = ConvertFrom-AnsibleJson -InputObject $job_output
        # TODO: check for conflicting keys
        $result = $result + $module_result
    }
    catch {
        $result.failed = $true
        $result.msg = "failed to parse module output: $($_.Exception.Message)"
        # return output back to Ansible to help with debugging errors
        $result.stdout = $job_output | Out-String
        $result.stderr = $job_error | Out-String
    }

    $result_json = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    Set-Content -Path $resultfile_path -Value $result_json

    Write-AnsibleLog "INFO - wrote output to $resultfile_path" "async_watchdog"
}
else {
    Write-AnsibleLog "ERROR - reached timeout on async job, stopping job" "async_watchdog"
    $ps.BeginStop($null, $null)  > $null # best effort stop

    # write timeout to result object
    $result.failed = $true
    $result.msg = "timed out waiting for module completion"
    $result_json = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    Set-Content -Path $resultfile_path -Value $result_json

    Write-AnsibleLog "INFO - wrote timeout to '$resultfile_path'" "async_watchdog"
}

# in the case of a hung pipeline, this will cause the process to stay alive until it's un-hung...
#$rs.Close() | Out-Null

Write-AnsibleLog "INFO - ending async_watchdog" "async_watchdog"
