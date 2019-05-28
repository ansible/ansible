#!powershell

# Copyright: (c) 2019, Jose Angel Munoz (@imjoseangel) <josea.munoz@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options             = @{
        state       = @{ type = "str"; choices = "shutdown", "suspend", "hibernate"; default = "suspend" }
        force       = @{ type = "bool"; default = $false }
        disablewake = @{ type = "bool"; default = $true }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$state = $module.Params.state
$force = $module.Params.force
$disablewake = $module.Params.disablewake

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

        $module.Warn("Can not change to state $PowerState on Windows Servers")

    }
    else {

        if ($PSCmdlet.ShouldProcess("Target", "Operation")) {

            try {

                Add-Type -AssemblyName System.Windows.Forms;
                [System.Windows.Forms.Application]::SetSuspendState($PowerState, $Force, $DisableWake);
            }
            catch [System.InvalidOperationException], [System.Security.SecurityException] {

                $module.FailJson("Could not Add Windows Forms Type")
            }

            $module.Result.changed = $true
        }
        else {
            try {

                Add-Type -AssemblyName System.Windows.Forms;
            }
            catch [System.InvalidOperationException], [System.Security.SecurityException] {

                $module.FailJson("Could not Add Windows Forms Type")
            }

            $module.Result.changed = $true
            $module.Result.check_mode = $true
        }
    }
}

if (($state -eq "suspend") -or ($state -eq "hibernate")) {

    try {

        Set-PowerState -PowerState $state -Force:$force -DisableWake:$disablewake -WhatIf:$module.CheckMode
    }
    catch [System.InvalidOperationException] {

        $module.FailJson("Could not change to state $state")
    }
}

elseif ($state -eq "shutdown") {
    try {

        Stop-Computer -Force:$force -WhatIf:$module.CheckMode
        $module.Result.changed = $true

        if ($module.CheckMode) {

            $module.Result.check_mode = $true
        }
    }

    catch [System.InvalidOperationException] {

        $module.FailJson("Could not change to state $state")
    }
}

$module.ExitJson()
