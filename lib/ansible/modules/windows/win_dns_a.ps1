#!powershell
#
# Copyright: (c) 2017, AMTEGA - Xunta de Galicia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy


# ------------------------------------------------------------------------------
$ErrorActionPreference = "Stop"

# Preparing result
$result = New-Object PSObject
Set-Attr $result "changed" $false

# Parameter ingestion
$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false | ConvertTo-Bool
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -default $false | ConvertTo-Bool

# ------------------------------------------------------------------------------
Function Get-DesiredState($params) {
  $computer_name = Get-AnsibleParam -obj $params -name "computer_name" -failifempty $true -resultobj $result
  $zone_name = Get-AnsibleParam -obj $params -name "zone_name" -failifempty $true -resultobj $result
  $name = Get-AnsibleParam -obj $params -name "name" -failifempty $true -resultobj $result
  $state = (Get-AnsibleParam -obj $params -name "state" -ValidateSet "Present","Absent" -default "Present").ToLower()
  If ($state -eq "present") {
    $ipv4_address = Get-AnsibleParam -obj $params -name "ipv4_address" -failifempty $true -resultobj $result
  } Else {
    $ipv4_address = $null
  }
  $desired_state = New-Object psobject @{
    computer_name = $computer_name
    ipv4_address = $ipv4_address
    name = $name
    state = $state
    zone_name = $zone_name
  }

  Return $desired_state
}

# ------------------------------------------------------------------------------
Function Get-InitialState($desired_state) {
  # Test DnsServerResourceRecord exists
  $record = Try { Get-DnsServerResourceRecord `
                    -ComputerName $desired_state.computer_name `
                    -ZoneName $desired_state.zone_name `
                    -RRType A `
                    -Name $desired_state.name
                } Catch { $null }
  If ($record) {
    $initial_state = New-Object psobject @{
      computer_name = $desired_state.computer_name # Same DNS server
      zone_name = $desired_state.zone_name
      name = $record.HostName
      ipv4_address = $record.RecordData.IPv4Address.IPAddressToString
      state = "present"
    }
  } Else {
    $initial_state = New-Object psobject @{
      computer_name = $desired_state.computer_name # Same DNS server
      zone_name = $desired_state.zone_name
      name = ""
      ipv4_address = ""
      state = "absent"
    }
  }
  Return $initial_state
}

# ------------------------------------------------------------------------------
Function Set-ConstructedState($desired_state) {
  Remove-ConstructedState($desired_state)
  Add-ConstructedState($desired_state)

  Set-Attr $result "changed" $true
}

# ------------------------------------------------------------------------------
Function Add-ConstructedState($desired_state) {
  Add-DnsServerResourceRecordA `
    -ComputerName $desired_state.computer_name `
    -ZoneName $desired_state.zone_name `
    -Name $desired_state.name `
    -IPv4Address $desired_state.ipv4_address `
    -Confirm:$False `
    -WhatIf:$check_mode

  Set-Attr $result "changed" $true
}

# ------------------------------------------------------------------------------
Function Remove-ConstructedState($desired_state) {
  Remove-DnsServerResourceRecord `
    -ComputerName $desired_state.computer_name `
    -ZoneName $desired_state.zone_name `
    -Name $desired_state.name `
    -RRType A `
    -Confirm:$False `
    -Force:$True `
    -WhatIf:$check_mode

  Set-Attr $result "changed" $true
}

# ------------------------------------------------------------------------------
Function are_hashtables_equal($x, $y) {
  foreach ($key in $x.Keys) {
      if (($y.Keys -notcontains $key) -or ($x[$key] -ne $y[$key])) {
          return $false
      }
  }
  foreach ($key in $y.Keys) {
      if (($x.Keys -notcontains $key) -or ($x[$key] -ne $y[$key])) {
          return $false
      }
  }
  Return $true
}

# ------------------------------------------------------------------------------
$desired_state = Get-DesiredState($params)
$initial_state = Get-InitialState($desired_state)

If ($desired_state.state -eq "Present") {
    If ($initial_state.state -eq "Present") {
      $in_desired_state =  are_hashtables_equal $initial_state $desired_state

      If (-not $in_desired_state) {
        Set-ConstructedState($desired_state)
      }
    } Else { # $desired_state.state = "Present" & $initial_state.state = "Absent"
      Add-ConstructedState($desired_state)
    }
  } Else { # $desired_state.state = "Absent"
    If ($initial_state.state -eq "Present") {
      Remove-ConstructedState($desired_state)
    }
  }

If ($diff_support) {
  $diff = @{
    before = $initial_state
    after = $desired_state
  }
  Set-Attr $result "diff" $diff
}

Exit-Json $result
