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

$ps = [PowerShell]::Create()

if ($ForModule) {
    $ps.Runspace.SessionStateProxy.SetVariable("ErrorActionPreference", "Stop")
}
else {
    # For script files we want to ensure we load it as UTF-8. We don't set this
    # for modules as they are loaded from memory whereas a script is loaded
    # from disk as part of the script being run than by us.
    Set-WinPSDefaultFileEncoding
}

foreach ($variable in $Variables) {
    $null = $ps.AddCommand("Set-Variable").AddParameters($variable).AddStatement()
}

# env vars are process side so we can just set them here.
foreach ($env in $Environment.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($env.Key, $env.Value)
}

# Redefine Write-Host to dump to output instead of failing, lots of scripts
# still use it.
$null = $ps.AddScript('Function Write-Host($msg) { Write-Output -InputObject $msg }').AddStatement()

$scriptInfo = Get-AnsibleScript -Name $Script
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
    if ($PowerShellModules) {
        foreach ($utilName in $PowerShellModules) {
            $utilInfo = Get-AnsibleScript -Name $utilName
            if ($utilInfo.ShouldConstrain) {
                throw "PowerShell module util '$utilName' is not trusted and cannot be loaded."
            }

            $null = $ps.AddScript(@'
param ($Name, $Script)

$moduleName = [System.IO.Path]::GetFileNameWithoutExtension($Name)
$sbk = [System.Management.Automation.Language.Parser]::ParseInput(
    $Script,
    $Name,
    [ref]$null,
    [ref]$null).GetScriptBlock()

New-Module -Name $moduleName -ScriptBlock $sbk |
    Import-Module -WarningAction SilentlyContinue -Scope Global
'@, $true)
            $null = $ps.AddParameters(
                @{
                    Name = $utilName
                    Script = $utilInfo.Script
                }
            ).AddStatement()
        }
    }

    if ($CSharpModules) {
        # C# utils are process wide so just load them here.
        Import-CSharpUtil -Name $CSharpModules
    }

    # We invoke it through a command with useLocalScope $false to
    # ensure the code runs with it's own $script: scope. It also
    # cleans up the StackTrace on errors by not showing the stub
    # execution line and starts immediately at the module "cmd".
    $null = $ps.AddScript(@'
${function:<AnsibleModule>} = [System.Management.Automation.Language.Parser]::ParseInput(
    $args[0],
    $args[1],
    [ref]$null,
    [ref]$null).GetScriptBlock()
'@).AddArgument($scriptInfo.Script).AddArgument($Script).AddStatement()
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
