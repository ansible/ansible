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
    $ForModule,

    [Parameter()]
    [switch]
    $WaitForDebugger,

    [Parameter()]
    [IDictionary]
    $DebugParam = @{}
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
            "$($ErrorRecord.InvocationInfo.PositionMessage)"
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

# It is important we use CreateDefault2 to ensure that builtin modules are
# imported when requested. CreateDefault only imports the builtin modules
# as snapins which miss things like ETS type definitions.
$ps = [PowerShell]::Create([InitialSessionState]::CreateDefault2())

if ($ForModule) {
    $ps.Runspace.SessionStateProxy.SetVariable("ErrorActionPreference", "Stop")

    foreach ($variable in $Variables) {
        $null = $ps.AddCommand("Set-Variable").AddParameters($variable).AddStatement()
    }
}
else {
    # For script files we want to ensure we load it as UTF-8. We don't set this
    # for modules as they are loaded from memory whereas a script is loaded
    # from disk as part of the script being run than by us.
    Set-WinPSDefaultFileEncoding
}

# env vars are process side so we can just set them here.
foreach ($env in $Environment.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($env.Key, $env.Value)
}

# Redefine Write-Host to dump to output instead of failing, lots of scripts
# still use it.
$null = $ps.AddScript('Function Write-Host($msg) { Write-Output -InputObject $msg }').AddStatement()

# ParseInput doesn't throw on an invalid script, we need to check the errors
# and throw ourselves. We use ParseInput so we can associate a filename with
# the script making StackTraces and error messages much easier to understand.
$parseScriptWithName = {
    [OutputType([ScriptBlock])]
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [string]
        $Name,

        [Parameter(Mandatory)]
        [string]
        $Script
    )

    $err = @()
    $ast = [System.Management.Automation.Language.Parser]::ParseInput(
        $Script,
        $Name,
        [ref]$null,
        [ref]$err)
    if ($err) {
        $parseErrors = $err -join "`n"
        throw "Failed to parse script '$Name'`n$parseErrors"
    }

    $ast.GetScriptBlock()
}

$scriptInfo = Get-AnsibleScript -Name $Script
$pwshUtilInfo = @(
    if ($PowerShellModules) {
        foreach ($utilName in $PowerShellModules) {
            Get-AnsibleScript -Name $utilName
        }
    }
)

$debugger = $null
if ($DebugParam.Count) {
    if ($scriptInfo.ShouldConstrain) {
        throw "Cannot run untrusted PowerShell script '$Script' in ConstrainedLanguage mode with a debugger."
    }

    # Get a more friendly name for debug session but fallback to the original
    # name if using an unexpected format.
    $extraMappings = @()
    $DebugParam.Name = if ($scriptInfo.Name.StartsWith('ansible.builtin.script.')) {
        "script: $($scriptInfo.Name.Substring(23))"

        # We want to set the local root to the actual script path rather than
        # the stub invoker script. The script action plugin sets this variable
        # for us so we can use it here to get the correct path.
        $extraMappings = @(
            @{
                localRoot = $scriptInfo.Path
                remoteRoot = $Variables[0].Value.script_path
            }
        )
    }
    elseif ($scriptInfo.Name -match 'ansible_collections\.(.+?)\.plugins\.modules\.(.+)') {
        "$($matches[1]).$($matches[2])"
    }
    else {
        $scriptInfo.Name
    }

    $DebugParam.Pipeline = $ps
    $DebugParam.PathMapping = @(
        # It is important the path mappings are set before to ensure
        # script paths take priority over the stub name.
        $extraMappings

        @{
            localRoot = $scriptInfo.Path
            remoteRoot = $scriptInfo.Name
        }
        foreach ($utilInfo in $pwshUtilInfo) {
            @{
                localRoot = $utilInfo.Path
                remoteRoot = $utilInfo.Name
            }
        }
    )
    $debugWrapper = Get-AnsibleScript -Name 'debug_wrapper.ps1' -IncludeScriptBlock
    $debugger = & $debugWrapper.ScriptBlock @DebugParam
}

if ($scriptInfo.ShouldConstrain) {
    # Fail if there are any module utils, in the future we may allow unsigned
    # PowerShell utils in CLM but for now we don't.
    if ($PowerShellModules -or $CSharpModules) {
        throw "Cannot run untrusted PowerShell script '$Script' in ConstrainedLanguage mode with module util imports."
    }

    # If the module is marked as needing to be constrained then we set the
    # language mode to ConstrainedLanguage so that when parsed inside the
    # Runspace it will run in CLM. We need to run it from a filepath as in
    # CLM we cannot call the methods needed to create the ScriptBlock and we
    # need to be in CLM to downgrade the language mode.
    $null = $ps.AddScript('$ExecutionContext.SessionState.LanguageMode = "ConstrainedLanguage"').AddStatement()
    $scriptPath = New-TempAnsibleFile -FileName $Script -Content $scriptInfo.Script
    $null = $ps.AddCommand($scriptPath, $false).AddStatement()
}
else {
    foreach ($utilInfo in $pwshUtilInfo) {
        if ($utilInfo.ShouldConstrain) {
            throw "PowerShell module util '$($utilInfo.Name)' is not trusted and cannot be loaded."
        }

        $null = $ps.AddScript($parseScriptWithName).AddParameters(@{
                Name = $utilInfo.Name
                Script = $utilInfo.Script
            })
        $null = $ps.AddScript(@'
New-Module -Name $args[0] -ScriptBlock @($input)[0] |
    Import-Module -WarningAction SilentlyContinue -Scope Global
'@).AddArgument([Path]::GetFileNameWithoutExtension($utilInfo.Name)).AddStatement()
    }

    if ($CSharpModules) {
        # C# utils are process wide so just load them here.
        Import-CSharpUtil -Name $CSharpModules
    }

    # We invoke it through a command with useLocalScope $false to
    # ensure the code runs with it's own $script: scope. It also
    # cleans up the StackTrace on errors by not showing the stub
    # execution line and starts immediately at the module "cmd".
    $null = $ps.AddScript($parseScriptWithName).AddParameters(@{
            Name = $Script
            Script = $scriptInfo.Script
        }).AddScript(@'
${function:<AnsibleModule>} = @($input)[0]
'@).AddStatement()

    if ($debugger -and ($WaitForDebugger -or $PSVersionTable.PSVersion -lt '6.0')) {
        # The debugger is set to stop on the next command which is the module
        # code. PowerShell 5.1 must have this or else it'll never receive the
        # breakpoint information as the debugger never has a chance to run any
        # commands.
        $null = $ps.AddCommand('Wait-Debugger').AddStatement()
    }

    $null = $ps.AddCommand('<AnsibleModule>', $false).AddStatement()
}

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

if ($debugger) {
    $debugger.WaitForExit()
    $debugger.Dispose()
}
