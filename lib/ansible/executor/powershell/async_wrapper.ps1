# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Payload
)

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting async_wrapper" "async_wrapper"

if (-not $Payload.environment.ContainsKey("ANSIBLE_ASYNC_DIR")) {
    Write-AnsibleError -Message "internal error: the environment variable ANSIBLE_ASYNC_DIR is not set and is required for an async task"
    $host.SetShouldExit(1)
    return
}
$async_dir = [System.Environment]::ExpandEnvironmentVariables($Payload.environment.ANSIBLE_ASYNC_DIR)

# calculate the result path so we can include it in the worker payload
$jid = $Payload.async_jid
$local_jid = $jid + "." + $pid

$results_path = [System.IO.Path]::Combine($async_dir, $local_jid)

Write-AnsibleLog "INFO - creating async results path at '$results_path'" "async_wrapper"

$Payload.async_results_path = $results_path
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($results_path)) > $null

# we use Win32_Process to escape the current process job, CreateProcess with a
# breakaway flag won't work for psrp as the psrp process does not have breakaway
# rights. Unfortunately we can't read/write to the spawned process as we can't
# inherit the handles. We use a locked down named pipe to send the exec_wrapper
# payload. Anonymous pipes won't work as the spawned process will not be a child
# of the current one and will not be able to inherit the handles

# pop the async_wrapper action so we don't get stuck in a loop and create new
# exec_wrapper for our async process
$Payload.actions = $Payload.actions[1..99]
$payload_json = ConvertTo-Json -InputObject $Payload -Depth 99 -Compress

#
$exec_wrapper = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.exec_wrapper))
$exec_wrapper += "`0`0`0`0" + $payload_json
$payload_bytes = [System.Text.Encoding]::UTF8.GetBytes($exec_wrapper)
$pipe_name = "ansible-async-$jid-$([guid]::NewGuid())"

# template the async process command line with the payload details
$bootstrap_wrapper = {
    # help with debugging errors as we loose visibility of the process output
    # from here on
    trap {
        $wrapper_path = "$($env:TEMP)\ansible-async-wrapper-error-$(Get-Date -Format "yyyy-MM-ddTHH-mm-ss.ffffZ").txt"
        $error_msg = "Error while running the async exec wrapper`r`n$($_ | Out-String)`r`n$($_.ScriptStackTrace)"
        Set-Content -Path $wrapper_path -Value $error_msg
        break
    }

    &chcp.com 65001 > $null

    # store the pipe name and no. of bytes to read, these are populated before
    # before the process is created - do not remove or changed
    $pipe_name = ""
    $bytes_length = 0

    $input_bytes = New-Object -TypeName byte[] -ArgumentList $bytes_length
    $pipe = New-Object -TypeName System.IO.Pipes.NamedPipeClientStream -ArgumentList @(
        ".",  # localhost
        $pipe_name,
        [System.IO.Pipes.PipeDirection]::In,
        [System.IO.Pipes.PipeOptions]::None,
        [System.Security.Principal.TokenImpersonationLevel]::Anonymous
    )
    try {
        $pipe.Connect()
        $pipe.Read($input_bytes, 0, $bytes_length) > $null
    } finally {
        $pipe.Close()
    }
    $exec = [System.Text.Encoding]::UTF8.GetString($input_bytes)
    $exec_parts = $exec.Split(@("`0`0`0`0"), 2, [StringSplitOptions]::RemoveEmptyEntries)
    Set-Variable -Name json_raw -Value $exec_parts[1]
    $exec = [ScriptBlock]::Create($exec_parts[0])
    &$exec
}

$bootstrap_wrapper = $bootstrap_wrapper.ToString().Replace('$pipe_name = ""', "`$pipe_name = `"$pipe_name`"")
$bootstrap_wrapper = $bootstrap_wrapper.Replace('$bytes_length = 0', "`$bytes_length = $($payload_bytes.Count)")
$encoded_command = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($bootstrap_wrapper))
$pwsh_path = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$exec_args = "`"$pwsh_path`" -NonInteractive -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded_command"

# create a named pipe that is set to allow only the current user read access
$current_user = ([Security.Principal.WindowsIdentity]::GetCurrent()).User
$pipe_sec = New-Object -TypeName System.IO.Pipes.PipeSecurity
$pipe_ar = New-Object -TypeName System.IO.Pipes.PipeAccessRule -ArgumentList @(
    $current_user,
    [System.IO.Pipes.PipeAccessRights]::Read,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$pipe_sec.AddAccessRule($pipe_ar)

Write-AnsibleLog "INFO - creating named pipe '$pipe_name'" "async_wrapper"
$pipe = New-Object -TypeName System.IO.Pipes.NamedPipeServerStream -ArgumentList @(
    $pipe_name,
    [System.IO.Pipes.PipeDirection]::Out,
    1,
    [System.IO.Pipes.PipeTransmissionMode]::Byte,
    [System.IO.Pipes.PipeOptions]::Asynchronous,
    0,
    0,
    $pipe_sec
)

try {
    Write-AnsibleLog "INFO - creating async process '$exec_args'" "async_wrapper"
    $process = Invoke-CimMethod -ClassName Win32_Process -Name Create -Arguments @{CommandLine=$exec_args}
    $rc = $process.ReturnValue

    Write-AnsibleLog "INFO - return value from async process exec: $rc" "async_wrapper"
    if ($rc -ne 0) {
        $error_msg = switch($rc) {
            2 { "Access denied" }
            3 { "Insufficient privilege" }
            8 { "Unknown failure" }
            9 { "Path not found" }
            21 { "Invalid parameter" }
            default { "Other" }
        }
        throw "Failed to start async process: $rc ($error_msg)"
    }
    $watchdog_pid = $process.ProcessId
    Write-AnsibleLog "INFO - created async process PID: $watchdog_pid" "async_wrapper"

    # populate initial results before we send the async data to avoid result race
    $result = @{
        started = 1;
        finished = 0;
        results_file = $results_path;
        ansible_job_id = $local_jid;
        _ansible_suppress_tmpdir_delete = $true;
        ansible_async_watchdog_pid = $watchdog_pid
    }

    Write-AnsibleLog "INFO - writing initial async results to '$results_path'" "async_wrapper"
    $result_json = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    Set-Content $results_path -Value $result_json

    Write-AnsibleLog "INFO - waiting for async process to connect to named pipe for 5 seconds" "async_wrapper"
    $wait_async = $pipe.BeginWaitForConnection($null, $null)
    $wait_async.AsyncWaitHandle.WaitOne(5000) > $null
    if (-not $wait_async.IsCompleted) {
        throw "timeout while waiting for child process to connect to named pipe"
    }
    $pipe.EndWaitForConnection($wait_async)

    Write-AnsibleLog "INFO - writing exec_wrapper and payload to async process" "async_wrapper"
    $pipe.Write($payload_bytes, 0, $payload_bytes.Count)
    $pipe.Flush()
    $pipe.WaitForPipeDrain()
} finally {
    $pipe.Close()
}

Write-AnsibleLog "INFO - outputting initial async result: $result_json" "async_wrapper"
Write-Output -InputObject $result_json
Write-AnsibleLog "INFO - ending async_wrapper" "async_wrapper"
