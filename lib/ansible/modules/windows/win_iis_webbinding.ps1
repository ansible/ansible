#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam $params -name "name" -type str -failifempty $true -aliases 'website'
$state = Get-AnsibleParam $params "state" -default "present" -validateSet "present","absent"
$host_header = Get-AnsibleParam $params -name "host_header" -type str
$protocol = Get-AnsibleParam $params -name "protocol" -type str -default 'http'
$port = Get-AnsibleParam $params -name "port" -type int -default '80'
$ip = Get-AnsibleParam $params -name "ip" -default '*'
$certificateHash = Get-AnsibleParam $params -name "certificate_hash" -type str
$certificateStoreName = Get-AnsibleParam $params -name "certificate_store_name" -type str
$sslFlags = Get-AnsibleParam $params -name "ssl_flags" -type int -default '0' -ValidateSet '0','1','2','3'

$result = @{
  changed = $false
  #parameters = $binding_parameters
  #matched = @()
  #removed = @()
  #added = @()
  #updated = @()
}

function Create-BindingInfo {
    $ht = @{
        'bindingInformation' = $args[0].bindingInformation
        'ip' = $args[0].bindingInformation.split(':')[0]
        'port' = $args[0].bindingInformation.split(':')[1]
        'isDsMapperEnabled' = $args[0].isDsMapperEnabled
        'protocol' = $args[0].protocol
        'certificateStoreName' = $args[0].certificateStoreName
        'certificateHash' = $args[0].certificateHash
    }

    # # all the properties returned from get-webbinding are strings even if they're empty...need to change them to null
    # If ($args[0].certificateHash -eq [string]::Empty) {$ht.certificateHash = $args[0].certificateHash}
    # Else {$ht.certificateHash = $null}

    # If ($args[0].certificateStoreName -eq [string]::Empty) {$ht.certificateStoreName = $args[0].certificateStoreName}
    # Else {$ht.certificateStoreName = $null}

    # If ($args[0].bindingInformation.split(':')[2]) {$ht.hostHeader = $args[0].bindingInformation.split(':')[2]}
    # Else {$ht.hostHeader = $null}

    #handle sslflag support
    If ([version][System.Environment]::OSVersion.Version -lt [version]'6.2')
    {
        $ht.sslFlags = 'not supported'
    }
    Else
    {
        $ht.sslFlags = $args[0].sslFlags
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

    If (-not $bind_search_splat['hostheader'])
    {
        Get-WebBinding @bind_search_splat -ea stop | Where-Object {$_.BindingInformation.Split(':')[-1] -eq [string]::Empty}
    }
    Else
    {
        Get-WebBinding @bind_search_splat -ea stop
    }
}

#############################
### Pre-Action Validation ###
#############################

# Ensure WebAdministration module is loaded
If ([version][System.Environment]::OSVersion.Version -lt [version]'6.1')
{
    Try {
        Add-PSSnapin WebAdministration
    }
    Catch {
        Fail-Json -obj $result -message "The WebAdministration snap-in is not present. Please make sure it is installed."
    }
}
Else
{
    Try {
        Import-Module WebAdministration
    }
    Catch {
        Fail-Json -obj $result -message "Failed to load WebAdministration module. Is IIS installed? $($_.Exception.Message)"
    }
}

# ensure website targetted exists. -Name filter doesn't work on 2k8r2 so do where-object instead
$website_check = get-website | Where-Object {$_.name -eq $name}
If (-not $website_check)
{
    Fail-Json -obj $result -message "Unable to retrieve website with name $Name. Make sure the website name is valid and exists."
}

# validate certificate details if provided
If ($certificateHash)
{
    If ($protocol -ne 'https')
    {
        Fail-Json -obj $result -message "You can  only provide a certificate thumbprint when protocol is set to https"
    }

    If (-Not $certificateStoreName)
    {
        $certificateStoreName = 'my'
    }

    $cert_path = "cert:\LocalMachine\$certificateStoreName\$certificateHash"
    If (-Not (Test-Path $cert_path) )
    {
        Fail-Json -obj $result -message "Unable to locate certificate at $cert_path"
    }
}

# if OS older than 2012 (6.2) and ssl flags are set, fail. Otherwise toggle sni_support
If ([version][System.Environment]::OSVersion.Version -lt [version]'6.2')
{
    If ($sslFlags -ne 0)
    {
        Fail-Json -obj $result -message "SNI and Certificate Store support is not available for systems older than 2012 (6.2)"
    }
    $sni_support = $false #will cause the sslflags check later to skip
}
Else
{
    $sni_support = $true
}
# make sure ssl flags only specified with https protocol
If ($protocol -ne 'https' -and $sslFlags -gt 0)
{
    Fail-Json -obj $result -message "SSLFlags can only be set for HTTPS protocol"
}

# make sure host_header: '*' only present when state: absent
If ($host_header -eq '*' -and $state -ne 'absent')
{
    Fail-Json -obj $result -message "host_header: '*' can only be used in combinaiton with state: absent"
}

##########################
### start action items ###
##########################

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

### Remove binding or exit if already absent ###
If ($current_bindings -and $state -eq 'absent')
{
    Try {
        # will remove multiple objects in the case of * host header
        $current_bindings | Remove-WebBinding -WhatIf:$check_mode
        $result.changed = $true
    }
    Catch {
        Fail-Json -obj $result -message "Failed to remove the binding - $($_.Exception.Message)"
    }

    $result.removed += Create-BindingInfo $current_bindings
    Exit-Json -obj $result
}
ElseIf (-Not $current_bindings -and $state -eq 'absent')
{
    # exit changed: false since it's already gone
    Exit-Json -obj $result
}

<#
since we have already matched the parameters available to get-webbinding,
we just need to check here for the ones that are not available which are the
ssl settings (hash, store, sslflags). If they aren't set we update here, or
exit with changed: false
#>
ElseIf ($current_bindings)
{
    $current_binding_hash = Create-BindingInfo $current_bindings

    # check if there is a match on the ssl parameters
    If ( ($current_bindings.sslFlags -ne $sslFlags -and $sni_support) -or
        $current_binding_hash['certificateHash'] -ne $certificateHash -or
        $current_binding_hash['certificateStoreName'] -ne $certificateStoreName)
    {
        # match/update SNI
        If ($current_bindings.sslFlags -ne $sslFlags -and $sni_support)
        {
            Try {
                Set-WebBinding -Name $name -IPAddress $ip -Port $port -HostHeader $host_header -PropertyName sslFlags -value $sslFlags
                $result.changed = $true
            }
            Catch {
                Fail-Json -obj $result -message "Failed to update sslFlags on binding - $($_.Exception.Message)"
            }
        }
        # match/update certificate
        If ($current_binding_hash['certificateHash'] -ne $certificateHash -or $current_binding_hash['certificateStoreName'] -ne $certificateStoreName)
        {
            Try {
                If (-not $check_mode)
                {
                    $current_bindings.AddSslCertificate($certificateHash,$certificateStoreName)
                }
                $result.changed = $true
            }
            Catch {
                Fail-Json -obj $result -message "Failed to update certificate on binding - $($_.Exception.Message)"
            }
        }
        $result.updated = Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
        Exit-Json -obj $result #exit changed true
    }
    Else
    {
        $result.matched = Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
        Exit-Json -obj $result #exit changed false
    }
}

### add binding ###
ElseIf (-not $current_bindings -and $state -eq 'present')
{
    Try
    {
        If (-not $check_mode)
        {
            If ($sni_support)
            {
                New-WebBinding @binding_parameters -SslFlags $sslFlags -Force
            }
            Else
            {
                New-WebBinding @binding_parameters -Force
            }
        }
        $result.changed = $true
    }
    Catch
    {
        Fail-Json -obj $result -message "Failed at creating new binding (note: creating binding and adding ssl are separate steps) - $($_.Exception.Message)"
    }

    # Select certificate
    If ($certificateHash)
    {
        Try
        {
            If (-not $check_mode)
            {
                $new_binding = Get-SingleWebBinding $binding_parameters
                $new_binding.AddSSLCertificate($certificateHash,$certificateStoreName)
            }
            $result.changed = $true
        }
        Catch
        {
            Fail-Json -obj $result -message "Failed at adding SSL to the binding - $($_.exception.message)"
        }
    }

    $result.added += Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
    $result.changed = $true
    Exit-Json $result
}
