#!powershell

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Facts
#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

# FUTURE: consider action wrapper to manage reboots and credential changes

Function Ensure-Prereqs {
    $gwf = Get-WindowsFeature AD-Domain-Services
    If($gwf.InstallState -ne "Installed") {
        $result.changed = $true

        If($check_mode) {
            Exit-Json $result
        }
        $awf = Add-WindowsFeature AD-Domain-Services
        # FUTURE: check if reboot necessary
    }
}

$parsed_args = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam $parsed_args "_ansible_check_mode" -default $false
$dns_domain_name = Get-AnsibleParam $parsed_args "dns_domain_name" -failifempty $true
$safe_mode_admin_password = Get-AnsibleParam $parsed_args "safe_mode_password" -failifempty $true
$database_path = Get-AnsibleParam $parsed_args "database_path" -type "path"
$sysvol_path = Get-AnsibleParam $parsed_args "sysvol_path" -type "path"

$forest = $null

# FUTURE: support down to Server 2012?
If([System.Environment]::OSVersion.Version -lt [Version]"6.3.9600.0") {
    Fail-Json -message "win_domain requires Windows Server 2012R2 or higher"
}

$result = @{changed=$false; reboot_required=$false}

# FUTURE: any sane way to do the detection under check-mode *without* installing the feature?

Ensure-Prereqs

Try {
    $forest = Get-ADForest $dns_domain_name -ErrorAction SilentlyContinue
}
Catch { }

If(-not $forest) {
    $result.changed = $true

    If(-not $check_mode) {
        $sm_cred = ConvertTo-SecureString $safe_mode_admin_password -AsPlainText -Force

        $install_forest_args = @{
            DomainName=$dns_domain_name;
            SafeModeAdministratorPassword=$sm_cred;
            Confirm=$false;
            SkipPreChecks=$true;
            InstallDNS=$true;
            NoRebootOnCompletion=$true;
        }
        if ($database_path) {
            $install_forest_args.DatabasePath = $database_path
        }
        if ($sysvol_path) {
            $install_forest_args.SysvolPath = $sysvol_path
        }

        $iaf = Install-ADDSForest @install_forest_args

        $result.reboot_required = $iaf.RebootRequired
        Set-AnsibleFact -obj $result -name "ansible_reboot_pending" -value $result.reboot_required
    }
}

Exit-Json $result
