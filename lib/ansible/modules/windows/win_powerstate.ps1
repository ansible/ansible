#!powershell

# Copyright: (c) 2019, Jose Angel Munoz (@imjoseangel) <josea.munoz@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$powerstate = Get-AnsibleParam -obj $params -name "powerstate" -type "str" -default "suspend" -validateset "shutdown", "suspend", "hibernate"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
$disablewake = Get-AnsibleParam -obj $params -name "disablewake" -type "bool" -default $true

$result = @{
    changed     = $false
    module_args = @{
        powerstate  = $powerstate
        force       = $force
        disablewake = $disablewake
    }
}

function Set-PowerState {

    [CmdletBinding(SupportsShouldProcess = $true)]
    param (

        [parameter(Mandatory = $True)]
        [ValidateSet("suspend", "hibernate")]$PowerState,

        [parameter(Mandatory = $False)]
        [switch]$Force,

        [parameter(Mandatory = $False)]
        [switch]$DisableWake
    )

    if ((Get-CimInstance -Class Win32_OperatingSystem).Caption -match "\sServer\s") {

        Exit-Json -obj $result -message "Can not change to state $PowerState on Windows Servers"
    }
    else {

        if ($PSCmdlet.ShouldProcess("Target", "Operation")) {

            try {

                Add-Type -AssemblyName System.Windows.Forms;
                [System.Windows.Forms.Application]::SetSuspendState($PowerState, $Force, $DisableWake);
            }
            catch [System.InvalidOperationException], [System.Security.SecurityException] {

                Fail-Json $result -message "Could not Add Windows Forms Type"
            }

            $result.changed = $true
        }
        else {
            try {

                Add-Type -AssemblyName System.Windows.Forms;
            }
            catch [System.InvalidOperationException], [System.Security.SecurityException] {

                Fail-Json $result -message "Could not Add Windows Forms Type"
            }

            $result.changed = $true
            $result.module_args.check_mode = $true
        }
    }
}

if (($powerstate -eq "suspend") -or ($powerstate -eq "hibernate")) {

    try {

        Set-PowerState -PowerState $powerstate -Force:$force -DisableWake:$disablewake -WhatIf:$check_mode
    }
    catch [System.InvalidOperationException] {

        Fail-Json -obj $result -message "Could not change to state $powerstate"
    }
}

elseif ($powerstate -eq "shutdown") {
    try {

        Stop-Computer -Force:$force -WhatIf:$check_mode
        $result.changed = $true

        if ($check_mode) {

            $result.module_args.check_mode = $true
        }
    }

    catch [System.InvalidOperationException] {

        Fail-Json -obj $result -message "Could not change to state $powerstate"
    }
}

Exit-Json -obj $result
