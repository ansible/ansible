#!powershell
#
# Copyright: (c) 2017, AMTEGA - Xunta de Galicia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy


# ------------------------------------------------------------------------------
$ErrorActionPreference = "Stop"

# Preparing result
$result = @{}
$result.changed = $false

# Parameter ingestion
$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool"  -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true -resultobj $result
$sam_account_name = Get-AnsibleParam -obj $params -name "sam_account_name" -default "$name$"
If (-not $sam_account_name.EndsWith("$")) {
  Fail-Json -obj $result -message "sam_account_name must end in $"
}
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool" -default $true
$description = Get-AnsibleParam -obj $params -name "description" -default ""
$state = Get-AnsibleParam -obj $params -name "state" -ValidateSet "present","absent" -default "present"
If ($state -eq "present") {
  $dns_hostname = Get-AnsibleParam -obj $params -name "dns_hostname" -failifempty $true -resultobj $result
  $ou = Get-AnsibleParam -obj $params -name "ou" -failifempty $true -resultobj $result
  $distinguished_name = "CN=$name,$ou"

  $desired_state = @{
    name = $name
    sam_account_name = $sam_account_name
    dns_hostname = $dns_hostname
    ou = $ou
    distinguished_name = $distinguished_name
    description = $description
    enabled = $enabled
    state = $state
  }
} Else {
  $desired_state = @{
    name = $name
    state = $state
  }
}

# ------------------------------------------------------------------------------
Function Get-InitialState($desired_state) {
  # Test computer exists
  $computer = Try {
    Get-ADComputer `
      -Identity $desired_state.name `
      -Properties DistinguishedName,DNSHostName,Enabled,Name,SamAccountName,Description,ObjectClass
  } Catch { $null }
  If ($computer) {
      $initial_state = @{
        name = $computer.Name
        sam_account_name = $computer.SamAccountName
        dns_hostname = $computer.DNSHostName
        # Get OU from regexp that removes all characters to the first ","
        ou = $computer.DistinguishedName -creplace "^[^,]*,",""
        distinguished_name = $computer.DistinguishedName
        description = $computer.Description
        enabled = $computer.Enabled
        state = "present"
      }
  } Else {
    $initial_state = @{
      name = $desired_state.name
      state = "absent"
    }
  }

  return $initial_state
}

# ------------------------------------------------------------------------------
Function Set-ConstructedState($initial_state, $desired_state) {
  Try {
    Set-ADComputer `
      -Identity $desired_state.name `
      -SamAccountName $desired_state.name `
      -DNSHostName $desired_state.dns_hostname `
      -Enabled $desired_state.enabled `
      -Description $desired_state.description `
      -WhatIf:$check_mode
  } Catch {
    Fail-Json -obj $result -message "Failed to set the AD object $($desired_state.name): $($_.Exception.Message)"
  }

  If ($initial_state.distinguished_name -cne $desired_state.distinguished_name) {
    # Move computer to OU
    Try {
      Get-ADComputer -Identity $desired_state.name |
          Move-ADObject `
            -TargetPath $desired_state.ou `
            -Confirm:$False `
            -WhatIf:$check_mode
    } Catch {
      Fail-Json -obj $result -message "Failed to move the AD object $($desired_state.name) to $($desired_state.ou) OU: $($_.Exception.Message)"
    }
  }
  $result.changed = $true
}

# ------------------------------------------------------------------------------
Function Add-ConstructedState($desired_state) {
  Try {
    New-ADComputer `
      -Name $desired_state.name `
      -SamAccountName $desired_state.sam_account_name `
      -DNSHostName $desired_state.dns_hostname `
      -Path $desired_state.ou `
      -Enabled $desired_state.enabled `
      -Description $desired_state.description `
      -WhatIf:$check_mode
    } Catch {
      Fail-Json -obj $result -message "Failed to create the AD object $($desired_state.name): $($_.Exception.Message)"
    }

  $result.changed = $true
}

# ------------------------------------------------------------------------------
Function Remove-ConstructedState($initial_state) {
  Try {
    Remove-ADComputer `
      -Identity $initial_state.name `
      -Confirm:$False `
      -WhatIf:$check_mode
  } Catch {
    Fail-Json -obj $result -message "Failed to remove the AD object $($desired_state.name): $($_.Exception.Message)"
  }

  $result.changed = $true
}

# ------------------------------------------------------------------------------
Function are_hashtables_equal($x, $y) {
  # Compare not nested HashTables
  Foreach ($key in $x.Keys) {
      If (($y.Keys -notcontains $key) -or ($x[$key] -cne $y[$key])) {
          Return $false
      }
  }
  foreach ($key in $y.Keys) {
      if (($x.Keys -notcontains $key) -or ($x[$key] -cne $y[$key])) {
          Return $false
      }
  }
  Return $true
}

# ------------------------------------------------------------------------------
$initial_state = Get-InitialState($desired_state)

If ($desired_state.state -eq "present") {
    If ($initial_state.state -eq "present") {
      $in_desired_state = are_hashtables_equal $initial_state $desired_state

      If (-not $in_desired_state) {
        Set-ConstructedState $initial_state $desired_state
      }
    } Else { # $desired_state.state = "Present" & $initial_state.state = "Absent"
      Add-ConstructedState($desired_state)
    }
  } Else { # $desired_state.state = "Absent"
    If ($initial_state.state -eq "present") {
      Remove-ConstructedState($initial_state)
    }
  }

If ($diff_support) {
  $diff = @{
    before = $initial_state
    after = $desired_state
  }
  $result.diff = $diff
}

Exit-Json -obj $result
