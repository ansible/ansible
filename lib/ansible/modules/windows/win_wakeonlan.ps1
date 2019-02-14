#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        mac = @{ type='str'; required=$true }
        broadcast = @{ type='str'; default='255.255.255.255' }
        port = @{ type='int'; default=7 }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$module.Result.changed = $false

$mac = $module.Params.mac
$mac_orig = $module.Params.mac
$broadcast = $module.Params.broadcast
$port = $module.Params.port

$broadcast = [Net.IPAddress]::Parse($broadcast)

# Remove possible separator from MAC address
if ($mac.Length -eq (12 + 5)) {
    $mac = $mac.Replace($mac.Substring(2, 1), "")
}

# If we don't end up with 12 hexadecimal characters, fail
if ($mac.Length -ne 12) {
    $module.FailJson("Incorrect MAC address: $mac_orig")
}

# Create payload for magic packet
# TODO: Catch possible conversion errors
$target = 0,2,4,6,8,10 | ForEach-Object { [convert]::ToByte($mac.Substring($_, 2), 16) }
$data = (,[byte]255 * 6) + ($target * 20)

# Broadcast payload to network
$udpclient = new-Object System.Net.Sockets.UdpClient
if (-not $module.CheckMode) {
    $udpclient.Connect($broadcast, $port)
    [void] $udpclient.Send($data, 102)
}

$module.Result.changed = $true

$module.ExitJson()
