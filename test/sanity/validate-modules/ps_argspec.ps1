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
$powershell.AddScript($module_code) > $null
$powershell.Invoke() > $null

if ($powershell.HadErrors) {
    $powershell.Streams.Error
    exit 1
}
