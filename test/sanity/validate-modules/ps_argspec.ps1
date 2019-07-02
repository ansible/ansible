#!/usr/bin/env pwsh
#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

$module_path = $args[0]
if (-not $module_path) {
    Write-Error -Message "No module specified."
    exit 1
}

# Check if the path is relative and get the full path to the module
if (-not ([System.IO.Path]::IsPathRooted($module_path))) {
    $module_path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($module_path)
}

if (-not (Test-Path -LiteralPath $module_path -PathType Leaf)) {
    Write-Error -Message "The module at '$module_path' does not exist."
    exit 1
}

$dummy_ansible_basic = @'
using System;
using System.Collections;
using System.Management.Automation;

namespace Ansible.Basic
{
    public class AnsibleModule
    {
        public AnsibleModule(string[] args, IDictionary argumentSpec)
        {
            PSObject rawOut = ScriptBlock.Create("ConvertTo-Json -InputObject $args[0] -Depth 99 -Compress").Invoke(argumentSpec)[0];
            Console.WriteLine(rawOut.BaseObject.ToString());
            ScriptBlock.Create("Set-Variable -Name LASTEXITCODE -Value 0 -Scope Global; exit 0").Invoke();
        }

        public static AnsibleModule Create(string[] args, IDictionary argumentSpec)
        {
            return new AnsibleModule(args, argumentSpec);
        }
    }
}
'@
Add-Type -TypeDefinition $dummy_ansible_basic

$module_code = Get-Content -LiteralPath $module_path -Raw

$powershell = [PowerShell]::Create()
$powershell.Runspace.SessionStateProxy.SetVariable("ErrorActionPreference", "Stop")

# Load the PowerShell module utils as the module may be using them to refer to shared module options
# FUTURE: Lookup utils in the role or collection's module_utils dir based on #AnsibleRequires
$script_requirements = [ScriptBlock]::Create($module_code).Ast.ScriptRequirements
$required_modules = @()
if ($null -ne $script_requirements) {
    $required_modules = $script_requirements.RequiredModules
}
foreach ($required_module in $required_modules) {
    if (-not $required_module.Name.StartsWith('Ansible.ModuleUtils.')) {
        continue
    }

    $module_util_path = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($module_path, '..', '..', '..',
        'module_utils', 'powershell', "$($required_module.Name).psm1"))
    if (-not (Test-Path -LiteralPath $module_util_path -PathType Leaf)) {
        # Failed to find path, just silently ignore for now and hope for the best
        continue
    }

    $module_util_sb = [ScriptBlock]::Create((Get-Content -LiteralPath $module_util_path -Raw))
    $powershell.AddCommand('New-Module').AddParameters(@{
        Name = $required_module.Name
        ScriptBlock = $module_util_sb
    }) > $null
    $powershell.AddCommand('Import-Module').AddParameter('WarningAction', 'SilentlyContinue') > $null
    $powershell.AddCommand('Out-Null').AddStatement() > $null

}

$powershell.AddScript($module_code) > $null
$powershell.Invoke() > $null

if ($powershell.HadErrors) {
    $powershell.Streams.Error
    exit 1
}
