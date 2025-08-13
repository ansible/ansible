# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible._Async

using namespace System.Collections
using namespace System.Diagnostics
using namespace System.IO
using namespace System.IO.Pipes
using namespace System.Text
using namespace System.Threading

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $AsyncDir,

    [Parameter(Mandatory)]
    [string]
    $AsyncJid,

    [Parameter(Mandatory)]
    [int]
    $StartupTimeout
)

Import-CSharpUtil -Name 'Ansible._Async.cs'

$AsyncDir = [Environment]::ExpandEnvironmentVariables($AsyncDir)
if (-not [Directory]::Exists($asyncDir)) {
    $null = [Directory]::CreateDirectory($asyncDir)
}

$parentProcessId = 0
$parentProcessHandle = $stdoutReader = $stderrReader = $stdinPipe = $stdoutPipe = $stderrPipe = $asyncProcess = $waitHandle = $null
try {
    $utf8 = [UTF8Encoding]::new($false)
    $stdinPipe = [AnonymousPipeServerStream]::new([PipeDirection]::Out, [HandleInheritability]::Inheritable)
    $stdoutPipe = [AnonymousPipeServerStream]::new([PipeDirection]::In, [HandleInheritability]::Inheritable)
    $stderrPipe = [AnonymousPipeServerStream]::new([PipeDirection]::In, [HandleInheritability]::Inheritable)
    $stdoutReader = [StreamReader]::new($stdoutPipe, $utf8, $false)
    $stderrReader = [StreamReader]::new($stderrPipe, $utf8, $false)
    $clientWaitHandle = $waitHandle = [Ansible._Async.AsyncUtil]::CreateInheritableEvent()

    $stdinHandle = $stdinPipe.ClientSafePipeHandle
    $stdoutHandle = $stdoutPipe.ClientSafePipeHandle
    $stderrHandle = $stderrPipe.ClientSafePipeHandle

    $executable = if ($PSVersionTable.PSVersion -lt '6.0') {
        'powershell.exe'
    }
    else {
        'pwsh.exe'
    }
    $executablePath = Join-Path -Path $PSHome -ChildPath $executable

    # We need to escape the job of the current process to allow the async
    # process to outlive the Windows job. If the current process is not part of
    # a job or job allows us to breakaway we can spawn the process directly.
    # Otherwise we use WMI Win32_Process.Create to create a process as our user
    # outside the job and use that as the async process parent. The winrm and
    # ssh connection plugin allows breaking away from the job but psrp does not.
    if (-not [Ansible._Async.AsyncUtil]::CanCreateBreakawayProcess()) {
        # We hide the console window and suspend the process to avoid it running
        # anything. We only need the process to be created outside the job and not
        # for it to run.
        $psi = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{
            CreateFlags = [uint32]4  # CREATE_SUSPENDED
            ShowWindow = [uint16]0  # SW_HIDE
        }
        $procInfo = Invoke-CimMethod -ClassName Win32_Process -Name Create -Arguments @{
            CommandLine = $executablePath
            ProcessStartupInformation = $psi
        }
        $rc = $procInfo.ReturnValue
        if ($rc -ne 0) {
            $msg = switch ($rc) {
                2 { "Access denied" }
                3 { "Insufficient privilege" }
                8 { "Unknown failure" }
                9 { "Path not found" }
                21 { "Invalid parameter" }
                default { "Other" }
            }
            throw "Failed to start async parent process: $rc $msg"
        }

        # WMI returns a UInt32, we want the signed equivalent of those bytes.
        $parentProcessId = [Convert]::ToInt32(
            [Convert]::ToString($procInfo.ProcessId, 16),
            16)

        $parentProcessHandle = [Ansible._Async.AsyncUtil]::OpenProcessAsParent($parentProcessId)
        $clientWaitHandle = [Ansible._Async.AsyncUtil]::DuplicateHandleToProcess($waitHandle, $parentProcessHandle)
        $stdinHandle = [Ansible._Async.AsyncUtil]::DuplicateHandleToProcess($stdinHandle, $parentProcessHandle)
        $stdoutHandle = [Ansible._Async.AsyncUtil]::DuplicateHandleToProcess($stdoutHandle, $parentProcessHandle)
        $stderrHandle = [Ansible._Async.AsyncUtil]::DuplicateHandleToProcess($stderrHandle, $parentProcessHandle)
        $stdinPipe.DisposeLocalCopyOfClientHandle()
        $stdoutPipe.DisposeLocalCopyOfClientHandle()
        $stderrPipe.DisposeLocalCopyOfClientHandle()
    }

    $localJid = "$AsyncJid.$pid"
    $resultsPath = [Path]::Combine($AsyncDir, $localJid)

    $bootstrapWrapper = Get-AnsibleScript -Name bootstrap_wrapper.ps1
    $execAction = Get-AnsibleExecWrapper -EncodeInputOutput

    $execAction.Parameters.ActionParameters = @{
        ResultPath = $resultsPath
        WaitHandleId = [Int64]$clientWaitHandle.DangerousGetHandle()
    }
    $execWrapper = @{
        name = 'exec_wrapper-async.ps1'
        script = $execAction.ScriptInfo.Script
        params = $execAction.Parameters
    } | ConvertTo-Json -Compress -Depth 99
    $asyncInput = "$execWrapper`n`0`0`0`0`n$($execAction.InputData)"

    $encCommand = [Convert]::ToBase64String([Encoding]::Unicode.GetBytes($bootstrapWrapper.Script))
    $asyncCommand = "`"$executablePath`" -NonInteractive -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encCommand"

    $asyncProcess = [Ansible._Async.AsyncUtil]::CreateAsyncProcess(
        $executablePath,
        $asyncCommand,
        $stdinHandle,
        $stdoutHandle,
        $stderrHandle,
        $clientWaitHandle,
        $parentProcessHandle,
        $stdoutReader,
        $stderrReader)

    # We need to write the result file before the process is started to ensure
    # it can read the file.
    $result = @{
        started = $true
        finished = $false
        results_file = $resultsPath
        ansible_job_id = $localJid
        _ansible_suppress_tmpdir_delete = $true
        ansible_async_watchdog_pid = $asyncProcess.ProcessId
    }
    $resultJson = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    [File]::WriteAllText($resultsPath, $resultJson, $utf8)

    if ($parentProcessHandle) {
        [Ansible._Async.AsyncUtil]::CloseHandleInProcess($stdinHandle, $parentProcessHandle)
        [Ansible._Async.AsyncUtil]::CloseHandleInProcess($stdoutHandle, $parentProcessHandle)
        [Ansible._Async.AsyncUtil]::CloseHandleInProcess($stderrHandle, $parentProcessHandle)
        [Ansible._Async.AsyncUtil]::CloseHandleInProcess($clientWaitHandle, $parentProcessHandle)
    }
    else {
        $stdinPipe.DisposeLocalCopyOfClientHandle()
        $stdoutPipe.DisposeLocalCopyOfClientHandle()
        $stderrPipe.DisposeLocalCopyOfClientHandle()
    }

    [Ansible._Async.AsyncUtil]::ResumeThread($asyncProcess.Thread)

    # If writing to the pipe fails the process has already ended.
    $procAlive = $true
    $procIn = [StreamWriter]::new($stdinPipe, $utf8)
    try {
        $procIn.WriteLine($asyncInput)
        $procIn.Flush()
        $procIn.Dispose()
    }
    catch [IOException] {
        $procAlive = $false
    }

    if ($procAlive) {
        # Wait for the process to signal it has started the async task or if it
        # has ended early/timed out.
        $waitTimespan = [TimeSpan]::FromSeconds($StartupTimeout)
        $handleIdx = [WaitHandle]::WaitAny(
            @(
                [Ansible._Async.ManagedWaitHandle]::new($waitHandle),
                [Ansible._Async.ManagedWaitHandle]::new($asyncProcess.Process)
            ),
            $waitTimespan)
        if ($handleIdx -eq [WaitHandle]::WaitTimeout) {
            $msg = -join @(
                "Ansible encountered a timeout while waiting for the async task to start and signal it has started. "
                "This can be affected by the performance of the target - you can increase this timeout using "
                "WIN_ASYNC_STARTUP_TIMEOUT or just for this host using the ansible_win_async_startup_timeout hostvar "
                "if this keeps happening."
            )
            throw $msg
        }
        $procAlive = $handleIdx -eq 0
    }

    if ($procAlive) {
        $resultJson
    }
    else {
        # If the process had ended before it signaled it was ready, we return
        # back the raw output and hope it contains an error.
        Remove-Item -LiteralPath $resultsPath -ErrorAction Ignore

        $stdout = $asyncProcess.StdoutReader.GetAwaiter().GetResult()
        $stderr = $asyncProcess.StderrReader.GetAwaiter().GetResult()
        $rc = [Ansible._Async.AsyncUtil]::GetProcessExitCode($asyncProcess.Process)

        $host.UI.WriteLine($stdout)
        Write-PowerShellClixmlStderr -Output $stderr
        $host.SetShouldExit($rc)
    }
}
finally {
    if ($parentProcessHandle) { $parentProcessHandle.Dispose() }
    if ($parentProcessId) {
        Stop-Process -Id $parentProcessId -Force -ErrorAction Ignore
    }
    if ($stdoutReader) { $stdoutReader.Dispose() }
    if ($stderrReader) { $stderrReader.Dispose() }
    if ($stdinPipe) { $stdinPipe.Dispose() }
    if ($stdoutPipe) { $stdoutPipe.Dispose() }
    if ($stderrPipe) { $stderrPipe.Dispose() }
    if ($asyncProcess) { $asyncProcess.Dispose() }
    if ($waitHandle) { $waitHandle.Dispose() }
}
