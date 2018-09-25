param(
    [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Payload
)

#Requires -Module Ansible.ModuleUtils.AddType
#AnsibleRequires -Wrapper module_wrapper

Write-AnsibleLog "INFO - starting module_csharp_wrapper" "module_csharp_wrapper"

$module_name = $Payload.module_args["_ansible_module_name"]
Write-AnsibleLog "INFO - building module payload for '$module_name'" "module_csharp_wrapper"

# import the AddType module util
$add_type_b64 = $Payload.powershell_modules["Ansible.ModuleUtils.AddType"]
$add_type = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($add_type_b64))
New-Module -Name Ansible.ModuleUtils.AddType -ScriptBlock ([ScriptBlock]::Create($add_type)) | Import-Module > $null

# compile the module code as well as any C# module utils passed in from the
# controller
$csharp_utils = [System.Collections.ArrayList]@([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.module_entry)))
foreach ($csharp_util in $Payload.csharp_utils_module) {
    Write-AnsibleLog "INFO - adding $csharp_util to list of C# references to compile" "module_csharp_wrapper"
    $util_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.csharp_utils[$csharp_util]))
    $csharp_utils.Add($util_code) > $null
}

Write-AnsibleLog "INFO - compiling module code for execution" "module_csharp_wrapper"
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
    Write-AnsibleError -Message "failed to find Main method class that starts with Ansible.Module in the loaded types: $($loaded_types.FullName -join ", ")"
    $host.SetShouldExit(1)
    return
}

$variables = [System.Collections.ArrayList]@(
    @{ Name = "complex_args"; Value = $Payload.module_args; Scope = "Global" },
    @{ Name = "module_type"; Value = $module_type }
)

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

# get the common module_wrapper code and invoke that to run the module
$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.module_wrapper))
$entrypoint = [ScriptBlock]::Create($entrypoint)

try {
    &$entrypoint -Scripts $script -Variables $variables -Environment $Payload.environment -ModuleName $module_name
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

Write-AnsibleLog "INFO - ending module_csharp_wrapper" "module_csharp_wrapper"
