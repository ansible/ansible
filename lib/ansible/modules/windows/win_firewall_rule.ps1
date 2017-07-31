#!powershell
#
# (c) 2014, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#
# WANT_JSON
# POWERSHELL_COMMON

function Parse-ProtocolType {
    param($protocol)

    $protocolNumber = $protocol -as [int]
    if ($protocolNumber -is [int]) {
        return $protocolNumber
    }

    switch -wildcard ($protocol) {
        "tcp" { return [System.Net.Sockets.ProtocolType]::Tcp -as [int] }
        "udp" { return [System.Net.Sockets.ProtocolType]::Udp -as [int] }
        "icmpv4*" { return [System.Net.Sockets.ProtocolType]::Icmp -as [int] }
        "icmpv6*" { return [System.Net.Sockets.ProtocolType]::IcmpV6 -as [int] }
        default { throw "Unknown protocol '$protocol'." }
    }
}

# See 'Direction' constants here: https://msdn.microsoft.com/ru-ru/library/windows/desktop/aa364724(v=vs.85).aspx
function Parse-Direction {
    param($directionStr)

    switch ($directionStr) {
        "in" { return 1 }
        "out" { return 2 }
        default { throw "Unknown direction '$directionStr'." }
    }
}

# See 'Action' constants here: https://msdn.microsoft.com/ru-ru/library/windows/desktop/aa364724(v=vs.85).aspx
function Parse-Action {
    param($actionStr)

    switch ($actionStr) {
        "block" { return 0 }
        "allow" { return 1 }
        default { throw "Unknown action '$actionStr'." }
    }
}

# Profile enum values: https://msdn.microsoft.com/en-us/library/windows/desktop/aa366303(v=vs.85).aspx
function Parse-Profiles
{
    param($profilesStr)

    $profiles = ($profilesStr.Split(',') | Select -uniq | ForEach {
        switch ($_) {
            "domain" { return 1 }
            "private" { return 2 }
            "public" { return 4 }
            default { throw "Unknown profile '$_'." }
        }
    } | Measure-Object -Sum).Sum

    if ($profiles -eq 7) { return 0x7fffffff }
    return $profiles
}

function Parse-InterfaceTypes
{
    param($interfaceTypesStr)

    return ($interfaceTypesStr.Split(',') | Select -uniq | ForEach {
        switch ($_) {
            "wireless" { return "Wireless" }
            "lan" { return "Lan" }
            "ras" { return "RemoteAccess" }
            default { throw "Unknown interface type '$_'." }
        }
    }) -Join ","
}


function New-FWRule
{
    param (
        [string]$name,
        [string]$description,
        [string]$applicationName,
        [string]$serviceName,
        [string]$protocol,
        [string]$localPorts,
        [string]$remotePorts,
        [string]$localAddresses,
        [string]$remoteAddresses,
        [string]$direction,
        [string]$action,
        [bool]$enabled,
        [string]$profiles,
        [string]$interfaceTypes
    )

    $rule = New-Object -ComObject HNetCfg.FWRule
    $rule.Name = $name
    $rule.Enabled = $enabled
    if ($description) { $rule.Description = $description }
    if ($applicationName) { $rule.ApplicationName = $applicationName }
    if ($serviceName) { $rule.ServiceName = $serviceName }
    if ($protocol -and $protocol -ne "any") { $rule.Protocol = Parse-ProtocolType -protocol $protocol }
    if ($localPorts -and $localPorts -ne "any") { $rule.LocalPorts = $localPorts }
    if ($remotePorts -and $remotePorts -ne "any") { $rule.RemotePorts = $remotePorts }
    if ($localAddresses -and $localAddresses -ne "any") { $rule.LocalAddresses = $localAddresses }
    if ($remoteAddresses -and $remoteAddresses -ne "any") { $rule.RemoteAddresses = $remoteAddresses }
    if ($direction) { $rule.Direction = Parse-Direction -directionStr $direction }
    if ($action) { $rule.Action = Parse-Action -actionStr $action }
    if ($profiles) { $rule.Profiles = Parse-Profiles -profilesStr $profiles }
    if ($interfaceTypes -and $interfaceTypes -ne "any") { $rule.InterfaceTypes = Parse-InterfaceTypes -interfaceTypesStr $interfaceTypes }

    return $rule
}

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$direction = Get-AnsibleParam -obj $params -name "direction" -type "str" -failifempty $true -validateset "in","out"
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -failifempty $true -validateset "allow","block","bypass"
$program = Get-AnsibleParam -obj $params -name "program" -type "str"
$service = Get-AnsibleParam -obj $params -name "service" -type "str"
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool" -default $true -aliases "enable"
$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "str" -default "domain,private,public" -aliases "profile"
$localip = Get-AnsibleParam -obj $params -name "localip" -type "str" -default "any"
$remoteip = Get-AnsibleParam -obj $params -name "remoteip" -type "str" -default "any"
$localport = Get-AnsibleParam -obj $params -name "localport" -type "str"
$remoteport = Get-AnsibleParam -obj $params -name "remoteport" -type "str"
$protocol = Get-AnsibleParam -obj $params -name "protocol" -type "str" -default "any"
$interfacetypes = Get-AnsibleParam -obj $params -name "interfacetypes" -type "str" -default "any"

# TODO: add to FWRule
$edge = Get-AnsibleParam -obj $params -name "edge" -type "str" -default "no" -validateset "no","yes","deferapp","deferuser"
$security = Get-AnsibleParam -obj $params -name "security" -type "str" -default "notrequired"

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

if ($diff_support) {
    $result.diff = @{}
    $result.diff.prepared = ""
}

try {
    $fw = New-Object -ComObject HNetCfg.FwPolicy2

    $existingRule = $fw.Rules | Where { $_.Name -eq $name }

    if ($existingRule -is [System.Array]) {
        Fail-Json $result "Multiple firewall rules with name '$name' found."
    }

    $rule = New-FWRule -name $name `
                       -description $description `
                       -direction $direction `
                       -action $action `
                       -applicationName $program `
                       -serviceName $service `
                       -enabled $enabled `
                       -profiles $profiles `
                       -localAddresses $localip `
                       -remoteAddresses $remoteip `
                       -localPorts $localport `
                       -remotePorts $remoteport `
                       -protocol $protocol `
                       -interfaceTypes $interfacetypes

    $fwPropertiesToCompare = @('Name','Description','Direction','Action','ApplicationName','ServiceName','Enabled','Profiles','LocalAddresses','RemoteAddresses','LocalPorts','RemotePorts','Protocol','InterfaceTypes')

    if ($state -eq "absent") {
        if ($existingRule -eq $null) {
            $result.msg = "Firewall rule '$name' does not exist."
        } else {
            if ($diff_support) {
                foreach ($prop in $fwPropertiesToCompare) {
                    $result.diff.prepared += "-[$($prop)='$($existingRule.$prop)']`n"
                }
            }

            if (-not $check_mode) {
                $fw.Rules.Remove($existingRule.Name)
            }
            $result.changed = $true
            $result.msg = "Firewall rule '$name' removed."
        }
    } elseif ($state -eq "present") {
        if ($existingRule -eq $null) {
            if ($diff_support) {
                foreach ($prop in $fwPropertiesToCompare) {
                    $result.diff.prepared += "+[$($prop)='$($existingRule.$prop)']`n"
                }
            }

            if (-not $check_mode) {
                $fw.Rules.Add($rule)
            }
            $result.changed = $true
            $result.msg = "Firewall rule '$name' created."
        } else {
            foreach ($prop in $fwPropertiesToCompare) {
                if ($existingRule.$prop -ne $rule.$prop) {
                    if ($diff_support) {
                        $result.diff.prepared += "-[$($prop)='$($existingRule.$prop)']`n"
                        $result.diff.prepared += "+[$($prop)='$($rule.$prop)']`n"
                    }

                    if (-not $check_mode) {
                        $existingRule.$prop = $rule.$prop
                    }
                    $result.changed = $true
                }
            }

            if ($result.changed) {
                $result.msg = "Firewall rule '$name' changed."
            } else {
                $result.msg = "Firewall rule '$name' already exists."
            }
        }
    }
} catch [Exception] {
    Fail-Json $result $_.Exception.Message
}

Exit-Json $result
