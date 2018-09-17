#!powershell

# POWERSHELL_COMMON

$params      = Parse-Args -arguments $args -supports_check_mode $true;
$check_mode  = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$managers    = Get-AnsibleParam -obj $params -name "permitted_managers" -failifempty $true
$communities = Get-AnsibleParam -obj $params -name "community_strings"  -failifempty $true
$replace     = Get-AnsibleParam -obj $params -name "replace" -type "bool" -default $false

$result = @{failed = $False; changed = $False;}

# Make sure lists are modifyable
[System.Collections.ArrayList]$managers    = $managers
[System.Collections.ArrayList]$communities = $communities

# Type checking
If ($managers.Count -gt 0 -And $managers[0].GetType().Name -ne 'String') {
  Fail-Json $result "Permitted managers must be an array of strings"
}

If ($communities.Count -gt 0 -And $communities[0].GetType().Name -ne 'String') {
  Fail-Json $result "SNMP communities must be an array of strings"
}

$Managers_reg_key    = "HKLM:\System\CurrentControlSet\services\SNMP\Parameters\PermittedManagers"
$Communities_reg_key = "HKLM:\System\CurrentControlSet\services\SNMP\Parameters\ValidCommunities"

ForEach ($idx in (Get-Item $Managers_reg_key).Property) {
  $manager = (Get-ItemProperty $Managers_reg_key).$idx

  If ($managers.Contains($manager)) {
    # Remove manager from list since it already exists
    $managers.Remove($manager)
  } Else {
    If ($replace -And $managers.Count -gt 0) {
      # Will remove this manager since it is not in the list
      $result.changed = $True

      If (-Not $check_mode) {
        # Remove the permitted manager
        Remove-ItemProperty -Path $Managers_reg_key -Name $idx
      }
    }
  }
}

ForEach ($community in (Get-Item $Communities_reg_key).Property) {
  If ($communities.Contains($community)) {
    # Remove community from list since it already exists
    $communities.Remove($community)
  } Else {
    If ($replace -And $communities.Count -gt 0) {
      # Will remove this community since it is not in the list
      $result.changed = $True

      If (-Not $check_mode) {
        # Remove the community
        Remove-ItemProperty -Path $Communities_reg_key -Name $community
      }
    }
  }
}

# Get used manager indexes as integers
[System.Collections.ArrayList]$indexes=@()
ForEach ($idx in (Get-Item $Managers_reg_key).Property) {
  $indexes.Add([int]$idx)
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

# Add communities that don't arleady exist
ForEach ($community in $communities) {
  $result.changed = $True
  If (-Not $check_mode) {
    New-ItemProperty -Path $Communities_reg_key -Name $community -PropertyType DWord -Value 4
  }
}

Exit-Json $result
