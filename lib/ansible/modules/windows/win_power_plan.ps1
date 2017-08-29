#!powershell

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy.psm1

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

# these are your module parameters
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true

Function Get-PowerPlans {
Param ($PlanName)
    If (!$PlanName) {
        Get-CimInstance -Name root\cimv2\power -Class win32_PowerPlan | Select ElementName,IsActive |
        Foreach -begin { $ht=@{} } -process { $ht."$($_.ElementName)" = $_.IsActive } -end {$ht}
    }
    Else {
        Get-CimInstance -Name root\cimv2\power -Class win32_PowerPlan -Filter "ElementName = '$PlanName'"
    }
}

#fail if older than 2008r2...need to do it here before Get-PowerPlans function runs further down
If ( (gcim Win32_OperatingSystem).version -lt 6.1)
{
    $result = @{
        changed = $false
        power_plan_name = $name
        power_plan_enabled = $null
        all_available_plans = $null
    }
    Fail-Json $result "The win_power_plan Ansible module is only available on Server 2008r2 (6.1) and newer"
}

$result = @{
    changed = $false
    power_plan_name = $name
    power_plan_enabled = (Get-PowerPlans $name).isactive
    all_available_plans = Get-PowerPlans
}

$all_available_plans = Get-PowerPlans

#Terminate if plan is not found on the system
If (! ($all_available_plans.ContainsKey($name)) )
{
    Fail-Json $result "Defined power_plan: ($name) is not available"
}

#If true, means plan is already active and we exit here with changed: false
#If false, means plan is not active and we move down to enable
#Since the results here are the same whether check mode or not, no specific handling is required
#for check mode.
If ( $all_available_plans.item($name) )
{
    Exit-Json $result
}
Else
{
    Try {
        $Null = Invoke-CimMethod -InputObject (Get-PowerPlans $name) -MethodName Activate -ea Stop -WhatIf:$check_mode
    }
    Catch {
        $result.power_plan_enabled = (Get-PowerPlans $name).isactive
        $result.all_available_plans = Get-PowerPlans
        Fail-Json $result "Failed to set the new plan: $($_.Exception.Message)"
    }

    #set success parameters and exit
    $result.changed = $true
    $result.power_plan_enabled = (Get-PowerPlans $name).isactive
    $result.all_available_plans = Get-PowerPlans
    Exit-Json $result
}

