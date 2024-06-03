# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Payload
)

#AnsibleRequires -Wrapper module_wrapper

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting module_powershell_wrapper" "module_powershell_wrapper"

$module_name = $Payload.module_args["_ansible_module_name"]
Write-AnsibleLog "INFO - building module payload for '$module_name'" "module_powershell_wrapper"

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

    # We use a fake module object to capture warnings
    $fake_module = [PSCustomObject]@{
        Tmpdir = $new_tmp
        Verbosity = 3
    }
    $warning_func = New-Object -TypeName System.Management.Automation.PSScriptMethod -ArgumentList Warn, {
        param($message)
        $Payload.module_args._ansible_exec_wrapper_warnings.Add($message)
    }
    $fake_module.PSObject.Members.Add($warning_func)
    Add-CSharpType -References $csharp_utils -AnsibleModule $fake_module
}

if ($Payload.ContainsKey("coverage") -and $null -ne $host.Runspace -and $null -ne $host.Runspace.Debugger) {
    $entrypoint = $payload.coverage_wrapper

    $params = @{
        Payload = $Payload
    }
}
else {
    # get the common module_wrapper code and invoke that to run the module
    $module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.module_entry))
    $variables = [System.Collections.ArrayList]@(@{ Name = "complex_args"; Value = $Payload.module_args; Scope = "Global" })
    $entrypoint = $Payload.module_wrapper

    $params = @{
        Scripts = @($script:common_functions, $module)
        Variables = $variables
        Environment = $Payload.environment
        Modules = $Payload.powershell_modules
        ModuleName = $module_name
    }
}

$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($entrypoint))
$entrypoint = [ScriptBlock]::Create($entrypoint)

try {
    &$entrypoint @params
}
catch {
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
