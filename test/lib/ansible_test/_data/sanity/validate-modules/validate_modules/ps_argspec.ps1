#!/usr/bin/env pwsh
#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

$manifest = ConvertFrom-Json -InputObject $args[0] -AsHashtable
if (-not $manifest.Contains('module_path') -or -not $manifest.module_path) {
    Write-Error -Message "No module specified."
    exit 1
}
$module_path = $manifest.module_path

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

# Load the PowerShell module utils as the module may be using them to refer to shared module options. Currently we
# can only load the PowerShell utils due to cross platform compatiblity issues.
if ($manifest.Contains('ps_utils')) {
    foreach ($util_info in $manifest.ps_utils.GetEnumerator()) {
        $util_name = $util_info.Key
        $util_path = $util_info.Value

        if (-not (Test-Path -LiteralPath $util_path -PathType Leaf)) {
            # Failed to find the util path, just silently ignore for now and hope for the best.
            continue
        }

        $util_sb = [ScriptBlock]::Create((Get-Content -LiteralPath $util_path -Raw))
        $powershell.AddCommand('New-Module').AddParameters(@{
            Name = $util_name
            ScriptBlock = $util_sb
        }) > $null
        $powershell.AddCommand('Import-Module').AddParameter('WarningAction', 'SilentlyContinue') > $null
        $powershell.AddCommand('Out-Null').AddStatement() > $null
    }
}

$powershell.AddScript($module_code) > $null
$powershell.Invoke() > $null

if ($powershell.HadErrors) {
    $powershell.Streams.Error
    exit 1
}
