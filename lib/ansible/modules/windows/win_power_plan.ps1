#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        name = @{ type = "str"; required = $true }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name

$module.Result.power_plan_name = $name
$module.Result.power_plan_enabled = $null
$module.Result.all_available_plans = $null

Add-CSharpType -References @"
using System;
using System.Runtime.InteropServices;

namespace Ansible.WinPowerPlan
{
    public enum AccessFlags : uint
    {
        AccessScheme = 16,
        AccessSubgroup = 17,
        AccessIndividualSetting = 18
    }

    public class NativeMethods
    {
        [DllImport("Kernel32.dll", SetLastError = true)]
        public static extern IntPtr LocalFree(
            IntPtr hMen);

        [DllImport("PowrProf.dll")]
        public static extern UInt32 PowerEnumerate(
            IntPtr RootPowerKey,
            IntPtr SchemeGuid,
            IntPtr SubGroupOfPowerSettingsGuid,
            AccessFlags AccessFlags,
            UInt32 Index,
            IntPtr Buffer,
            ref UInt32 BufferSize);

        [DllImport("PowrProf.dll")]
        public static extern UInt32 PowerGetActiveScheme(
            IntPtr UserRootPowerKey,
            out IntPtr ActivePolicyGuid);

        [DllImport("PowrProf.dll")]
        public static extern UInt32 PowerReadFriendlyName(
            IntPtr RootPowerKey,
            Guid SchemeGuid,
            IntPtr SubGroupOfPowerSettingsGuid,
            IntPtr PowerSettingGuid,
            IntPtr Buffer,
            ref UInt32 BufferSize);

        [DllImport("PowrProf.dll")]
        public static extern UInt32 PowerSetActiveScheme(
            IntPtr UserRootPowerKey,
            Guid SchemeGuid);
    }
}
"@

Function Get-LastWin32ErrorMessage {
    param([Int]$ErrorCode)
    $exp = New-Object -TypeName System.ComponentModel.Win32Exception -ArgumentList $ErrorCode
    $error_msg = "{0} - (Win32 Error Code {1} - 0x{1:X8})" -f $exp.Message, $ErrorCode
    return $error_msg
}

Function Get-PlanName {
    param([Guid]$Plan)

    $buffer_size = 0
    $buffer = [IntPtr]::Zero
    [Ansible.WinPowerPlan.NativeMethods]::PowerReadFriendlyName([IntPtr]::Zero, $Plan, [IntPtr]::Zero, [IntPtr]::Zero,
        $buffer, [ref]$buffer_size) > $null

    $buffer = [System.Runtime.InteropServices.Marshal]::AllocHGlobal($buffer_size)
    try {
        $res = [Ansible.WinPowerPlan.NativeMethods]::PowerReadFriendlyName([IntPtr]::Zero, $Plan, [IntPtr]::Zero,
            [IntPtr]::Zero, $buffer, [ref]$buffer_size)

        if ($res -ne 0) {
            $err_msg = Get-LastWin32ErrorMessage -ErrorCode $res
            $module.FailJson("Failed to get name for power scheme $Plan - $err_msg")
        }

        return [System.Runtime.InteropServices.Marshal]::PtrToStringUni($buffer)
    } finally {
        [System.Runtime.InteropServices.Marshal]::FreeHGlobal($buffer)
    }
}

Function Get-PowerPlans {
    $plans = @{}

    $i = 0
    while ($true) {
        $buffer_size = 0
        $buffer = [IntPtr]::Zero
        $res = [Ansible.WinPowerPlan.NativeMethods]::PowerEnumerate([IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero,
            [Ansible.WinPowerPlan.AccessFlags]::AccessScheme, $i, $buffer, [ref]$buffer_size)

        if ($res -eq 259) {
            # 259 == ERROR_NO_MORE_ITEMS, there are no more power plans to enumerate
            break
        } elseif ($res -notin @(0, 234)) {
            # 0 == ERROR_SUCCESS and 234 == ERROR_MORE_DATA
            $err_msg = Get-LastWin32ErrorMessage -ErrorCode $res
            $module.FailJson("Failed to get buffer size on local power schemes at index $i - $err_msg")
        }

        $buffer = [System.Runtime.InteropServices.Marshal]::AllocHGlobal($buffer_size)
        try {
            $res = [Ansible.WinPowerPlan.NativeMethods]::PowerEnumerate([IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero,
                [Ansible.WinPowerPlan.AccessFlags]::AccessScheme, $i, $buffer, [ref]$buffer_size)

            if ($res -eq 259) {
                # Server 2008 does not return 259 in the first call above so we do an additional check here
                break
            } elseif ($res -notin @(0, 234, 259)) {
                $err_msg = Get-LastWin32ErrorMessage -ErrorCode $res
                $module.FailJson("Failed to enumerate local power schemes at index $i - $err_msg")
            }
            $scheme_guid = [System.Runtime.InteropServices.Marshal]::PtrToStructure($buffer, [Type][Guid])
        } finally {
            [System.Runtime.InteropServices.Marshal]::FreeHGlobal($buffer)
        }
        $scheme_name = Get-PlanName -Plan $scheme_guid
        $plans.$scheme_name = $scheme_guid

        $i += 1
    }

    return $plans
}

Function Get-ActivePowerPlan {
    $buffer = [IntPtr]::Zero
    $res = [Ansible.WinPowerPlan.NativeMethods]::PowerGetActiveScheme([IntPtr]::Zero, [ref]$buffer)
    if ($res -ne 0) {
        $err_msg = Get-LastWin32ErrorMessage -ErrorCode $res
        $module.FailJson("Failed to get the active power plan - $err_msg")
    }

    try {
        $active_guid = [System.Runtime.InteropServices.Marshal]::PtrToStructure($buffer, [Type][Guid])
    } finally {
        [Ansible.WinPowerPlan.NativeMethods]::LocalFree($buffer) > $null
    }

    return $active_guid
}

Function Set-ActivePowerPlan {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([Guid]$Plan)

    $res = 0
    if ($PSCmdlet.ShouldProcess($Plan, "Set Power Plan")) {
        $res = [Ansible.WinPowerPlan.NativeMethods]::PowerSetActiveScheme([IntPtr]::Zero, $Plan)
    }

    if ($res -ne 0) {
        $err_msg = Get-LastWin32ErrorMessage -ErrorCode $res
        $module.FailJson("Failed to set the active power plan to $Plan - $err_msg")
    }
}

# Get all local power plans and the current active plan
$plans = Get-PowerPlans
$active_plan = Get-ActivePowerPlan
$module.Result.all_available_plans = @{}
foreach ($plan_info in $plans.GetEnumerator()) {
    $module.Result.all_available_plans.($plan_info.Key) = $plan_info.Value -eq $active_plan
}

if ($name -notin $plans.Keys) {
    $module.FailJson("Defined power_plan: ($name) is not available")
}
$plan_guid = $plans.$name
$is_active = $active_plan -eq $plans.$name
$module.Result.power_plan_enabled = $is_active

if (-not $is_active) {
    Set-ActivePowerPlan -Plan $plan_guid -WhatIf:$module.CheckMode
    $module.Result.changed = $true
    $module.Result.power_plan_enabled = $true
    foreach ($plan_info in $plans.GetEnumerator()) {
        $is_active = $plan_info.Value -eq $plan_guid
        $module.Result.all_available_plans.($plan_info.Key) = $is_active
    }
}

$module.ExitJson()

