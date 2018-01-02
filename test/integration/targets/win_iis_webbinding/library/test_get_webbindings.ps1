#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#
$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam $params -name "name" -type str -failifempty $true -aliases 'website'
#$state = Get-AnsibleParam $params "state" -default "present" -validateSet "present","absent"
$host_header = Get-AnsibleParam $params -name "host_header" -type str
$protocol = Get-AnsibleParam $params -name "protocol" -type str -default 'http'
$port = Get-AnsibleParam $params -name "port" -type int -default '80'
$ip = Get-AnsibleParam $params -name "ip" -default '*'
$certificateHash = Get-AnsibleParam $params -name "certificate_hash" -type str
$certificateStoreName = Get-AnsibleParam $params -name "certificate_store_name" -type str
$sslFlags = Get-AnsibleParam $params -name "ssl_flags" -type int -default '0' -ValidateSet '0','1','2','3'

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
    $bind_search_splat = @{
        'name' = $args[0].name
        'protocol' = $args[0].protocol
        'port' = $args[0].port
        'ip' = $args[0].ip
        'hostheader' = $args[0].hostheader
    }

    # if no bindings exist, get-webbinding fails with an error that can't be ignored via error actions on older systems
    # let's ignore that specific error
    If (-not $bind_search_splat['hostheader'])
    {
        Try {
            Get-WebBinding @bind_search_splat | Where-Object {$_.BindingInformation.Split(':')[-1] -eq [string]::Empty}
        }
        Catch {
            If (-not $_.Exception.Message.CompareTo('Cannot process argument because the value of argument "obj" is null. Change the value of argument "obj" to a non-null value'))
            {
                Throw $_.Exception.Message
            }
        }
    }
    Else
    {
        Try {
            Get-WebBinding @bind_search_splat
        }
        Catch {
            If (-not $_.Exception.Message.CompareTo('Cannot process argument because the value of argument "obj" is null. Change the value of argument "obj" to a non-null value'))
            {
                Throw $_.Exception.Message
            }
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
