#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params      = Parse-Args -arguments $args -supports_check_mode $true;
$check_mode  = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$managers    = Get-AnsibleParam -obj $params -name "permitted_managers"  -type "list" -default @()
$communities = Get-AnsibleParam -obj $params -name "community_strings"   -type "list" -default @()
$action_in   = Get-AnsibleParam -obj $params -name "replace"             -type "str"  -default "set" -ValidateSet @("set", "add", "remove")
$action      = $action_in.ToLower()

$result = @{failed = $False; changed = $False;}

# Make sure lists are modifyable
[System.Collections.ArrayList]$managers    = $managers
[System.Collections.ArrayList]$communities = $communities

# Type checking
If ($managers.Count -gt 0 -And $managers[0] -IsNot [String]) {
  Fail-Json $result "Permitted managers must be an array of strings"
}

If ($communities.Count -gt 0 -And $communities[0] -IsNot [String]) {
  Fail-Json $result "SNMP communities must be an array of strings"
}

$Managers_reg_key    = "HKLM:\System\CurrentControlSet\services\SNMP\Parameters\PermittedManagers"
$Communities_reg_key = "HKLM:\System\CurrentControlSet\services\SNMP\Parameters\ValidCommunities"

ForEach ($idx in (Get-Item $Managers_reg_key).Property) {
  $manager = (Get-ItemProperty $Managers_reg_key).$idx
  If ($idx.ToLower() -eq '(default)') {
    continue
  }

  $remove = $False
  If ($managers.Contains($manager)) {
    If ($action -eq "remove") {
      $remove = $True
    } Else {
      # Remove manager from list to add since it already exists
      $managers.Remove($manager)
    }
  } ElseIf ($action -eq "set" -And $managers.Count -gt 0) {
    # Will remove this manager since it is not in the set list
    $remove = $True
  }

  If ($remove) {
    $result.changed = $True
    Remove-ItemProperty -Path $Managers_reg_key -Name $idx -WhatIf $check_mode
  }
}

ForEach ($community in (Get-Item $Communities_reg_key).Property) {
  If ($community.ToLower() -eq '(default)') {
    continue
  }

  $remove = $False
  If ($communities.Contains($community)) {
    If ($action -eq "remove") {
      $remove = $True
    } Else {
      # Remove community from list to add since it already exists
      $communities.Remove($community)
    }
  } ElseIf ($action -eq "set" -And $communities.Count -gt 0) {
    # Will remove this community since it is not in the set list
    $remove = $True
  }

  If ($remove) {
    $result.changed = $True
    Remove-ItemProperty -Path $Communities_reg_key -Name $community -WhatIf $check_mode
  }
}

If ($action -eq "remove") {
  Exit-Json $result
}

# Get used manager indexes as integers
[System.Collections.ArrayList]$indexes=@()
ForEach ($idx in (Get-Item $Managers_reg_key).Property) {
  If ($idx.ToLower() -ne '(default)') {
    $indexes.Add([int]$idx) | Out-Null
  }
}

# Add managers that don't already exist
ForEach ($manager in $managers) {
  $result.changed = $True
  If (-Not $check_mode) {
    $next_index = 1;
    While($True) {
      If (-Not $indexes.Contains($next_index)) {
        New-ItemProperty -Path $Managers_reg_key -Name $next_index -Value "$manager"
        break
      }

      $next_index = $next_index + 1
    }
  }
}

# Add communities that don't already exist
ForEach ($community in $communities) {
  $result.changed = $True
  New-ItemProperty -Path $Communities_reg_key -Name $community -PropertyType DWord -Value 4 -WhatIf $check_mode
}

Exit-Json $result
