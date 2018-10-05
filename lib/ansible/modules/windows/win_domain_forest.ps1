#!powershell

# Copyright: (c) 2017, Red Hat, Inc.
# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"
$ConfirmPreference = "None"

$log_path = $null

Function Write-DebugLog {
    Param(
        [string]$msg
    )

    $DebugPreference = "Continue"
    $ErrorActionPreference = "Continue"
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug $msg

    if($log_path) {
        Add-Content $log_path $msg
    }
}

$required_features = @("AD-Domain-Services","RSAT-ADDS")

Function Get-MissingFeatures {
    Write-DebugLog "Checking for missing Windows features..."

    $features = @(Get-WindowsFeature $required_features)

    If($features.Count -ne $required_features.Count) {
        Throw "One or more Windows features required for a domain controller are unavailable"
    }

    $missing_features = @($features | Where-Object InstallState -ne Installed)

    return ,$missing_features  # No, the comma is not a typo- allows us to return an empty array
}

Function Ensure-FeatureInstallation {
    # Ensure RSAT-ADDS and AD-Domain-Services features are installed

    Write-DebugLog "Ensuring required Windows features are installed..."
    $feature_result = Install-WindowsFeature $required_features

    If(-not $feature_result.Success) {
        Exit-Json -message ("Error installing AD-Domain-Services and RSAT-ADDS features: {0}" -f ($feature_result | Out-String))
    }
}

# Return the domain we're a DC for, or null if not a DC
Function Get-DomainControllerDomain {
    Write-DebugLog "Checking for domain controller role and domain name"

    $sys_cim = Get-WmiObject Win32_ComputerSystem

    $is_dc = $sys_cim.DomainRole -in (4,5)  # backup/primary DC
    # This will be our workgroup or joined-domain if we're not a DC
    $domain = $sys_cim.Domain

    Switch($is_dc) {
        $true { return $domain }
        Default { return $null }
    }
}

Function Get-OperationMasterRoles {
    $assigned_roles = @((Get-ADDomainController -Server localhost).OperationMasterRoles)

    Return ,$assigned_roles  # No, the comma is not a typo- allows us to return an empty array
}

$result = @{
    changed = $false
    reboot_required = $false
}

$params = Parse-Args -arguments $args -supports_check_mode $true

$dns_domain_name = Get-AnsibleParam -obj $params -name "dns_domain_name"
$safe_mode_password= Get-AnsibleParam -obj $params -name "safe_mode_password"
$database_path = Get-AnsibleParam -obj $params -name "database_path" -type "path"
$sysvol_path = Get-AnsibleParam -obj $params -name "sysvol_path" -type "path"
$create_dns_delegation = Get-AnsibleParam -obj $params -name "create_dns_delegation" -type "bool" -default $true
$domain_mode = Get-AnsibleParam -obj $params -name "domain_mode" -type "str" -choices "Win2003","Win2008","Win2008R2","Win2012","Win2012R2","WinTreshold"
$domain_netbios_name = Get-AnsibleParam -obj $params -name "domain_netbios_name" -type "str"
$forest_mode = Get-AnsibleParam -obj $params -name "forest_mode" -type "str" -choices "Win2003","Win2008","Win2008R2","Win2012","Win2012R2","WinTreshold"

$log_path = Get-AnsibleParam -obj $params -name "log_path"
$_ansible_check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$global:log_path = $log_path

Try {
    # Ensure target OS support; < 2012 doesn't have cmdlet support for DC promotion
    If(-not (Get-Command Install-WindowsFeature -ErrorAction SilentlyContinue)) {
        Fail-Json -message "win_domain_controller requires at least Windows Server 2012"
    }

    # Check that domain_netbios_name is less than 15 characters
    If ($domain_netbios_name -and $domain_netbios_name.length -gt 15) {
        Fail-Json -message "The parameter 'domain_netbios_name' should not exceed 15 characters in length"
    }

    # Validate args
    If(-not $dns_domain_name) {
        Fail-Json -message "dns_domain_name is required"
    }

    If(-not $safe_mode_password) {
        Fail-Json -message "safe_mode_password is required"
    }

    $current_dc_domain = Get-DomainControllerDomain

    # All other operations will require the AD-DS and RSAT-ADDS features...

    $missing_features = Get-MissingFeatures

    If($missing_features.Count -gt 0) {
        Write-DebugLog ("Missing Windows features ({0}), need to install" -f ($missing_features -join ", "))
        $result.changed = $true  # We need to install features
        If($_ansible_check_mode) {
            # Bail out here- we can't proceed without knowing the features are installed
            Write-DebugLog "check-mode, exiting early"
            Exit-Json $result
        }

        Ensure-FeatureInstallation | Out-Null
    }

    If(-not $safe_mode_password) {
        Fail-Json -message "safe_mode_password is required"
    }

    If($current_dc_domain) {
        # FUTURE: Implement managed Remove/Add to change domains?

        If($current_dc_domain -ne $dns_domain_name) {
            Fail-Json "$(hostname) is a domain controller for domain $current_dc_domain; changing DC domains is not implemented"
        }
    }

    # Need to promote to DC
    If(-not $current_dc_domain) {
        Write-DebugLog "Not currently a domain controller; needs promotion"
        $result.changed = $true
        If($_ansible_check_mode) {
            Write-DebugLog "check-mode, exiting early"
            Fail-Json -message $result
        }

        $result.reboot_required = $true

        $safe_mode_secure = $safe_mode_password | ConvertTo-SecureString -AsPlainText -Force
        Write-DebugLog "Installing domain controller..."
        $install_params = @{
            DomainName = $dns_domain_name
            SafeModeAdministratorPassword = $safe_mode_secure
        }
        if ($domain_netbios_name) {
            $install_params.DomainNetbiosName = $domain_netbios_name
        }
        if ($database_path) {
            $install_params.DatabasePath = $database_path
        }
        if ($sysvol_path) {
            $install_params.SysvolPath = $sysvol_path
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
        $install_result = Install-ADDSForest -NoRebootOnCompletion -Force @install_params

        Write-DebugLog "Installation complete, trying to start the Netlogon service"
        # The Netlogon service is set to auto start but is not started. This is
        # required for Ansible to connect back to the host and reboot in a
        # later task. Even if this fails Ansible can still connect but only
        # with ansible_winrm_transport=basic so we just display a warning if
        # this fails.
        try {
            Start-Service -Name Netlogon
        } catch {
            Write-DebugLog "Failed to start the Netlogon service: $($_.Exception.Message)"
            Add-Warning -obj $result -message "Failed to start the Netlogon service after promoting the host, Ansible may be unable to connect until the host is manually rebooting: $($_.Exception.Message)"
        }

        Write-DebugLog "Domain Controller setup completed, needs reboot..."
    }

    Exit-Json $result
} Catch {
    Write-DebugLog "Exception: $($_.Exception.Message)"
    Throw
}
