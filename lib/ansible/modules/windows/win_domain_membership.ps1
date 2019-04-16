#!powershell

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

$ErrorActionPreference = "Stop"

$log_path = $null

Function Write-DebugLog {
    Param(
    [string]$msg
    )

    $DebugPreference = "Continue"
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug $msg

    if($log_path) {
        Add-Content $log_path $msg
    }
}

Function Get-DomainMembershipMatch {
    Param(
        [string] $dns_domain_name
    )

    # FUTURE: add support for NetBIOS domain name?

    # this requires the DC to be accessible; "DC unavailable" is indistinguishable from "not joined to the domain"...
    Try {
        Write-DebugLog "calling GetComputerDomain()"
        $current_dns_domain = [System.DirectoryServices.ActiveDirectory.Domain]::GetComputerDomain().Name

        $domain_match = $current_dns_domain -eq $dns_domain_name

        Write-DebugLog ("current domain {0} matches {1}: {2}" -f $current_dns_domain, $dns_domain_name, $domain_match)

        return $domain_match
    }
    catch [System.Security.Authentication.AuthenticationException] {
        Write-DebugLog "Failed to get computer domain.  Attempting a different method."
        Add-Type -AssemblyName System.DirectoryServices.AccountManagement            
        $user_principal = [System.DirectoryServices.AccountManagement.UserPrincipal]::Current
        If ($user_principal.ContextType -eq "Machine") {
            $current_dns_domain = (Get-CimInstance -ClassName Win32_ComputerSystem -Property Domain).Domain
            
            $domain_match = $current_dns_domain -eq $dns_domain_name

            Write-DebugLog ("current domain {0} matches {1}: {2}" -f $current_dns_domain, $dns_domain_name, $domain_match)

            return $domain_match
        }
        Else {
            Fail-Json -obj $result -message "Failed to authenticate with domain controller and cannot retrieve the existing domain name: $($_.Exception.Message)"
        }
    }
    Catch [System.DirectoryServices.ActiveDirectory.ActiveDirectoryObjectNotFoundException] {
        Write-DebugLog "not currently joined to a reachable domain"
        return $false
    }
}

Function Create-Credential {
    Param(
        [string] $cred_user,
        [string] $cred_pass
    )

    $cred = New-Object System.Management.Automation.PSCredential($cred_user, $($cred_pass | ConvertTo-SecureString -AsPlainText -Force))

    return $cred
}

Function Get-HostnameMatch {
    Param(
        [string] $hostname
    )

    # Add-Computer will validate the "shape" of the hostname- we just care if it matches...

    $hostname_match = $env:COMPUTERNAME -eq $hostname
    Write-DebugLog ("current hostname {0} matches {1}: {2}" -f $env:COMPUTERNAME, $hostname, $hostname_match)

    return $hostname_match
}

Function Is-DomainJoined {
    return (Get-WmiObject Win32_ComputerSystem).PartOfDomain
}

Function Join-Domain {
    Param(
        [string] $dns_domain_name,
        [string] $new_hostname,
        [string] $domain_admin_user,
        [string] $domain_admin_password,
        [string] $domain_ou_path
    )

    Write-DebugLog ("Creating credential for user {0}" -f $domain_admin_user)
    $domain_cred = Create-Credential $domain_admin_user $domain_admin_password

    $add_args = @{
        ComputerName="."
        Credential=$domain_cred
        DomainName=$dns_domain_name
        Force=$null
    }

    Write-DebugLog "adding hostname set arg to Add-Computer args"
    If($new_hostname) {
        $add_args["NewName"] = $new_hostname
    }


    if($domain_ou_path){
        Write-DebugLog "adding OU destination arg to Add-Computer args"
        $add_args["OUPath"] = $domain_ou_path
    }
    $argstr = $add_args | Out-String
    Write-DebugLog "calling Add-Computer with args: $argstr"
    try {
        $add_result = Add-Computer @add_args
    } catch {
        Fail-Json -obj $result -message "failed to join domain: $($_.Exception.Message)"
    }

    Write-DebugLog ("Add-Computer result was \n{0}" -f $add_result | Out-String)
}

Function Get-Workgroup {
    return (Get-WmiObject Win32_ComputerSystem).Workgroup
}

Function Set-Workgroup {
    Param(
        [string] $workgroup_name
    )

    Write-DebugLog ("Calling JoinDomainOrWorkgroup with workgroup {0}" -f $workgroup_name)
    try {
        $swg_result = (Get-WmiObject -ClassName Win32_ComputerSystem).JoinDomainOrWorkgroup($workgroup_name)
    } catch {
        Fail-Json -obj $result -message "failed to call Win32_ComputerSystem.JoinDomainOrWorkgroup($workgroup_name): $($_.Exception.Message)"
    }

    if ($swg_result.ReturnValue -ne 0) {
        Fail-Json -obj $result -message "failed to set workgroup through WMI, return value: $($swg_result.ReturnValue)"
    
    return $swg_result}
}

Function Join-Workgroup {
    Param(
        [string] $workgroup_name,
        [string] $domain_admin_user,
        [string] $domain_admin_password
    )

    If(Is-DomainJoined) { # if we're on a domain, unjoin it (which forces us to join a workgroup)
        $domain_cred = Create-Credential $domain_admin_user $domain_admin_password

        # 2012+ call the Workgroup arg WorkgroupName, but seem to accept
        try {
            $rc_result = Remove-Computer -Workgroup $workgroup_name -Credential $domain_cred -Force
        } catch {
            Fail-Json -obj $result -message "failed to remove computer from domain: $($_.Exception.Message)"
        }
    }

    # we're already on a workgroup- change it.
    Else {
        $swg_result = Set-Workgroup $workgroup_name
    }
}


$result = @{
    changed = $false
    reboot_required = $false
}

$params = Parse-Args -arguments $args -supports_check_mode $true

$state = Get-AnsibleParam $params "state" -validateset @("domain","workgroup") -failifempty $result

$dns_domain_name = Get-AnsibleParam $params "dns_domain_name"
$hostname = Get-AnsibleParam $params "hostname"
$workgroup_name = Get-AnsibleParam $params "workgroup_name"
$domain_admin_user = Get-AnsibleParam $params "domain_admin_user" -failifempty $result
$domain_admin_password = Get-AnsibleParam $params "domain_admin_password" -failifempty $result
$domain_ou_path = Get-AnsibleParam $params "domain_ou_path"

$log_path = Get-AnsibleParam $params "log_path"
$_ansible_check_mode = Get-AnsibleParam $params "_ansible_check_mode" -default $false

If ($state -eq "domain") {
    If(-not $dns_domain_name) {
        Fail-Json @{} "dns_domain_name is required when state is 'domain'"
    }
}
Else { # workgroup
    If(-not $workgroup_name) {
        Fail-Json @{} "workgroup_name is required when state is 'workgroup'"
    }
}


$global:log_path = $log_path

Try {

    $hostname_match = If($hostname) { Get-HostnameMatch $hostname } Else { $true }

    $result.changed = $result.changed -or (-not $hostname_match)

    Switch($state) {
        domain {
            $domain_match = Get-DomainMembershipMatch $dns_domain_name

            $result.changed = $result.changed -or (-not $domain_match)

            If($result.changed -and -not $_ansible_check_mode) {
                If(-not $domain_match) {
                    If(Is-DomainJoined) {
                        Write-DebugLog "domain doesn't match, and we're already joined to another domain"
                        throw "switching domains is not implemented"
                    }

                    $join_args = @{
                        dns_domain_name = $dns_domain_name
                        domain_admin_user = $domain_admin_user
                        domain_admin_password = $domain_admin_password
                    }

                    Write-DebugLog "not a domain member, joining..."

                    If(-not $hostname_match) {
                        Write-DebugLog "adding hostname change to domain-join args"
                        $join_args.new_hostname = $hostname
                    }
                    If($null -ne $domain_ou_path){ # If OU Path is not empty
                        Write-DebugLog "adding domain_ou_path to domain-join args"
                        $join_args.domain_ou_path = $domain_ou_path
                    }

                    $join_result = Join-Domain @join_args

                    # this change requires a reboot
                    $result.reboot_required = $true
                }
                ElseIf(-not $hostname_match) { # domain matches but hostname doesn't, just do a rename
                    Write-DebugLog ("domain matches, setting hostname to {0}" -f $hostname)

                    $rename_args = @{NewName=$hostname}

                    If (Is-DomainJoined) {
                        $domain_cred = Create-Credential $domain_admin_user $domain_admin_password
                        $rename_args.DomainCredential = $domain_cred
                    }

                    $rename_result = Rename-Computer @rename_args

                    # this change requires a reboot
                    $result.reboot_required = $true
                } Else {
                    # no change is needed
                }

            }
            Else {
                Write-DebugLog "check mode, exiting early..."
            }

        }

        workgroup {
            $workgroup_match = $(Get-Workgroup) -eq $workgroup_name

            $result.changed = $result.changed -or (-not $workgroup_match)

            If(-not $_ansible_check_mode) {
                If(-not $workgroup_match) {
                    Write-DebugLog ("setting workgroup to {0}" -f $workgroup_name)
                    $join_wg_result = Join-Workgroup -workgroup_name $workgroup_name -domain_admin_user $domain_admin_user -domain_admin_password $domain_admin_password

                    # this change requires a reboot
                    $result.reboot_required = $true
                }
                If(-not $hostname_match) {
                    Write-DebugLog ("setting hostname to {0}" -f $hostname)
                    $rename_result = Rename-Computer -NewName $hostname

                    # this change requires a reboot
                    $result.reboot_required = $true
                }
            }
        }
        default { throw "invalid state $state" }
    }

    Exit-Json $result
}
Catch {
    $excep = $_

    Write-DebugLog "Exception: $($excep | out-string)"

    Throw
}
