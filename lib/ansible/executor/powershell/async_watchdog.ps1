# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace Microsoft.Win32.SafeHandles
using namespace System.Collections
using namespace System.IO
using namespace System.Management.Automation
using namespace System.Text
using namespace System.Threading

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $ResultPath,

    [Parameter(Mandatory)]
    [int]
    $Timeout,

    [Parameter(Mandatory)]
    [Int64]
    $WaitHandleId
)

if (-not (Test-Path -LiteralPath $ResultPath)) {
    throw "async result file at '$ResultPath' does not exist"
}
$result = Get-Content -LiteralPath $ResultPath | ConvertFrom-Json | Convert-JsonObject

# The intermediate script is used so that things are set up like it normally
# is. The new Runspace is used to ensure we can stop it once the async time is
# exceeded.
$execInfo = Get-AnsibleExecWrapper -ManifestAsParam -IncludeScriptBlock
$ps = [PowerShell]::Create()
$null = $ps.AddScript(@'
[CmdletBinding()]
param([ScriptBlock]$ScriptBlock, $Param)

& $ScriptBlock.Ast.GetScriptBlock() @Param
'@).AddParameters(
    @{
        ScriptBlock = $execInfo.ScriptInfo.ScriptBlock
        Param = $execInfo.Parameters
    })

# It is important we run with the invocation settings so that it has access
# to the same PSHost. The pipeline input also needs to be marked as complete
# so the exec_wrapper isn't waiting for input indefinitely.
$pipelineInput = [PSDataCollection[object]]::new()
$pipelineInput.Complete()
$invocationSettings = [PSInvocationSettings]@{
    Host = $host
}

# Signals async_wrapper that we are ready to start the job and to stop waiting
$waitHandle = [SafeWaitHandle]::new([IntPtr]$WaitHandleId, $true)
$waitEvent = [ManualResetEvent]::new($false)
$waitEvent.SafeWaitHandle = $waitHandle
$null = $waitEvent.Set()

$jobOutput = $null
$jobError = $null
try {
    $jobAsyncResult = $ps.BeginInvoke($pipelineInput, $invocationSettings, $null, $null)
    $jobAsyncResult.AsyncWaitHandle.WaitOne($Timeout * 1000) > $null
    $result.finished = $true

    if ($jobAsyncResult.IsCompleted) {
        $jobOutput = @($ps.EndInvoke($jobAsyncResult) | Out-String) -join "`n"
        $jobError = $ps.Streams.Error

        # write success/output/error to result object
        $moduleResultJson = $jobOutput
        $startJsonChar = $moduleResultJson.IndexOf([char]'{')
        if ($startJsonChar -eq -1) {
            throw "No start of json char found in module result"
        }
        $moduleResultJson = $moduleResultJson.Substring($startJsonChar)

        $endJsonChar = $moduleResultJson.LastIndexOf([char]'}')
        if ($endJsonChar -eq -1) {
            throw "No end of json char found in module result"
        }

        $trailingJunk = $moduleResultJson.Substring($endJsonChar + 1).Trim()
        $moduleResultJson = $moduleResultJson.Substring(0, $endJsonChar + 1)
        $moduleResult = $moduleResultJson | ConvertFrom-Json | Convert-JsonObject
        # TODO: check for conflicting keys
        $result = $result + $moduleResult

        if ($trailingJunk) {
            if (-not $result.warnings) {
                $result.warnings = @()
            }
            $result.warnings += "Module invocation had junk after the JSON data: $trailingJunk"
        }
    }
    else {
        # We can't call Stop() as pwsh won't respond if it is busy calling a .NET
        # method. The process end will shut everything down instead.
        $ps.BeginStop($null, $null)  > $null

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
    $result.stdout = $jobOutput
    $result.stderr = $jobError | Out-String
}
finally {
    $resultJson = ConvertTo-Json -InputObject $result -Depth 99 -Compress
    Set-Content -LiteralPath $ResultPath -Value $resultJson -Encoding UTF8
}
