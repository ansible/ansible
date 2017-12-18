#!powershell
# This file is part of Ansible

# Copyright 2017, Jamie Thompson <jamiet@datacom.co.nz>
# Copyright 2017, Michael Eaton <meaton@iforium.com>
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

$ErrorActionPreference = "Stop"
$firewall_profiles = @('Domain', 'Private', 'Public')

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "list" -default @("Domain", "Private", "Public")
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -failifempty $true -validateset 'disabled','enabled'

$DefaultInboundAction = Get-AnsibleParam -obj $params -name "defaultinboundaction" -validateset 'block','allow','notconfigured' -failifempty $false
$DefaultOutboundAction = Get-AnsibleParam -obj $params -name "defaultoutboundaction" -validateset 'block','allow','notconfigured' -failifempty $false
$AllowInboundRules = Get-AnsibleParam -obj $params -name "allowinboundrules" -validateset 'true','false','notconfigured' -failifempty $false
$AllowLocalFirewallRules = Get-AnsibleParam -obj $params -name "allowlocalfirewallrules" -validateset 'true','false','notconfigured' -failifempty $false
$AllowLocalIPsecRules = Get-AnsibleParam -obj $params -name "allowlocalipsecrules" -validateset 'true','false','notconfigured' -failifempty $false
$AllowUserApps = Get-AnsibleParam -obj $params -name "allowuserapps" -validateset 'true','false','notconfigured' -failifempty $false
$AllowUserPorts = Get-AnsibleParam -obj $params -name "allowuserports" -validateset 'true','false','notconfigured' -failifempty $false
$AllowUnicastResponseToMulticast = Get-AnsibleParam -obj $params -name "allowunicastresponsetomulticast" -validateset 'true','false','notconfigured' -failifempty $false
$NotifyOnListen = Get-AnsibleParam -obj $params -name "notifyonlisten" -validateset 'true','false','notconfigured' -failifempty $false
$EnableStealthModeForIPsec = Get-AnsibleParam -obj $params -name "enablestealthmodeforipsec" -validateset 'true','false','notconfigured' -failifempty $false
$LogFileName = Get-AnsibleParam -obj $params -name "logfilename" -failifempty $false -type "str"
$LogMaxSizeKilobytes = Get-AnsibleParam -obj $params -name "logmaxsizekilobytes" -failifempty $false
$LogAllowed = Get-AnsibleParam -obj $params -name "logallowed" -validateset 'true','false','notconfigured' -failifempty $false
$LogBlocked = Get-AnsibleParam -obj $params -name "logblocked" -validateset 'true','false','notconfigured' -failifempty $false
$LogIgnored = Get-AnsibleParam -obj $params -name "logignored" -validateset 'true','false','notconfigured' -failifempty $false
#$DisabledInterfaceAliases = $null
#$PolicyStore = $null

# Firewall Options hashtable
$NetFirewallProfile =
@([pscustomobject]@{option="DefaultInboundAction";value=$DefaultInboundAction;DataType="GpoBoolean"},
[pscustomobject]@{option="DefaultOutboundAction";value=$DefaultOutboundAction;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowInboundRules";value=$AllowInboundRules;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowLocalFirewallRules";value=$AllowLocalFirewallRules;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowLocalIPsecRules";value=$AllowLocalIPsecRules;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowUserApps";value=$AllowUserApps;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowUserPorts";value=$AllowUserPorts;DataType="GpoBoolean"},
[pscustomobject]@{option="AllowUnicastResponseToMulticast";value=$AllowUnicastResponseToMulticast;DataType="GpoBoolean"},
[pscustomobject]@{option="NotifyOnListen";value=$NotifyOnListen;DataType="GpoBoolean"},
[pscustomobject]@{option="EnableStealthModeForIPsec";value=$EnableStealthModeForIPsec;DataType="GpoBoolean"},
[pscustomobject]@{option="LogFileName";value=$LogFileName;DataType="String"},
[pscustomobject]@{option="LogMaxSizeKilobytes";value=$LogMaxSizeKilobytes;DataType="UInt64"},
[pscustomobject]@{option="LogAllowed";value=$LogAllowed;DataType="GpoBoolean"},
[pscustomobject]@{option="LogBlocked";value=$LogBlocked;DataType="GpoBoolean"},
[pscustomobject]@{option="LogIgnored";value=$LogIgnored;DataType="String"},
[pscustomobject]@{option="DisabledInterfaceAliases";value=$DisabledInterfaceAliases;DataType="String"},
[pscustomobject]@{option="Enabled";value=$state;DataType="GpoBoolean"},
[pscustomobject]@{option="PolicyStore";value=$PolicyStore;DataType="String"}
)

# Create hash table of required settings
 $settings = $null
 $settings = @{}

 # Add String values to the settings hashtable
  foreach ($option in $NetFirewallProfile | where {$_.value -ne $null -and $_.DataType -eq "String"}) {
   $settings.Add("$($option.option)", "$($option.value)")
    }

# Add GPOBoolean values to the settings hashtable (really just strings in this case) should use [Microsoft.PowerShell.Cmdletization.GeneratedTypes.NetSecurity.GpoBoolean]
  foreach ($option in $NetFirewallProfile | where {$_.value -ne $null -and $_.DataType -eq "GpoBoolean"}) {
       if($option.value -eq 'enabled') {
             $settings.Add("$($option.option)", "true")
    } elseif($option.value -eq 'disabled') {
             $settings.Add("$($option.option)", "false")
    } else{
              $settings.Add("$($option.option)", "$($option.value)")
              }
          }
# Add uint64 values to the settings hashtable
  foreach ($option in $NetFirewallProfile | where {$_.value -ne $null -and $_.DataType -eq "UInt64"}) {
   $settings.Add("$($option.option)", ([uint64]::Parse($option.value)))
    }

$result = @{
    changed = $false
    profiles = $profiles
    state = $state
}

if ($PSVersionTable.PSVersion -lt [Version]"5.0") {
     "win_firewall requires Windows Management Framework 5 or higher."
}

Try {

    ForEach ($profile in $firewall_profiles) {
        # build hashtable to store only the settings that actually need changing based on Firewall Profile
         $splat += @{
              $profile = @{}
                 }

        # Get current firewall profile state
        $currentstate = (Get-NetFirewallProfile -Name $profile)
        $changerequired = 0

        $result.$profile = @{
            considered = ($profiles -contains $profile)
            currentstate = $currentstate.Enabled
            changerequired = $changerequired
        }

         ForEach ($name in $settings.Keys) {
                  $result.$profile.add( "$($name)",(Get-Variable -name currentstate).value.$($name))
                  if( (Get-Variable -name currentstate).value.$($name) -eq $settings.$name){
                     "Already set"}
                else{
                     # Accumulate the settings that require changing
                     $splat.$profile.add("$($name)",$settings.$name)
                     # Flag a change is required
                     $result.$profile.changerequired++ }
           }

          # only action the firewall profiles requested
          if ($profiles -notcontains $profile) {
              continue
              }

                  if ($result.$profile.changerequired -ge '1'){
                  $splat = $splat.$profile
                      Set-NetFirewallProfile -name $profile @splat -WhatIf:$check_mode
                      $result.changed = $true
                      "Changed"
                  } else {
                  "No Change"
                  }
    }

      } Catch {
                "an error occurred when attempting to change firewall status for profile $profile $($_.Exception.Message)"
}

Exit-Json $result
