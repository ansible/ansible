#!powershell
# This file is part of Ansible
#
# (c) 2017, Dag Wieers <dag@wieers.com>
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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$mac = Get-AnsibleParam -obj $params -name "mac" -type "str" -failifempty $true
$broadcast = Get-AnsibleParam -obj $params -name "broadcast" -type "str" -default "255.255.255.255"
$port = Get-AnsibleParam -obj $params -name "port" -type "int" -default 7

$result = @{
    changed = $false
}

$mac_orig = $mac
$broadcast = [Net.IPAddress]::Parse($broadcast)

# Remove possible separator from MAC address
if ($mac.Length -eq (12 + 5)) {
    $mac = $mac.Replace($mac.Substring(2, 1), "")
}

# If we don't end up with 12 hexadecimal characters, fail
if ($mac.Length -ne 12) {
    Fail-Json $result "Incorrect MAC address: $mac_orig"
}

# Create payload for magic packet
# TODO: Catch possible conversion errors
$target = 0,2,4,6,8,10 | % { [convert]::ToByte($mac.Substring($_, 2), 16) }
$data = (,[byte]255 * 6) + ($target * 20)

# Broadcast payload to network
$udpclient = new-Object System.Net.Sockets.UdpClient
if (-not $check_mode) {
    $udpclient.Connect($broadcast, $port)
    [void] $udpclient.Send($data, 102)
}

$result.changed = $true

Exit-Json $result
