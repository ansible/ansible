#!powershell

# (c) 2017, Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

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
    Catch [System.DirectoryServices.ActiveDirectory.ActiveDirectoryObjectNotFoundException] {
        Write-DebugLog "not currently joined to a reachable domain"
        return $false
    }
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
        [System.Management.Automation.PSCredential] $domain_cred,
        [string] $domain_ou_path
    )

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
        [System.Management.Automation.PSCredential] $domain_cred
    )

    If(Is-DomainJoined) { # if we're on a domain, unjoin it (which forces us to join a workgroup)
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

$dns_domain_name = Get-AnsibleParam -obj $params -name "dns_domain_name" -type "str"
$hostname = Get-AnsibleParam -obj $params -name "hostname" -type "str"
$workgroup_name = Get-AnsibleParam -obj $params -name "workgroup_name" -type "str"
$domain_admin_user = Get-AnsibleParam -obj $params -name "domain_admin_user" -type "str" -failifempty $result
$domain_admin_password = Get-AnsibleParam -obj $params -name "domain_admin_password" -type "securestr" -failifempty $result
$domain_ou_path = Get-AnsibleParam -obj $params -name "domain_ou_path" -type "str"

$log_path = Get-AnsibleParam -obj $params -name "log_path" -type "path"
$_ansible_check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

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

                    $domain_cred = Create-PSCredential $domain_admin_user $domain_admin_password
                    $join_args = @{
                        dns_domain_name = $dns_domain_name
                        domain_cred = $domain_cred
                    }

                    Write-DebugLog "not a domain member, joining..."

                    If(-not $hostname_match) {
                        Write-DebugLog "adding hostname change to domain-join args"
                        $join_args.new_hostname = $hostname
                    }
                    If($domain_ou_path -ne $null){ # If OU Path is not empty
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
                        $domain_cred = Create-PSCredential $domain_admin_user $domain_admin_password
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
                    $domain_cred = Create-PSCredential $domain_admin_user $domain_admin_password
                    $join_wg_result = Join-Workgroup -workgroup_name $workgroup_name -domain_cred $domain_cred

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
