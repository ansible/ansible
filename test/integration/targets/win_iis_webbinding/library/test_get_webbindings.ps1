#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args -arguments $args -supports_check_mode $true

$name = Get-AnsibleParam $params -name "name" -type str -failifempty $true -aliases 'website'
$host_header = Get-AnsibleParam $params -name "host_header" -type str
$protocol = Get-AnsibleParam $params -name "protocol" -type str -default 'http'
$port = Get-AnsibleParam $params -name "port" -type int -default '80'
$ip = Get-AnsibleParam $params -name "ip" -default '*'

$result = @{
  changed = $false
}
function Create-BindingInfo {
    $ht = @{
        'bindingInformation' = $args[0].bindingInformation
        'ip' = $args[0].bindingInformation.split(':')[0]
        'port' = [int]$args[0].bindingInformation.split(':')[1]
        'hostheader' = $args[0].bindingInformation.split(':')[2]
        'isDsMapperEnabled' = $args[0].isDsMapperEnabled
        'protocol' = $args[0].protocol
        'certificateStoreName' = $args[0].certificateStoreName
        'certificateHash' = $args[0].certificateHash
    }

    #handle sslflag support
    If ([version][System.Environment]::OSVersion.Version -lt [version]'6.2')
    {
        $ht.sslFlags = 'not supported'
    }
    Else
    {
        $ht.sslFlags = [int]$args[0].sslFlags
    }

    Return $ht
}

# Used instead of get-webbinding to ensure we always return a single binding
# pass it $binding_parameters hashtable
function Get-SingleWebBinding {

    Try {
        $site_bindings = get-webbinding -name $args[0].name
    }
    Catch {
        # 2k8r2 throws this error when you run get-webbinding with no bindings in iis
        If (-not $_.Exception.Message.CompareTo('Cannot process argument because the value of argument "obj" is null. Change the value of argument "obj" to a non-null value'))
        {
            Throw $_.Exception.Message
        }
        Else { return }
    }

    Foreach ($binding in $site_bindings)
    {
        $splits = $binding.bindingInformation -split ':'

        if (
            $args[0].protocol -eq $binding.protocol -and
            $args[0].ipaddress -eq $splits[0] -and
            $args[0].port -eq $splits[1] -and
            $args[0].hostheader -eq $splits[2]
        )
        {
            Return $binding
        }
    }
}

# create binding search splat
$binding_parameters = @{
    Name = $name
    Protocol = $protocol
    Port = $port
    IPAddress = $ip
}

# insert host header to search if specified, otherwise it will return * (all bindings matching protocol/ip)
If ($host_header)
{
    $binding_parameters.HostHeader = $host_header
}
Else
{
    $binding_parameters.HostHeader = [string]::Empty
}

# Get bindings matching parameters
Try {
    $current_bindings = Get-SingleWebBinding $binding_parameters
}
Catch {
    Fail-Json -obj $result -message "Failed to retrieve bindings with Get-SingleWebBinding - $($_.Exception.Message)"
}

If ($current_bindings)
{
    Try {
        $binding_info = Create-BindingInfo $current_bindings
    }
    Catch {
        Fail-Json -obj $result -message "Failed to create binding info - $($_.Exception.Message)"
    }

    $result.binding = $binding_info
}
exit-json -obj $result