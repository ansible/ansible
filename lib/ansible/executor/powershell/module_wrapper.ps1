param(
    [Parameter(Mandatory=$true)][Hashtable]$Payload
)

$ErrorActionPreference = "Stop"

Function Invoke-AnsibleModule {
    <#
    .SYNOPSIS
    Invokes an Ansible module in a new Runspace. This cmdlet will output the
    module's output and write any errors to the error stream of the current
    host.

    .PARAMETER Script
    [String] The main script to run, this could be the PowerShell module or a
    stub to invoke an added C# type.

    .PARAMETER Variables
    [System.Collections.ArrayList] The variables to set in the new Pipeline.
    Each value is a hashtable that contains the parameters to use with
    Set-Variable;
        Name: the name of the variable to set
        Value: the value of the variable to set
        Scope: the scope of the variable

    .PARAMETER Environment
    [Hashtable] A Dictionary of environment key/values to set in the new
    Pipeline.

    .PARAMETER Modules
    [Hashtable] A Dictionary of PowerShell modules to import into the new
    Pipeline. The key is the name of the module and the value is a base64 string
    of the module util code.
    #>
    param(
        [String]$Script,
        [System.Collections.ArrayList]$Variables,
        [Hashtable]$Environment,
        [Hashtable]$Modules,
        [String]$ModuleName
    )

    Write-AnsibleLog "INFO - creating new Runspace for $ModuleName" "module_wrapper"
    $rs = [RunspaceFactory]::CreateRunspace()
    $rs.Open()

    try {
        Write-AnsibleLog "INFO - creating new PowerShell pipeline for $ModuleName" "module_wrapper"
        $ps = [PowerShell]::Create()
        $ps.Runspace = $rs

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

        # load the common functions
        $ps.AddScript($script:common_functions).AddStatement() > $null

        # redefine Write-Host to dump to output instead of failing
        # lots of scripts still use it
        $ps.AddScript('Function Write-Host($msg) { Write-Output -InputObject $msg }').AddStatement() > $null

        # add the script and run
        $ps.AddScript($Script) > $null

        Write-AnsibleLog "INFO - start module exec with Invoke() - $ModuleName" "module_wrapper"
        $module_output = $ps.Invoke()
        Write-AnsibleLog "INFO - module exec ended $ModuleName" "module_wrapper"
        $ansible_output = $rs.SessionStateProxy.GetVariable("_ansible_output")

        # _ansible_output is a special var used by new modules to store the
        # output JSON. If set, we consider the ExitJson and FailJson methods
        # called and assume it contains the JSON we want and the pipeline
        # output won't contain anything of note
        # TODO: should we validate it or use a random variable name?
        # TODO: should we use this behaviour for all new modules and not just
        # ones running under psrp
        if ($null -ne $ansible_output) {
            Write-AnsibleLog "INFO - using the _ansible_output variable for module output - $ModuleName" "module_wrapper"
            Write-Output -InputObject $ansible_output.ToString()
        } elseif ($module_output.Count -gt 0) {
            # do not output if empty collection
            Write-AnsibleLog "INFO - using the output stream for module output - $ModuleName" "module_wrapper"
            Write-Output -InputObject ($module_output -join "`r`n")
        }

        # we attempt to get the return code from the LASTEXITCODE variable
        # this is set explicitly in newer style variables when calling
        # ExitJson and FailJson. If set we set the current hosts' exit code
        # to that same value
        $rc = $rs.SessionStateProxy.GetVariable("LASTEXITCODE")
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
    } finally {
        $rs.Close()
    }
}

Write-AnsibleLog "INFO - starting module_wrapper" "module_wrapper"

$module_name = $Payload.module_args["_ansible_module_name"]
Write-AnsibleLog "INFO - building module payload for '$module_name'" "module_wrapper"

# both module types rely on the complex_args variable to be set that
# contains the module args from Ansible
$variables = [System.Collections.ArrayList]@(@{Name="complex_args"; Value=$Payload.module_args; Scope="Global"})

# build a collection of C# utils for the module
$csharp_utils = [System.Collections.ArrayList]@()
foreach ($csharp_util in $Payload.csharp_utils_module) {
    Write-AnsibleLog "INFO - adding $csharp_util to list of C# references to compile" "module_wrapper"
    $csharp_utils.Add($Payload.csharp_utils[$csharp_util]) > $null
}

if ($Payload.substyle -in @("powershell", "script")) {
    Write-AnsibleLog "INFO - creating wrapper for a PowerShell module" "module_wrapper"
    $module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.module_entry))

    # add a trap to the end of the PowerShell module to help catch any
    # uncaught exceptions and output a better error message
    $script = $module + "`r`n`r`n" + @'
trap {
    $excp = $_

    $old_ps_style = Get-Command -Name Fail-Json -CommandType Function -ErrorAction SilentlyContinue
    $new_ps_module = Get-Variable | Where-Object { $null -ne $_.Value -and $_.Value.GetType().FullName -eq "Ansible.Basic.AnsibleModule" }
    if ($old_ps_style) {
        $_result = Get-Variable -Name result -ErrorAction SilentlyContinue
        if (-not $_result) {
            $_result = @{}
        } else {
            $_result = $_result.Value
        }
        $_result.exception = (Format-AnsibleException -ErrorRecord $excp)
        Fail-Json -obj $_result -message "Unhandled exception while executing module: $($excp.Exception.Message)"
    } elseif ($new_ps_module) {
        if ($new_ps_module -is [Array]) {
            $_ansible_module = $new_ps_module | Where-Object { $_.Name -eq "ansible_module" }
            if ($_ansible_module) {
                $_ansible_module = $ansible_module.Value
            } else {
                $_ansible_module = $new_ps_module[0].Value
            }
        } else {
            $_ansible_module = $new_ps_module.Value
        }
        $error_msg = "Unhandled exception while executing module: $($excp.Exception.Message)"
        $_ansible_module.FailJson($error_msg, $excp)
    }

    break
}
'@
    # add any C# references so the module does not have to do so
    $new_tmp = [System.Environment]::ExpandEnvironmentVariables($Payload.module_args["_ansible_remote_tmp"])
    Add-CSharpType -References $csharp_utils -TempPath $new_tmp -IncludeDebugInfo

    try {
        Invoke-AnsibleModule -Script $script -Variables $variables -Environment $Payload.environment `
            -Modules $Payload.powershell_modules -ModuleName $module_name
    } catch {
        # failed to invoke the PowerShell module, capture the exception and
        # output a pretty error for Ansible to parse
        $result = @{
            msg = "Failed to invoke PowerShell module: $($_.Exception.Message)"
            failed = $true
            exception = (Format-AnsibleException -ErrorRecord $_)
        }
        Write-Output -InputObject (ConvertTo-Json -InputObject $result -Depth 99 -Compress)
        $host.SetShouldExit(1)
    }
} else {
    Write-AnsibleLog "INFO - creating module wrapper for a CSharp module" "module_wrapper"
    # compile the C# module and all the C# utils. This allows the Runspace to
    # invoke the C# module
    $csharp_utils.Insert(0, $Payload.module_entry)
    $new_tmp = [System.Environment]::ExpandEnvironmentVariables($Payload.module_args["_ansible_remote_tmp"])
    $loaded_assembly = Add-CSharpType -References $csharp_utils -TempPath $new_tmp -PassThru -IncludeDebugInfo
    $loaded_types = $loaded_assembly.GetTypes()

    # attempt to find the static Main() method in the loaded classes
    $module_type = $null
    $param_types = [Type[]]@([String[]])
    $binding_flags = [System.Reflection.BindingFlags]"InvokeMethod, Public, Static"
    foreach ($type in $loaded_types) {
        if ($type.FullName.StartsWith("Ansible.Module.")) {
            $main_method = $type.GetMethod("Main", $binding_flags, $null, $param_types, $null)
            if ($null -ne $main_method) {
                $module_type = $type
                break
            }
        }
    }

    if ($null -eq $module_type) {
        $result = @{
            msg = "failed to find Main method class that starts with Ansible.Module in the loaded types: $($loaded_types.FullName -join ", ")"
            failed = $true
        }
        Write-Output -InputObject (ConvertTo-Ansible -InputObject $result -Depth 99 -Compress)
        $host.SetShouldExit(1)
        return
    }

    $variables.Add(@{Name="module_type"; Value=$module_type}) > $null
    $script = @'
try {
    $module_type::Main([String[]]@())
} catch {
    $result = @{
        msg = "Unhandled exception while executing C# module: $($_.Exception.InnerException.Message)"
        failed = $true
        exception = $_.Exception.InnerException.ToString()
    }
    Write-Output -InputObject (ConvertTo-Json -InputObject $result -Depth 99 -Compress)
    $host.SetShouldExit(1)
}
'@

    try {
        Invoke-AnsibleModule -Script $script -Variables $variables -Environment $Payload.environment `
            -ModuleName $module_name
    } catch {
        # failed to invoke the C# module, capture the exception and
        # output a pretty error for Ansible to parse
        $result = @{
            msg = "Failed to invoke C# module: $($_.Exception.Message)"
            failed = $true
            exception = (Format-AnsibleException -ErrorRecord $_)
        }
        Write-Output -InputObject (ConvertTo-Json -InputObject $result -Depth 99 -Compress)
        $host.SetShouldExit(1)
    }
}

Write-AnsibleLog "INFO - ending module_wrapper" "module_wrapper"
