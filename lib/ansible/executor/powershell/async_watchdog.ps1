# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace Microsoft.Win32.SafeHandles
using namespace System.Collections
using namespace System.Text
using namespace System.Threading

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [IDictionary]
    $Payload
)

$ErrorActionPreference = "Stop"

# pop 0th action as entrypoint
$payload.actions = $payload.actions[1..99]

$actions = $Payload.actions
$entrypoint = $payload.($actions[0])
$entrypoint = [Encoding]::UTF8.GetString([Convert]::FromBase64String($entrypoint))

$resultPath = $payload.async_results_path
$timeoutSec = $payload.async_timeout_sec
$waitHandleId = $payload.async_wait_handle_id

if (-not (Test-Path -LiteralPath $resultPath)) {
    throw "result file at '$resultPath' does not exist"
}
$resultJson = Get-Content -LiteralPath $resultPath -Raw
$result = ConvertFrom-AnsibleJson -InputObject $resultJson

$ps = [PowerShell]::Create()

# these functions are set in exec_wrapper
$ps.AddScript($script:common_functions).AddStatement() > $null
$ps.AddScript($script:wrapper_functions).AddStatement() > $null
$functionParams = @{
    Name = "common_functions"
    Value = $script:common_functions
    Scope = "script"
}
$ps.AddCommand("Set-Variable").AddParameters($functionParams).AddStatement() > $null

$ps.AddScript($entrypoint).AddArgument($payload) > $null

# Signals async_wrapper that we are ready to start the job and to stop waiting
$waitHandle = [SafeWaitHandle]::new([IntPtr]$waitHandleId, $true)
$waitEvent = [ManualResetEvent]::new($false)
$waitEvent.SafeWaitHandle = $waitHandle
$null = $waitEvent.Set()

$jobOutput = $null
$jobError = $null
try {
    $jobAsyncResult = $ps.BeginInvoke()
    $jobAsyncResult.AsyncWaitHandle.WaitOne($timeoutSec * 1000) > $null
    $result.finished = 1

    if ($jobAsyncResult.IsCompleted) {
        $jobOutput = $ps.EndInvoke($jobAsyncResult)
        $jobError = $ps.Streams.Error

        # write success/output/error to result object
        # TODO: cleanse leading/trailing junk
        $moduleResult = ConvertFrom-AnsibleJson -InputObject $jobOutput
        # TODO: check for conflicting keys
        $result = $result + $moduleResult
    }
    else {
        $ps.BeginStop($null, $null)  > $null # best effort stop

        throw "timed out waiting for module completion"
    }
}
catch {
    $exception = @(
        "$_"
        "$($_.InvocationInfo.PositionMessage)"
        "+ CategoryInfo          : $($_.CategoryInfo)"
        "+ FullyQualifiedErrorId : $($_.FullyQualifiedErrorId)"
        ""
        "ScriptStackTrace:"
        "$($_.ScriptStackTrace)"

        if ($_.Exception.StackTrace) {
            "$($_.Exception.StackTrace)"
        }
    ) -join ([Environment]::NewLine)

    $result.exception = $exception
    $result.failed = $true
    $result.msg = "failure during async watchdog: $_"
    # return output back, if available, to Ansible to help with debugging errors
    $result.stdout = $jobOutput | Out-String
    $result.stderr = $jobError | Out-String
}
finally {
    $resultJson = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    Set-Content -LiteralPath $resultPath -Value $resultJson -Encoding UTF8
}
