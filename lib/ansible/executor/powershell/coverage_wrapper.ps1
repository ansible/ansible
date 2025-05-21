# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.Collections.Generic
using namespace System.IO
using namespace System.Management.Automation
using namespace System.Management.Automation.Language
using namespace System.Reflection
using namespace System.Text

param(
    [Parameter(Mandatory)]
    [string]
    $ModuleName,

    [Parameter(Mandatory)]
    [string]
    $OutputPath,

    [Parameter(Mandatory)]
    [string]
    $PathFilter
)

# Required to be set for psrp so we can set a breakpoint in the remote runspace
$Host.Runspace.Debugger.SetDebugMode([DebugModes]::RemoteScript)

Function New-CoverageBreakpointsForScriptBlock {
    Param (
        [Parameter(Mandatory)]
        [string]
        $ScriptName,

        [Parameter(Mandatory)]
        [ScriptBlockAst]
        $ScriptBlockAst,

        [Parameter(Mandatory)]
        [String]
        $AnsiblePath
    )

    $predicate = {
        $args[0] -is [CommandBaseAst]
    }
    $scriptCmds = $ScriptBlockAst.FindAll($predicate, $true)

    # Create an object that tracks the Ansible path of the file and the breakpoints that have been set in it
    $info = [PSCustomObject]@{
        Path = $AnsiblePath
        Breakpoints = [List[Breakpoint]]@()
    }

    # LineBreakpoint was only made public in PowerShell 6.0 so we need to use
    # reflection to achieve the same thing in 5.1.
    $lineCtor = if ($PSVersionTable.PSVersion -lt '6.0') {
        [LineBreakpoint].GetConstructor(
            [BindingFlags]'NonPublic, Instance',
            $null,
            [type[]]@([string], [int], [int], [scriptblock]),
            $null)
    }
    else {
        [LineBreakpoint]::new
    }

    # Keep track of lines that are already scanned. PowerShell can contains multiple commands in 1 line
    $scannedLines = [HashSet[int]]@()
    foreach ($cmd in $scriptCmds) {
        if (-not $scannedLines.Add($cmd.Extent.StartLineNumber)) {
            continue
        }

        # Action is explicitly $null as it will slow down the runtime quite dramatically.
        $b = $lineCtor.Invoke(@($ScriptName, $cmd.Extent.StartLineNumber, $cmd.Extent.StartColumnNumber, $null))
        $info.Breakpoints.Add($b)
    }

    [Runspace]::DefaultRunspace.Debugger.SetBreakpoints($info.Breakpoints)

    $info
}

Function Compare-PathFilterPattern {
    Param (
        [String[]]$Patterns,
        [String]$Path
    )

    foreach ($pattern in $Patterns) {
        if ($Path -like $pattern) {
            return $true
        }
    }
    return $false
}

$actionInfo = Get-NextAnsibleAction
$actionParams = $actionInfo.Parameters

# A PS Breakpoint needs a path to be associated with the ScriptBlock, luckily
# the Get-AnsibleScript does this for us.
$breakpointInfo = @()

try {
    $coveragePathFilter = $PathFilter.Split(":", [StringSplitOptions]::RemoveEmptyEntries)
    $breakpointInfo = @(
        foreach ($scriptName in @($ModuleName; $actionParams.PowerShellModules)) {
            # We don't use -IncludeScriptBlock as the script might be untrusted
            # and will run under CLM. While we recreate the ScriptBlock here it
            # is only to get the AST that contains the statements and their
            # line numbers to create the breakpoint info for.
            $scriptInfo = Get-AnsibleScript -Name $scriptName

            if (Compare-PathFilterPattern -Patterns $coveragePathFilter -Path $scriptInfo.Path) {
                $covParams = @{
                    ScriptName = $scriptInfo.Name
                    ScriptBlockAst = [ScriptBlock]::Create($scriptInfo.Script).Ast
                    AnsiblePath = $scriptInfo.Path
                }
                New-CoverageBreakpointsForScriptBlock @covParams
            }
        }
    )

    if ($breakpointInfo) {
        $actionParams.Breakpoints = $breakpointInfo.Breakpoints
    }

    try {
        & $actionInfo.ScriptBlock @actionParams
    }
    finally {
        # Processing here is kept to an absolute minimum to make sure each task runtime is kept as small as
        # possible. Once all the tests have been run ansible-test will collect this info and process it locally in
        # one go.
        $coverageInfo = @{}
        foreach ($info in $breakpointInfo) {
            $coverageInfo[$info.Path] = $info.Breakpoints | Select-Object -Property Line, HitCount
        }

        $psVersion = "$($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)"
        $coverageOutputPath = "$OutputPath=powershell-$psVersion=coverage.$($env:COMPUTERNAME).$PID.$(Get-Random)"
        $codeCovJson = ConvertTo-Json -InputObject $coverageInfo -Compress

        # Ansible controller expects these files to be UTF-8 without a BOM, use .NET for this.
        $utf8 = [UTF8Encoding]::new($false)
        [File]::WriteAllText($coverageOutputPath, $codeCovJson, $utf8)
    }
}
finally {
    foreach ($b in $breakpointInfo.Breakpoints) {
        Remove-PSBreakpoint -Breakpoint $b
    }
}
