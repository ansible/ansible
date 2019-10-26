#!powershell

# Copyright: (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: GPL-3.0-only
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$ErrorActionPreference = 'Stop'

$spec = @{
    options = @{
        type = @{ type = "str"; choices = "reservation", "lease"; default = "reservation" }
        ip = @{ type = "str" }
        scope_id = @{ type = "str" }
        mac = @{ type = "str" }
        duration = @{ type = "int" }
        dns_hostname = @{ type = "str"; }
        dns_regtype = @{ type = "str"; choices = "aptr", "a", "noreg"; default = "aptr" }
        reservation_name = @{ type = "str"; }
        description = @{ type = "str"; }
        state = @{ type = "str"; choices = "absent", "present"; default = "present" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$module.Result.changed = $false
$check_mode = $module.CheckMode

$type = $module.Params.type
$ip = $module.Params.ip
$scope_id = $module.Params.scope_id
$mac = $module.Params.mac
$duration = $module.Params.duration
$dns_hostname = $module.Params.dns_hostname
$dns_regtype = $module.Params.dns_regtype
$reservation_name = $module.Params.reservation_name
$description = $module.Params.description
$state = $module.Params.state

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
    $module.FailJson("The DhcpServer module failed to load properly")
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
        $module.FailJson("The MAC Address is not properly formatted")
    }
    else {
        $current_lease = Get-DhcpServerv4Scope | Get-DhcpServerv4Lease | Where-Object ClientId -eq $mac_original
    }
}

# Did we find a lease/reservation
if ($current_lease) {
    $current_lease_exists = $true
    $original_lease = $current_lease
    $module.Diff.before = Convert-ReturnValue -Object $original_lease
}
else {
    $current_lease_exists = $false
}

# If we found a lease, is it a reservation?
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
        $module.Result.changed = $false
        $module.FailJson("The ip or mac parameter is required for state=absent")
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
        $module.Result.changed = $false
        $module.Result.msg = "The lease or reservation doesn't exist."
        $module.ExitJson()
    }

    # See if we removed the lease/reservation
    if ($state_absent_removed) {
        $module.Result.changed = $true
        $module.ExitJson()
    }
    else {
        $module.Result.lease = Convert-ReturnValue -Object $current_lease
        $module.FailJson("Unable to remove lease/reservation")
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
                } else {
                    $params.ClientId = $current_lease.ClientId
                }

                if ($description) {
                    $params.Description = $description
                } else {
                    $params.Description = $current_lease.Description
                }

                if ($reservation_name) {
                    $params.Name = $reservation_name
                } else {
                    $params.Name = "reservation-" + $params.ClientId
                }

                # Desired type is reservation
                $current_lease | Add-DhcpServerv4Reservation -WhatIf:$check_mode

                if(-not $check_mode) {
                    $current_reservation = Get-DhcpServerv4Lease -ClientId $params.ClientId -ScopeId $current_lease.ScopeId
                }

                # Update the reservation with new values
                $current_reservation | Set-DhcpServerv4Reservation @params -WhatIf:$check_mode

                if(-not $check_mode) {
                    $updated_reservation = Get-DhcpServerv4Lease -ClientId $params.ClientId -ScopeId $current_reservation.ScopeId
                }

                if(-not $check_mode) {
                    # Compare Values
                    $module.Result.changed = Compare-DhcpLease -Original $original_lease -Updated $updated_reservation
                    $module.Result.lease = Convert-ReturnValue -Object $updated_reservation
                } else {
                    $module.Result.changed = $true
                }

                $module.ExitJson()
            }
            Catch {
                $module.Result.changed = $false
                $module.FailJson("Could not convert lease to a reservation")
            }
        }

        # Nothing needs to be done, already in the desired state
        if ($type -eq "lease") {
            $module.Result.changed = $true
            $module.msg = "The lease is already in it's desired state"
            $module.ExitJson()
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
                    ClientId = $original_lease.ClientId
                    IPAddress = $original_lease.IPAddress.IPAddressToString
                    ScopeId = $original_lease.ScopeId.IPAddressToString
                    HostName = $original_lease.HostName
                    AddressState = 'Active'
                }

                # Create new lease
                Try {
                    Add-DhcpServerv4Lease @lease_params -WhatIf:$check_mode
                }
                Catch {
                    $module.Result.changed = $false
                    $module.FailJson("Unable to convert the reservation to a lease")
                }

                # Get the lease we just created
                if(-not $check_mode) {
                    Try {
                        $new_lease = Get-DhcpServerv4Lease -ClientId $lease_params.ClientId -ScopeId $lease_params.ScopeId
                    }
                    Catch {
                        $module.Result.changed = $false
                        $module.FailJson("Unable to retreive the newly created lease")
                    }
                }

                if(-not $check_mode) {
                    $module.Result.lease = Convert-ReturnValue -Object $new_lease
                }

                $module.Result.changed = $true
                $module.ExitJson()
            }
            Catch {
                $module.Result.changed = $false
                $module.FailJson("Could not convert reservation to lease")
            }
        }

        # Already in the desired state
        if ($type -eq "reservation") {

            # Update parameters
            $params = @{ }

            if ($mac) {
                $params.ClientId = $mac
            } else {
                $params.ClientId = $current_lease.ClientId
            }

            if ($description) {
                $params.Description = $description
            } else {
                $params.Description = $current_lease.Description
            }

            if ($reservation_name) {
                $params.Name = $reservation_name
            } else {
                # Original lease had a null name so let's generate one
                if ($null -eq $original_lease.Name) {
                    $params.Name = "reservation-" + $original_lease.ClientId
                } else {
                    $params.Name = $original_lease.Name
                }
            }

            # Update the reservation with new values
            $current_lease | Set-DhcpServerv4Reservation @params -WhatIf:$check_mode

            if(-not $check_mode) {
                $reservation = Get-DhcpServerv4Lease -ClientId $current_lease.ClientId -ScopeId $current_lease.ScopeId
                $module.Result.changed = Compare-DhcpLease -Original $original_lease -Updated $reservation
                $module.Result.lease = Convert-ReturnValue -Object $reservation
            } else {
                $module.Result.changed = $true
            }

            # Return values
            $module.ExitJson()
        }
    }

    # Lease Doesn't Exist - Create
    if ($current_lease_exists -eq $false) {

        # Required: MAC and IP address
        if ((-not $mac) -or (-not $ip)) {
            $module.Result.changed = $false
            $module.FailJson("The ip and mac parameters are required for state=present")
        }

        # Required: Scope ID
        if (-not $scope_id) {
            $module.Result.changed = $false
            $module.FailJson("The scope_id parameter is required for state=present")
        }

        # Required Parameters
        $lease_params = @{
            ClientId = $mac
            IPAddress = $ip
            ScopeId = $scope_id
            AddressState = 'Active'
            Confirm = $false
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
            if(-not $check_mode) {
                $new_lease = Get-DhcpServerv4Lease -ClientId $mac -ScopeId $scope_id
                $module.Result.lease = Convert-ReturnValue -Object $new_lease
            }

            # If lease is the desired type
            if ($type -eq "lease") {
                $module.Result.changed = $true
                $module.ExitJson()
            }
        }
        Catch {
            # Failed to create lease
            $module.Result.changed = $false
            $module.FailJson("Could not create DHCP lease")
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

                Try {
                    if($check_mode) {
                        # In check mode, a lease won't exist for conversion, make one manually
                        Add-DhcpServerv4Reservation -ScopeId $scope_id -ClientId $mac_original -IPAddress $ip -WhatIf:$check_mode
                    } else {
                        # Convert to Reservation
                        $new_lease | Add-DhcpServerv4Reservation -WhatIf:$check_mode
                    }
                }
                Catch {
                    # Failed to create reservation
                    $module.Result.changed = $false
                    $module.FailJson("Could not create DHCP reservation")
                }

                if(-not $check_mode) {
                    # Get DHCP reservation object
                    $new_lease = Get-DhcpServerv4Reservation -ClientId $mac_original -ScopeId $scope_id
                    $module.Result.lease = Convert-ReturnValue -Object $new_lease
                }

                $module.Result.changed = $true
                $module.ExitJson()
            }
        }
        Catch {
            # Failed to create reservation
            $module.Result.changed = $false
            $module.FailJson("Could not create DHCP reservation")
        }
    }
}

$module.ExitJson()