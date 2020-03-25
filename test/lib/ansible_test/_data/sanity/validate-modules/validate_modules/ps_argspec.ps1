#!/usr/bin/env pwsh
#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

Function Resolve-CircularReference {
    <#
    .SYNOPSIS
    Removes known types that cause a circular reference in their json serialization.

    .PARAMETER Hash
    The hash to scan for circular references
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [System.Collections.IDictionary]
        $Hash
    )

    foreach ($key in [String[]]$Hash.Keys) {
        $value = $Hash[$key]
        if ($value -is [System.Collections.IDictionary]) {
            Resolve-CircularReference -Hash $value
        } elseif ($value -is [Array] -or $value -is [System.Collections.IList]) {
            $values = @(foreach ($v in $value) {
                if ($v -is [System.Collections.IDictionary]) {
                    Resolve-CircularReference -Hash $v
                }
                ,$v
            })
            $Hash[$key] = $values
        } elseif ($value -is [delegate]) {
            # Type can be set to a delegate function which defines it's own type. For the documentation we just
            # reflection that as raw
            if ($key -eq 'type') {
                $Hash[$key] = 'raw'
            } else {
                $Hash[$key] = $value.ToString()  # Shouldn't ever happen but just in case.
            }
        }
    }
}

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
            ScriptBlock.Create("Set-Variable -Name arg_spec -Value $args[0] -Scope Global; exit 0"
                ).Invoke(new Object[] { argumentSpec });
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

$arg_spec = $powershell.Runspace.SessionStateProxy.GetVariable('arg_spec')
Resolve-CircularReference -Hash $arg_spec

ConvertTo-Json -InputObject $arg_spec -Compress -Depth 99