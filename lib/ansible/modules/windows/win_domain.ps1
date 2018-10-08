#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

# FUTURE: Consider action wrapper to manage reboots and credential changes

Function Ensure-Prereqs {
    $gwf = Get-WindowsFeature AD-Domain-Services
    If($gwf.InstallState -ne "Installed") {
        $result.changed = $true

        If($check_mode) {
            Exit-Json $result
        }
        $awf = Add-WindowsFeature AD-Domain-Services
        # FUTURE: Check if reboot necessary
    }
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false
$dns_domain_name = Get-AnsibleParam -obj $params -name "dns_domain_name" -failifempty $true
$domain_netbios_name = Get-AnsibleParam -obj $params -name "domain_netbios_name"
$safe_mode_admin_password = Get-AnsibleParam -obj $params -name "safe_mode_password" -failifempty $true
$database_path = Get-AnsibleParam -obj $params -name "database_path" -type "path"
$sysvol_path = Get-AnsibleParam -obj $params -name "sysvol_path" -type "path"
$create_dns_delegation = Get-AnsibleParam -obj $params -name "create_dns_delegation" -type "bool" -default $true
$domain_mode = Get-AnsibleParam -obj $params -name "domain_mode" -type "str" -choices "Win2003","Win2008","Win2008R2","Win2012","Win2012R2","WinThreshold"
$forest_mode = Get-AnsibleParam -obj $params -name "forest_mode" -type "str" -choices "Win2003","Win2008","Win2008R2","Win2012","Win2012R2","WinThreshold"

$forest = $null

# FUTURE: Support down to Server 2012?
If([System.Environment]::OSVersion.Version -lt [Version]"6.3.9600.0") {
    Fail-Json -message "win_domain requires Windows Server 2012R2 or higher"
}

# Check that domain_netbios_name is less than 15 characters
If ($domain_netbios_name -and $domain_netbios_name.length -gt 15) {
    Fail-Json -message "The parameter 'domain_netbios_name' should not exceed 15 characters in length"
}

$result = @{
    changed=$false;
    reboot_required=$false;
}

# FUTURE: Any sane way to do the detection under check-mode *without* installing the feature?

Ensure-Prereqs

Try {
    $forest = Get-ADForest $dns_domain_name -ErrorAction SilentlyContinue
}
Catch { }

If(-not $forest) {
    $result.changed = $true

    $sm_cred = ConvertTo-SecureString $safe_mode_admin_password -AsPlainText -Force

    $install_params = @{
        DomainName=$dns_domain_name;
        SafeModeAdministratorPassword=$sm_cred;
        Confirm=$false;
        SkipPreChecks=$true;
        InstallDns=$true;
        NoRebootOnCompletion=$true;
        WhatIf=$check_mode;
    }
    if ($database_path) {
        $install_params.DatabasePath = $database_path
    }
    if ($sysvol_path) {
        $install_params.SysvolPath = $sysvol_path
    }
    if ($domain_netbios_name) {
        $install_params.DomainNetBiosName = $domain_netbios_name
    }
    if ($create_dns_delegation -ne $null) {
        $install_params.CreateDnsDelegation = $create_dns_delegation
    }
    if ($domain_mode) {
        $install_params.DomainMode = $domain_mode
    }
    if ($forest_mode) {
        $install_params.ForestMode = $forest_mode
    }

    $iaf = Install-ADDSForest @install_params

    $result.reboot_required = $iaf.RebootRequired

    If(-not $check_mode) {
        # The Netlogon service is set to auto start but is not started. This is
        # required for Ansible to connect back to the host and reboot in a
        # later task. Even if this fails Ansible can still connect but only
        # with ansible_winrm_transport=basic so we just display a warning if
        # this fails.
        try {
            Start-Service -Name Netlogon
        } catch {
            Add-Warning -obj $result -message "Failed to start the Netlogon service after promoting the host, Ansible may be unable to connect until the host is manually rebooting: $($_.Exception.Message)"
        }
    }
}

Exit-Json $result
