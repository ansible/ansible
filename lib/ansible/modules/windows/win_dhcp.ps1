#!powershell

# Copyright: (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: GPL-3.0-only
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.CamelConversion
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

Function Convert-MacAddress {
    Param(
        [string]$mac
    )

    # Evaluate Length
    if ($mac.Length -eq 12) {
        # Insert Dashes
        $mac = $mac.Insert(2, "-").Insert(5, "-").Insert(8, "-").Insert(11, "-").Insert(14, "-")
        return $mac
    }
    elseif ($mac.Length -eq 17) {
        # Remove Dashes
        $mac = $mac -replace '-'
        return $mac
    }
    else {
        return $false
    }
}

Function Compare-DhcpLease {
    Param(
        [PSObject]$Original,
        [PSObject]$Updated
    )

    # Compare values that we care about
    if (($Original.AddressState -eq $Updated.AddressState) -and ($Original.IPAddress -eq $Updated.IPAddress) -and ($Original.ScopeId -eq $Updated.ScopeId) -and ($Original.Name -eq $Updated.Name) -and ($Original.Description -eq $Updated.Description)) {
        # changed = false
        return $false
    }
    else {
        # changed = true
        return $true
    }
}

Function Convert-ReturnValue {
    Param(
        $Object
    )

    # TODO: Use camelconversion here instead of manual

    $data = @{
        address_state = $Object.AddressState
        client_id     = $Object.ClientId
        ip_address    = $Object.IPAddress.IPAddressToString
        scope_id      = $Object.ScopeId.IPAddressToString
        name          = $Object.Name
        description   = $Object.Description
    }

    return $data
}

# Doesn't Support Check or Diff Mode
$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $true

# Client Config Params
$type = Get-AnsibleParam -obj $params -name "type" -type "str" -validateset ("reservation", "lease")
$ip = Get-AnsibleParam -obj $params -name "ip" -type "str"
$scope_id = Get-AnsibleParam -obj $params -name "scope_id" -type "str"
$mac = Get-AnsibleParam -obj $params -name "mac" -type "str"
$duration = Get-AnsibleParam -obj $params -name "duration" -type "int"
$dns_hostname = Get-AnsibleParam -obj $params -name "dns_hostname" -type "str"
$dns_regtype = Get-AnsibleParam -obj $params -name "dns_regtype" -type "str" -default "aptr" -validateset ("aptr", "a", "noreg")
$reservation_name = Get-AnsibleParam -obj $params -name "reservation_name" -type "str"
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset ("absent", "present")

# Result KVP
$result = @{
    changed = $false
}

# Parse Regtype
if ($dns_regtype) {
    Switch ($dns_regtype) {
        "aptr" { $dns_regtype = "AandPTR"; break }
        "a" { $dns_regtype = "A"; break }
        "noreg" { $dns_regtype = "NoRegistration"; break }
        default { $dns_regtype = "NoRegistration"; break }
    }
}

Try {
    # Import DHCP Server PS Module
    Import-Module DhcpServer
}
Catch {
    # Couldn't load the DhcpServer Module
    Fail-Json -obj $result -message "The DhcpServer module failed to load properly."
}

# Determine if there is an existing lease
if ($ip) {
    $current_lease = Get-DhcpServerv4Scope | Get-DhcpServerv4Lease | Where-Object IPAddress -eq $ip
}

# MacAddress was specified
if ($mac) {
    if ($mac -like "*-*") {
        $mac_original = $mac
        $mac = Convert-MacAddress -mac $mac
    }

    if ($mac -eq $false) {
        Fail-Json -obj $result -message "The MAC Address is improperly formatted"
    }
    else {
        $current_lease = Get-DhcpServerv4Scope | Get-DhcpServerv4Lease | Where-Object ClientId -eq $mac_original
    }
}

# Did we find a lease/reservation
if ($current_lease) {
    $current_lease_exists = $true
    $original_lease = $current_lease
    $result.original = Convert-ReturnValue -Object $original_lease
}
else {
    $current_lease_exists = $false
}

# If we found a lease, is it a reservation
if ($current_lease_exists -eq $true -and ($current_lease.AddressState -like "*Reservation*")) {
    $current_lease_reservation = $true
}
else {
    $current_lease_reservation = $false
}

# State: Absent
# Ensure the DHCP Lease/Reservation is not present
if ($state -eq "absent") {

    # Required: MAC or IP address
    if ((-not $mac) -and (-not $ip)) {
        $result.changed = $false
        Fail-Json -obj $result -message "The ip or mac parameter is required for state=absent"
    }

    # If the lease exists, we need to destroy it
    if ($current_lease_reservation -eq $true) {
        # Try to remove reservation
        Try {
            $current_lease | Remove-DhcpServerv4Reservation -WhatIf:$check_mode
            $state_absent_removed = $true
        }
        Catch {
            $state_absent_removed = $false
        }
    }
    else {
        # Try to remove lease
        Try {
            $current_lease | Remove-DhcpServerv4Lease -WhatIf:$check_mode
            $state_absent_removed = $true
        }
        Catch {
            $state_absent_removed = $false
        }
    }

    # If the lease doesn't exist, our work here is done
    if ($current_lease_exists -eq $false) {
        $result.changed = $false
        Exit-Json -obj $result
    }

    # See if we removed the lease/reservation
    if ($state_absent_removed) {
        $result.changed = $true
        Exit-Json -obj $result
    }
    else {
        $result.lease = Convert-ReturnValue -Object $current_lease
        Fail-Json -obj $result -message "Could not remove lease/reservation"
    }
}

# State: Present
# Ensure the DHCP Lease/Reservation is present, and consistent
if ($state -eq "present") {

    # Current lease exists, and is not a reservation
    if (($current_lease_reservation -eq $false) -and ($current_lease_exists -eq $true)) {
        if ($type -eq "reservation") {
            Try {
                # Update parameters
                $params = @{ }
                if ($mac) {
                    $params.ClientId = $mac
                }
                else {
                    $params.ClientId = $current_lease.ClientId
                }

                if ($description) {
                    $params.Description = $description
                }
                else {
                    $params.Description = $current_lease.Description
                }

                if ($reservation_name) {
                    $params.Name = $reservation_name
                }
                else {
                    $params.Name = "reservation-" + $params.ClientId
                }

                # Desired type is reservation
                $current_lease | Add-DhcpServerv4Reservation -WhatIf:$check_mode
                $current_reservation = Get-DhcpServerv4Lease -ClientId $params.ClientId -ScopeId $current_lease.ScopeId

                # Update the reservation with new values
                $current_reservation | Set-DhcpServerv4Reservation @params -WhatIf:$check_mode
                $updated_reservation = Get-DhcpServerv4Lease -ClientId $params.ClientId -ScopeId $current_reservation.ScopeId

                # Successful, compare values
                $result.changed = Compare-DhcpLease -Original $original_lease -Updated $reservation

                # Return values
                $result.lease = Convert-ReturnValue -Object $updated_reservation

                Exit-Json -obj $result
            }
            Catch {
                $result.changed = $false
                Fail-Json -obj $result -message "Could not convert lease to a reservation"
            }
        }

        # Nothing needs to be done, already in the desired state
        if ($type -eq "lease") {
            $result.changed = $false
            $result.lease = Convert-ReturnValue -Object $current_lease
            Exit-Json -obj $result
        }
    }

    # Current lease exists, and is a reservation
    if (($current_lease_reservation -eq $true) -and ($current_lease_exists -eq $true)) {
        if ($type -eq "lease") {
            Try {
                # Desired type is a lease, remove the reservation
                $current_lease | Remove-DhcpServerv4Reservation -WhatIf:$check_mode

                # Build a new lease object with remnants of the reservation
                $lease_params = @{
                    ClientId     = $original_lease.ClientId
                    IPAddress    = $original_lease.IPAddress
                    ScopeId      = $original_lease.ScopeId
                    ComputerName = $original_lease.HostName
                    AddressState = 'Active'
                }

                # Create new lease
                Try {
                    Add-DhcpServerv4Lease @lease_params -WhatIf:$check_mode
                }
                Catch {
                    $result.changed = $false
                    Fail-Json -obj $result -message "Could not recreate the reservation as a lease"
                }

                # Get the lease we just created
                Try {
                    $new_lease = Get-DhcpServerv4Lease -ClientId $lease_params.ClientId -ScopeId $lease_params.ScopeId
                }
                Catch {
                    $result.changed = $false
                    Fail-Json -obj $result -message "Could not retreive the newly created lease"
                }

                # Successful
                $result.changed = $true
                $result.lease = Convert-ReturnValue -Object $new_lease
                Exit-Json -obj $result
            }
            Catch {
                $result.changed = $false
                Fail-Json -obj $result -message "Could not convert reservation to lease"
            }
        }

        # Already in the desired state
        if ($type -eq "reservation") {

            # Update parameters
            $params = @{ }
            if ($mac) {
                $params.ClientId = $mac
            }
            else {
                $params.ClientId = $current_lease.ClientId
            }

            if ($description) {
                $params.Description = $description
            }
            else {
                $params.Description = $current_lease.Description
            }

            if ($reservation_name) {
                $params.Name = $reservation_name
            }
            else {
                if ($null -eq $original_lease.Name) {
                    $params.Name = "reservation-" + $original_lease.ClientId
                }
                else {
                    $params.Name = $original_lease.Name
                }
            }

            # Update the reservation with new values
            $current_lease | Set-DhcpServerv4Reservation @params -WhatIf:$check_mode
            $reservation = Get-DhcpServerv4Lease -ClientId $current_lease.ClientId -ScopeId $current_lease.ScopeId

            # Successful
            $result.changed = Compare-DhcpLease -Original $original_lease -Updated $reservation

            # Return values
            $result.lease = Convert-ReturnValue -Object $reservation
            Exit-Json -obj $result
        }
    }

    # Lease Doesn't Exist - Create
    if ($current_lease_exists -eq $false) {

        # Required: MAC and IP address
        if ((-not $mac) -or (-not $ip)) {
            $result.changed = $false
            Fail-Json -obj $result -message "The ip and mac parameters are required for state=present"
        }

        # Required: Scope ID
        if (-not $scope_id) {
            $result.changed = $false
            Fail-Json -obj $result -message "The scope_id parameter is required for state=present"
        }

        # Required Parameters
        $lease_params = @{
            ClientId     = $mac
            IPAddress    = $ip
            ScopeId      = $scope_id
            AddressState = 'Active'
            Confirm      = $false
        }

        if ($duration) {
            $lease_params.LeaseExpiryTime = (Get-Date).AddDays($duration)
        }

        if ($dns_hostname) {
            $lease_params.HostName = $dns_hostname
        }

        if ($dns_regtype) {
            $lease_params.DnsRR = $dns_regtype
        }

        if ($description) {
            $lease_params.Description = $description
        }

        # Create Lease
        Try {
            # Create lease based on parameters
            Add-DhcpServerv4Lease @lease_params -WhatIf:$check_mode
            # Retreive the lease
            $lease = Get-DhcpServerv4Lease -ClientId $mac -ScopeId $scope_id

            # If lease is the desired type
            if ($type -eq "lease") {
                $result.changed = $true
                $result.lease = Convert-ReturnValue -Object $lease
                Exit-Json -obj $result
            }
        }
        Catch {
            # Failed to create lease
            $result.changed = $false
            Fail-Json -obj $result -message "Could not create DHCP lease"
        }

        # Create Reservation
        Try {
            # If reservation is the desired type
            if ($type -eq "reservation") {
                if ($reservation_name) {
                    $lease_params.Name = $reservation_name
                }
                else {
                    $lease_params.Name = "reservation-" + $mac
                }

                # Convert to Reservation
                $lease | Add-DhcpServerv4Reservation -WhatIf:$check_mode
                # Get DHCP reservation object
                $reservation = Get-DhcpServerv4Reservation -ClientId $mac -ScopeId $scope_id
                $result.changed = $true
                $result.lease = Convert-ReturnValue -Object $reservation
                Exit-Json -obj $result
            }
        }
        Catch {
            # Failed to create reservation
            $result.changed = $false
            Fail-Json -obj $result -message "Could not create DHCP reservation"
        }
    }
}

# Exit, Return Result
Exit-Json -obj $result