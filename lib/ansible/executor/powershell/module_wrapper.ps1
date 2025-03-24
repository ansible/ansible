# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.Collections
using namespace System.IO
using namespace System.Management.Automation
using namespace System.Management.Automation.Language
using namespace System.Management.Automation.Security
using namespace System.Text

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]
    $Script,

    [Parameter()]
    [IDictionary[]]
    [AllowEmptyCollection()]
    $Variables = @(),

    [Parameter()]
    [IDictionary]
    $Environment,

    [Parameter()]
    [AllowEmptyCollection()]
    [string[]]
    $CSharpModules,

    [Parameter()]
    [AllowEmptyCollection()]
    [string[]]
    $PowerShellModules,

    [Parameter()]
    [LineBreakpoint[]]
    $Breakpoints,

    [Parameter()]
    [switch]
    $ForModule
)

Function Write-AnsibleErrorDetail {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [System.Management.Automation.ErrorRecord]
        $ErrorRecord,

        [Parameter()]
        [switch]
        $ForModule
    )

    # Be more defensive when trying to find the InnerException in case it isn't
    # set. This shouldn't ever be the case but if it is then it makes it more
    # difficult to track down the problem.
    if ($ErrorRecord.Exception.InnerException.ErrorRecord) {
        $ErrorRecord = $ErrorRecord.Exception.InnerException.ErrorRecord
    }

    $exception = @(
        "$ErrorRecord"

        # stderr from sub processes have this error id, we don't want to format those errors
        # like a normal powershell error record.
        if ($ErrorRecord.FullyQualifiedErrorId -notin @('NativeCommandError', 'NativeCommandErrorMessage')) {
            "$($invocationInfo.PositionMessage)"
            "+ CategoryInfo          : $($ErrorRecord.CategoryInfo)"
            "+ FullyQualifiedErrorId : $($ErrorRecord.FullyQualifiedErrorId)"
            ""
            "ScriptStackTrace:"
            "$($ErrorRecord.ScriptStackTrace)"

            if ($ErrorRecord.Exception.StackTrace) {
                "$($ErrorRecord.Exception.StackTrace)"
            }
        }
    ) -join ([Environment]::NewLine)

    if ($ForModule) {
        @{
            failed = $true
            msg = "Unhandled exception while executing module: $ErrorRecord"
            exception = $exception
        } | ConvertTo-Json -Compress
    }
    else {
        $host.UI.WriteErrorLine($exception)
    }
}

$ps = [PowerShell]::Create()

if ($ForModule) {
    $ps.Runspace.SessionStateProxy.SetVariable("ErrorActionPreference", "Stop")
}

foreach ($variable in $Variables) {
    $null = $ps.AddCommand("Set-Variable").AddParameters($variable).AddStatement()
}

if ($Environment.Count) {
    $ps.Runspace.SessionStateProxy.SetVariable("_AnsibleEnvironment", $Environment)
    $null = $ps.AddScript(@'
foreach ($env in $_AnsibleEnvironment.GetEnumerator()) {
    [System.Environment]::SetEnvironmentVariable($env.Key, $env.Value)
}
Remove-Variable -Name _AnsibleEnvironment -Force
'@).AddStatement()
}

# Redefine Write-Host to dump to output instead of failing, lots of scripts
# still use it.
$null = $ps.AddScript('Function Write-Host($msg) { Write-Output -InputObject $msg }').AddStatement()

if ($PowerShellModules) {
    Import-PowerShellUtil -Name $PowerShellModules -Pipeline $ps
}

if ($CSharpModules) {
    Import-CSharpUtil -Name $CSharpModules
}

# This will inject the script into the pipeline for us.
Get-AnsibleScript -Name $Script -Pipeline $ps
if ($Breakpoints) {
    $ps.Runspace.Debugger.SetBreakpoints($Breakpoints)
}

# Temporarily override the stdout stream and create our own in a StringBuilder.
# We use this to ensure there's always an Out pipe and that we capture the
# output for things like async or psrp.
$origOut = [Console]::Out
$sb = [StringBuilder]::new()
try {
    $newOut = [StringWriter]::new($sb)
    [Console]::SetOut($newOut)

    $modOut = @($ps.Invoke())
}
catch {
    Write-AnsibleErrorDetail -ErrorRecord $_ -ForModule:$ForModule
    if ($ForModule) {
        $host.SetShouldExit(1)
        return
    }
}
finally {
    if ($newOut) {
        [Console]::SetOut($origOut)
        $newOut.Dispose()
    }
}

$stdout = $sb.ToString()
if ($stdout) {
    $stdout
}
if ($modOut.Count) {
    $modOut -join "`r`n"
}

# Attempt to set the return code from the LASTEXITCODE variable. This is set
# explicitly in newer style modules when calling ExitJson and FailJson.
$rc = $ps.Runspace.SessionStateProxy.GetVariable("LASTEXITCODE")
if ($null -ne $rc) {
    $host.SetShouldExit($rc)
}

foreach ($err in $ps.Streams.Error) {
    Write-AnsibleErrorDetail -ErrorRecord $err -ForModule:$ForModule
    if ($ForModule) {
        if ($null -eq $rc) {
            $host.SetShouldExit(1)
        }
        return
    }
}
