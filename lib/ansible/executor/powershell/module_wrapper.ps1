# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

<#
.SYNOPSIS
Invokes an Ansible module in a new Runspace. This cmdlet will output the
module's output and write any errors to the error stream of the current
host.

.PARAMETER Scripts
[Object[]] String or ScriptBlocks to execute.

.PARAMETER Variables
[System.Collections.ArrayList] The variables to set in the new Pipeline.
Each value is a hashtable that contains the parameters to use with
Set-Variable;
    Name: the name of the variable to set
    Value: the value of the variable to set
    Scope: the scope of the variable

.PARAMETER Environment
[System.Collections.IDictionary] A Dictionary of environment key/values to
set in the new Pipeline.

.PARAMETER Modules
[System.Collections.IDictionary] A Dictionary of PowerShell modules to
import into the new Pipeline. The key is the name of the module and the
value is a base64 string of the module util code.

.PARAMETER ModuleName
[String] The name of the module that is being executed.

.PARAMETER Breakpoints
A list of line breakpoints to add to the runspace debugger. This is used to
track module and module_utils coverage.
#>
param(
    [Object[]]$Scripts,
    [System.Collections.ArrayList][AllowEmptyCollection()]$Variables,
    [System.Collections.IDictionary]$Environment,
    [System.Collections.IDictionary]$Modules,
    [String]$ModuleName,
    [System.Management.Automation.LineBreakpoint[]]$Breakpoints = @()
)

Write-AnsibleLog "INFO - creating new PowerShell pipeline for $ModuleName" "module_wrapper"
$ps = [PowerShell]::Create()

# do not set ErrorActionPreference for script
if ($ModuleName -ne "script") {
    $ps.Runspace.SessionStateProxy.SetVariable("ErrorActionPreference", "Stop")
}

# force input encoding to preamble-free UTF8 so PS sub-processes (eg,
# Start-Job) don't blow up. This is only required for WinRM, a PSRP
# runspace doesn't have a host console and this will bomb out
if ($host.Name -eq "ConsoleHost") {
    Write-AnsibleLog "INFO - setting console input encoding to UTF8 for $ModuleName" "module_wrapper"
    $ps.AddScript('[Console]::InputEncoding = New-Object Text.UTF8Encoding $false').AddStatement() > $null
}

# set the variables
foreach ($variable in $Variables) {
    Write-AnsibleLog "INFO - setting variable '$($variable.Name)' for $ModuleName" "module_wrapper"
    $ps.AddCommand("Set-Variable").AddParameters($variable).AddStatement() > $null
}

# set the environment vars
if ($Environment) {
    foreach ($env_kv in $Environment.GetEnumerator()) {
        Write-AnsibleLog "INFO - setting environment '$($env_kv.Key)' for $ModuleName" "module_wrapper"
        $env_key = $env_kv.Key.Replace("'", "''")
        $env_value = $env_kv.Value.ToString().Replace("'", "''")
        $escaped_env_set = "[System.Environment]::SetEnvironmentVariable('$env_key', '$env_value')"
        $ps.AddScript($escaped_env_set).AddStatement() > $null
    }
}

# import the PS modules
if ($Modules) {
    foreach ($module in $Modules.GetEnumerator()) {
        Write-AnsibleLog "INFO - create module util '$($module.Key)' for $ModuleName" "module_wrapper"
        $module_name = $module.Key
        $module_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($module.Value))
        $ps.AddCommand("New-Module").AddParameters(@{Name=$module_name; ScriptBlock=[ScriptBlock]::Create($module_code)}) > $null
        $ps.AddCommand("Import-Module").AddParameter("WarningAction", "SilentlyContinue") > $null
        $ps.AddCommand("Out-Null").AddStatement() > $null
    }
}

# redefine Write-Host to dump to output instead of failing
# lots of scripts still use it
$ps.AddScript('Function Write-Host($msg) { Write-Output -InputObject $msg }').AddStatement() > $null

# add the scripts and run
foreach ($script in $Scripts) {
    $ps.AddScript($script).AddStatement() > $null
}

if ($Breakpoints.Count -gt 0) {
    Write-AnsibleLog "INFO - adding breakpoint to runspace that will run the modules" "module_wrapper"
    if ($PSVersionTable.PSVersion.Major -eq 3) {
        # The SetBreakpoints method was only added in PowerShell v4+. We need to rely on a private method to
        # achieve the same functionality in this older PowerShell version. This should be removed once we drop
        # support for PowerShell v3.
        $set_method = $ps.Runspace.Debugger.GetType().GetMethod(
            'AddLineBreakpoint', [System.Reflection.BindingFlags]'Instance, NonPublic'
        )
        foreach ($b in $Breakpoints) {
            $set_method.Invoke($ps.Runspace.Debugger, [Object[]]@(,$b)) > $null
        }
    } else {
        $ps.Runspace.Debugger.SetBreakpoints($Breakpoints)
    }
}

Write-AnsibleLog "INFO - start module exec with Invoke() - $ModuleName" "module_wrapper"

# temporarily override the stdout stream and create our own in a StringBuilder
# we use this to ensure there's always an Out pipe and that we capture the
# output for things like async or psrp
$orig_out = [System.Console]::Out
$sb = New-Object -TypeName System.Text.StringBuilder
$new_out = New-Object -TypeName System.IO.StringWriter -ArgumentList $sb
try {
    [System.Console]::SetOut($new_out)
    $module_output = $ps.Invoke()
} catch {
    # uncaught exception while executing module, present a prettier error for
    # Ansible to parse
    $error_params = @{
        Message = "Unhandled exception while executing module"
        ErrorRecord = $_
    }

    # Be more defensive when trying to find the InnerException in case it isn't
    # set. This shouldn't ever be the case but if it is then it makes it more
    # difficult to track down the problem.
    if ($_.Exception.PSObject.Properties.Name -contains "InnerException") {
        $inner_exception = $_.Exception.InnerException
        if ($inner_exception.PSObject.Properties.Name -contains "ErrorRecord") {
            $error_params.ErrorRecord = $inner_exception.ErrorRecord
        }
    }

    Write-AnsibleError @error_params
    $host.SetShouldExit(1)
    return
} finally {
    [System.Console]::SetOut($orig_out)
    $new_out.Dispose()
}

# other types of errors may not throw an exception in Invoke but rather just
# set the pipeline state to failed
if ($ps.InvocationStateInfo.State -eq "Failed" -and $ModuleName -ne "script") {
    $reason = $ps.InvocationStateInfo.Reason
    $error_params = @{
        Message = "Unhandled exception while executing module"
    }

    # The error record should always be set on the reason but this does not
    # always happen on Server 2008 R2 for some reason (probably memory hotfix).
    # Be defensive when trying to get the error record and fall back to other
    # options.
    if ($null -eq $reason) {
        $error_params.Message += ": Unknown error"
    } elseif ($reason.PSObject.Properties.Name -contains "ErrorRecord") {
        $error_params.ErrorRecord = $reason.ErrorRecord
    } else {
        $error_params.Message += ": $($reason.ToString())"
    }

    Write-AnsibleError @error_params
    $host.SetShouldExit(1)
    return
}

Write-AnsibleLog "INFO - module exec ended $ModuleName" "module_wrapper"
$stdout = $sb.ToString()
if ($stdout) {
    Write-Output -InputObject $stdout
}
if ($module_output.Count -gt 0) {
    # do not output if empty collection
    Write-AnsibleLog "INFO - using the output stream for module output - $ModuleName" "module_wrapper"
    Write-Output -InputObject ($module_output -join "`r`n")
}

# we attempt to get the return code from the LASTEXITCODE variable
# this is set explicitly in newer style variables when calling
# ExitJson and FailJson. If set we set the current hosts' exit code
# to that same value
$rc = $ps.Runspace.SessionStateProxy.GetVariable("LASTEXITCODE")
if ($null -ne $rc) {
    Write-AnsibleLog "INFO - got an rc of $rc from $ModuleName exec" "module_wrapper"
    $host.SetShouldExit($rc)
}

# PS3 doesn't properly set HadErrors in many cases, inspect the error stream as a fallback
# with the trap handler that's now in place, this should only write to the output if
# $ErrorActionPreference != "Stop", that's ok because this is sent to the stderr output
# for a user to manually debug if something went horribly wrong
if ($ps.HadErrors -or ($PSVersionTable.PSVersion.Major -lt 4 -and $ps.Streams.Error.Count -gt 0)) {
    Write-AnsibleLog "WARN - module had errors, outputting error info $ModuleName" "module_wrapper"
    # if the rc wasn't explicitly set, we return an exit code of 1
    if ($null -eq $rc) {
        $host.SetShouldExit(1)
    }

    # output each error to the error stream of the current pipeline
    foreach ($err in $ps.Streams.Error) {
        $error_msg = Format-AnsibleException -ErrorRecord $err

        # need to use the current hosts's UI class as we may not have
        # a console to write the stderr to, e.g. psrp
        Write-AnsibleLog "WARN - error msg for for $($ModuleName):`r`n$error_msg" "module_wrapper"
        $host.UI.WriteErrorLine($error_msg)
    }
}
