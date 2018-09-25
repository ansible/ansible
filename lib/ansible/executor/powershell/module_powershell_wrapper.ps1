param(
    [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Payload
)

#AnsibleRequires -Wrapper module_wrapper

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting module_powershell_wrapper" "module_powershell_wrapper"

$module_name = $Payload.module_args["_ansible_module_name"]
Write-AnsibleLog "INFO - building module payload for '$module_name'" "module_powershell_wrapper"

$variables = [System.Collections.ArrayList]@(@{Name="complex_args"; Value=$Payload.module_args; Scope="Global"})

# compile any C# module utils passed in from the controller, Add-CSharpType is
# automatically added to the payload manifest if any csharp util is set
$csharp_utils = [System.Collections.ArrayList]@()
foreach ($csharp_util in $Payload.csharp_utils_module) {
    Write-AnsibleLog "INFO - adding $csharp_util to list of C# references to compile" "module_powershell_wrapper"
    $util_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.csharp_utils[$csharp_util]))
    $csharp_utils.Add($util_code) > $null
}
if ($csharp_utils.Count -gt 0) {
    $add_type_b64 = $Payload.powershell_modules["Ansible.ModuleUtils.AddType"]
    $add_type = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($add_type_b64))
    New-Module -Name Ansible.ModuleUtils.AddType -ScriptBlock ([ScriptBlock]::Create($add_type)) | Import-Module > $null

    # add any C# references so the module does not have to do so
    $new_tmp = [System.Environment]::ExpandEnvironmentVariables($Payload.module_args["_ansible_remote_tmp"])
    Add-CSharpType -References $csharp_utils -TempPath $new_tmp -IncludeDebugInfo
}

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

# get the common module_wrapper code and invoke that to run the module
$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.module_wrapper))
$entrypoint = [ScriptBlock]::Create($entrypoint)

try {
    &$entrypoint -Scripts $script:common_functions, $script -Variables $variables `
        -Environment $Payload.environment -Modules $Payload.powershell_modules `
        -ModuleName $module_name
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

Write-AnsibleLog "INFO - ending module_powershell_wrapper" "module_powershell_wrapper"
