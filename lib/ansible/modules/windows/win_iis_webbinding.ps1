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
$port = Get-AnsibleParam $params -name "port" -default '80'
$ip = Get-AnsibleParam $params -name "ip" -default '*'
$certificateHash = Get-AnsibleParam $params -name "certificate_hash" -type str -default ([string]::Empty)
$certificateStoreName = Get-AnsibleParam $params -name "certificate_store_name" -type str -default ([string]::Empty)
$sslFlags = Get-AnsibleParam $params -name "ssl_flags" -default '0' -ValidateSet '0','1','2','3'

$result = @{
  changed = $false
}

#################
### Functions ###
#################
function Create-BindingInfo {
    $ht = @{
        'bindingInformation' = $args[0].bindingInformation
        'ip' = $args[0].bindingInformation.split(':')[0]
        'port' = [int]$args[0].bindingInformation.split(':')[1]
        'hostheader' = $args[0].bindingInformation.split(':')[2]
        #'isDsMapperEnabled' = $args[0].isDsMapperEnabled
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

Function Get-CertificateSubjects {
Param (
[string]$CertPath
)
    If (-Not (Test-Path $CertPath) )
    {
        Fail-Json -obj $result -message "Unable to locate certificate at $CertPath"
    }

    $cert = get-item $CertPath

    If ([version][System.Environment]::OSVersion.Version -ge [version]6.2)
    {
        $cert.DnsNameList.unicode
    }
    Else
    {
        $san = $cert.extensions | Where-Object {$_.Oid.FriendlyName -eq 'Subject Alternative Name'}
        If ($san)
        {
            $san.Format(1) -split '\r\n' | Where-Object {$_} | ForEach-Object {
                ($_ -split '=')[-1]
            }
        }
        Else
        {
            If ($cert.subject -like "*,*")
            {
                ($cert.Subject | Select-String "CN=(.*?),?").matches.groups[-1].value
            }
            Else
            {
                $cert.subject -replace "CN=",''
            }
        }
    }
}



#############################
### Pre-Action Validation ###
#############################
$os_version = [version][System.Environment]::OSVersion.Version

# Ensure WebAdministration module is loaded
If ($os_version -lt [version]'6.1')
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

# if OS older than 2012 (6.2) and ssl flags are set, fail. Otherwise toggle sni_support
If ($os_version -lt [version]'6.2')
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

# validate certificate details if provided
# we don't do anything with cert on state: absent, so only validate present
If ($certificateHash -and $state -eq 'present')
{
    If ($protocol -ne 'https')
    {
        Fail-Json -obj $result -message "You can  only provide a certificate thumbprint when protocol is set to https"
    }

    #apply default for cert store name
    If (-Not $certificateStoreName)
    {
        $certificateStoreName = 'my'
    }

    #validate cert path
    $cert_path = "cert:\LocalMachine\$certificateStoreName\$certificateHash"
    If (-Not (Test-Path $cert_path) )
    {
        Fail-Json -obj $result -message "Unable to locate certificate at $cert_path"
    }

    #check if cert is wildcard and update results with useful info.
    $cert_subjects = Get-CertificateSubjects $cert_path
    $result.certificate_subjects = $cert_subjects
    If ($cert_subjects | Where-Object {$_ -match '^\*'})
    {
        $cert_is_wildcard = $true
        $result.cert_is_wildcard = $cert_is_wildcard
    }
    Else
    {
        $cert_is_wildcard = $false
        $result.cert_is_wildcard = $cert_is_wildcard
    }

    If ($os_version -lt [version]6.2 -and $host_header -and -not $cert_is_wildcard)
    {
        Fail-Json -obj $result -message "You cannot specify host headers with SSL unless it is a wildcard certificate."
    }
    Elseif ($os_version -ge [version]6.2 -and $host_header -and (-not $cert_is_wildcard -and $sslFlags -eq 0))
    {
        Fail-Json -obj $result -message "You cannot specify host headers with SSL unless it is a wildcard certificate or SNI is enabled."
    }
}

# make sure binding info is valid for central cert store if sslflags -gt 1
If ($sslFlags -gt 1 -and ($certificateHash -ne [string]::Empty -or $certificateStoreName -ne [string]::Empty))
{
    Fail-Json -obj $result -message "You set sslFlags to $sslFlags. This indicates you wish to use the Central Certificate Store feature.
    This cannot be used in combination with certficiate_hash and certificate_store_name. When using the Central Certificate Store feature,
    the certificate is automatically retrieved from the store rather than manually assigned to the binding."
}

# make sure host_header: '*' only present when state: absent
If ($host_header -match '^\*$' -and $state -ne 'absent')
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

################################################
### Remove binding or exit if already absent ###
################################################
If ($current_bindings -and $state -eq 'absent')
{
    Try {
        # will remove multiple objects in the case of * host header
        $current_bindings | Remove-WebBinding -WhatIf:$check_mode
        $result.changed = $true
    }
    Catch {
        Fail-Json -obj $result -message "Failed to remove the binding from IIS - $($_.Exception.Message)"
    }

    # removing bindings from iis may not also remove them from iis:\sslbindings

    $result.operation_type = 'removed'
    $result.binding_info = $current_bindings | ForEach-Object {Create-BindingInfo $_}
    Exit-Json -obj $result
}
ElseIf (-Not $current_bindings -and $state -eq 'absent')
{
    # exit changed: false since it's already gone
    Exit-Json -obj $result
}


################################
### Modify existing bindings ###
################################
<#
since we have already.binding_info the parameters available to get-webbinding,
we just need to check here for the ones that are not available which are the
ssl settings (hash, store, sslflags). If they aren't set we update here, or
exit with changed: false
#>
ElseIf ($current_bindings)
{
    #ran into a strange edge case in testing where I was able to retrieve bindings but not expand all the properties
    #when adding a self-signed wildcard cert to a binding. it seemed to permanently break the binding. only removing it
    #would cause the error to stop.
    Try {
        $null = $current_bindings |  Select-Object *
    }
    Catch {
        Fail-Json -obj $result -message "Found a matching binding, but failed to expand it's properties (get-binding | FL *). In testing, this was caused by using a self-signed wildcard certificate. $($_.Exception.Message)"
    }

    # check if there is a match on the ssl parameters
    If ( ($current_bindings.sslFlags -ne $sslFlags -and $sni_support) -or
        $current_bindings.certificateHash -ne $certificateHash -or
        $current_bindings.certificateStoreName -ne $certificateStoreName)
    {
        # match/update SNI
        If ($current_bindings.sslFlags -ne $sslFlags -and $sni_support)
        {
            Try {
                Set-WebBinding -Name $name -IPAddress $ip -Port $port -HostHeader $host_header -PropertyName sslFlags -value $sslFlags -whatif:$check_mode
                $result.changed = $true
            }
            Catch {
                Fail-Json -obj $result -message "Failed to update sslFlags on binding - $($_.Exception.Message)"
            }

            # Refresh the binding object since it has been changed
            Try {
                $current_bindings = Get-SingleWebBinding $binding_parameters
            }
            Catch {
                Fail-Json -obj $result -message "Failed to refresh bindings after setting sslFlags - $($_.Exception.Message)"
            }
        }
        # match/update certificate
        If ($current_bindings.certificateHash -ne $certificateHash -or $current_bindings.certificateStoreName -ne $certificateStoreName)
        {
            If (-Not $check_mode)
            {
                Try {
                    $current_bindings.AddSslCertificate($certificateHash,$certificateStoreName)
                }
                Catch {
                    Fail-Json -obj $result -message "Failed to set new SSL certificate - $($_.Exception.Message)"
                }
            }
        }
        $result.changed = $true
        $result.operation_type = 'updated'
        $result.website_state = (Get-Website | Where-Object {$_.Name -eq $Name}).State
        $result.binding_info = Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
        Exit-Json -obj $result #exit changed true
    }
    Else
    {
        $result.operation_type = 'matched'
        $result.website_state = (Get-Website | Where-Object {$_.Name -eq $Name}).State
        $result.binding_info = Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
        Exit-Json -obj $result #exit changed false
    }
}

########################
### Add new bindings ###
########################
ElseIf (-not $current_bindings -and $state -eq 'present')
{
    If ($certificateHash)
    {
        <#
        Make sure a valid binding is specified. It's possible for another site to have a binding on the same IP:PORT. If
        we bind to that same ip port without hostheader/sni it will cause a collision. Note, this check only matters for
        https. Http will generate an error when new-webbinding is called if there is a conflict, unlike https.

        I couldn't think of a good way to handle scenarios involving wildcards. There's just too many to think about and I
        wouldn't want to potentially hard fail valid scenarios here that I did not consider...so those can still collide. We just skip
        validation anytime an existing binding is a wildcard.

        If a collision does occur, the website will be stopped. To help with this we'll return the website state into results.
        #>

        #use this instead of get-webbinding. on 2k8r2 get-webbinding fails with an error if a site with no bindings exists
        $binding_matches = (Get-Website).bindings.collection | Where-Object {$_.BindingInformation -eq "$ip`:$port`:"}

        #get dns names for all certs in matching bindings
        $subjects = Foreach ($binding in $binding_matches)
        {
            $cert_path = "cert:\localmachine\$($binding.certificatestorename)\$($binding.certificatehash)"
            Get-CertificateSubjects $cert_path
        }

        #skip validating scenarios where existing certs are wildcard
        If (-not ($subjects | Where-Object {$_ -match "^\*"}))
        {
            If ($sslFlags -eq 0 -and $binding_matches -and $os_version -gt [version]6.2)
            {
                Fail-Json -obj $result -message "A conflicting binding has been found on the same ip $ip and port $port. To continue, you will either have to remove the offending binding or enable sni"
            }
            ElseIf ($binding_matches -and $os_version -lt [version]6.2)
            {
                Fail-Json -obj $result -message "A conflicting binding has been found on the same ip $ip and port $port. To continue you will need to remove the existing binding or assign a new IP or Port to this one"
            }
        }
    }

    # add binding. this creates the binding, but does not apply a certificate to it.
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
        $result.website_state = (Get-Website | Where-Object {$_.Name -eq $Name}).State
        Fail-Json -obj $result -message "Failed at creating new binding (note: creating binding and adding ssl are separate steps) - $($_.Exception.Message)"
    }

    # add certificate to binding
    If ($certificateHash -and -not $check_mode)
    {
        Try {
            $new_binding = get-webbinding -Name $name -IPAddress $ip -port $port -Protocol $protocol -hostheader $host_header
            $new_binding.addsslcertificate($certificateHash,$certificateStoreName)
        }
        Catch {
            $result.website_state = (Get-Website | Where-Object {$_.Name -eq $Name}).State
            Fail-Json -obj $result -message "Failed to set new SSL certificate - $($_.Exception.Message)"
        }
    }

    $result.changed = $true
    $result.operation_type = 'added'
    $result.website_state = (Get-Website | Where-Object {$_.Name -eq $Name}).State
    $result.binding_info = Create-BindingInfo (Get-SingleWebBinding $binding_parameters)
    Exit-Json $result
}
