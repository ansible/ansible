#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params      = Parse-Args -arguments $args -supports_check_mode $true;
$check_mode  = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$managers    = Get-AnsibleParam -obj $params -name "permitted_managers"  -type "list" -default $null
$communities = Get-AnsibleParam -obj $params -name "community_strings"   -type "list" -default $null
$action_in   = Get-AnsibleParam -obj $params -name "action"              -type "str"  -default "set" -ValidateSet @("set", "add", "remove")
$action      = $action_in.ToLower()

$result = @{
  failed = $False
  changed = $False
  community_strings = [System.Collections.ArrayList]@()
  permitted_managers = [System.Collections.ArrayList]@()
}

# Make sure lists are modifyable
[System.Collections.ArrayList]$managers    = $managers
[System.Collections.ArrayList]$communities = $communities
[System.Collections.ArrayList]$indexes     = @()

# Type checking
# You would think that "$null -ne $managers" would work, but it doesn't.
# A proper type check is required. If a user provides an empty list then $managers
# is still of the correct type. If a user provides no option then $managers is $null.
If ($managers -Is [System.Collections.ArrayList] -And $managers.Count -gt 0 -And $managers[0] -IsNot [String]) {
  Fail-Json $result "Permitted managers must be an array of strings"
}

If ($communities -Is [System.Collections.ArrayList] -And $communities.Count -gt 0 -And $communities[0] -IsNot [String]) {
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
  If ($managers -Is [System.Collections.ArrayList] -And $managers.Contains($manager)) {
    If ($action -eq "remove") {
      $remove = $True
    } Else {
      # Remove manager from list to add since it already exists
      $managers.Remove($manager)
    }
  } ElseIf ($action -eq "set" -And $managers -Is [System.Collections.ArrayList]) {
    # Will remove this manager since it is not in the set list
    $remove = $True
  }

  If ($remove) {
    $result.changed = $True
    Remove-ItemProperty -Path $Managers_reg_key -Name $idx -WhatIf:$check_mode
  } Else {
    # Remember that this index is in use
    $indexes.Add([int]$idx) | Out-Null
    $result.permitted_managers.Add($manager) | Out-Null
  }
}

ForEach ($community in (Get-Item $Communities_reg_key).Property) {
  If ($community.ToLower() -eq '(default)') {
    continue
  }

  $remove = $False
  If ($communities -Is [System.Collections.ArrayList] -And $communities.Contains($community)) {
    If ($action -eq "remove") {
      $remove = $True
    } Else {
      # Remove community from list to add since it already exists
      $communities.Remove($community)
    }
  } ElseIf ($action -eq "set" -And $communities -Is [System.Collections.ArrayList]) {
    # Will remove this community since it is not in the set list
    $remove = $True
  }

  If ($remove) {
    $result.changed = $True
    Remove-ItemProperty -Path $Communities_reg_key -Name $community -WhatIf:$check_mode
  } Else {
    $result.community_strings.Add($community) | Out-Null
  }
}

If ($action -eq "remove") {
  Exit-Json $result
}

# Add managers that don't already exist
$next_index = 0
If ($managers -Is [System.Collections.ArrayList]) {
  ForEach ($manager in $managers) {
    While ($True) {
      $next_index = $next_index + 1
      If (-Not $indexes.Contains($next_index)) {
        $result.changed = $True
        New-ItemProperty -Path $Managers_reg_key -Name $next_index -Value "$manager" -WhatIf:$check_mode | Out-Null
        $result.permitted_managers.Add($manager) | Out-Null
        break
      }
    }
  }
}

# Add communities that don't already exist
If ($communities -Is [System.Collections.ArrayList]) {
  ForEach ($community in $communities) {
    $result.changed = $True
    New-ItemProperty -Path $Communities_reg_key -Name $community -PropertyType DWord -Value 4 -WhatIf:$check_mode | Out-Null
    $result.community_strings.Add($community) | Out-Null
  }
}

Exit-Json $result
