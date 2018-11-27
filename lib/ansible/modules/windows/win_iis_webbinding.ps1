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
# We can't filter properly with get-webbinding...ex get-webbinding ip * returns all bindings
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
}

# make sure binding info is valid for central cert store if sslflags -gt 1
If ($sslFlags -gt 1 -and ($certificateHash -ne [string]::Empty -or $certificateStoreName -ne [string]::Empty))
{
    Fail-Json -obj $result -message "You set sslFlags to $sslFlags. This indicates you wish to use the Central Certificate Store feature.
    This cannot be used in combination with certficiate_hash and certificate_store_name. When using the Central Certificate Store feature,
    the certificate is automatically retrieved from the store rather than manually assigned to the binding."
}

# disallow host_header: '*'
If ($host_header -eq '*')
{
    Fail-Json -obj $result -message "To make or remove a catch-all binding, please omit the host_header parameter entirely rather than specify host_header *"
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

################################################
### Remove binding or exit if already absent ###
################################################
If ($current_bindings -and $state -eq 'absent')
{
    Try {
        #there is a bug in this method that will result in all bindings being removed if the IP in $current_bindings is a *
        #$current_bindings | Remove-WebBinding -verbose -WhatIf:$check_mode

        #another method that did not work. It kept failing to match on element and removed everything.
        #$element = @{protocol="$protocol";bindingInformation="$ip`:$port`:$host_header"}
        #Remove-WebconfigurationProperty -filter $current_bindings.ItemXPath -Name Bindings.collection -AtElement $element -WhatIf #:$check_mode

        #this method works
        [array]$bindings = Get-WebconfigurationProperty -filter $current_bindings.ItemXPath -Name Bindings.collection

        $index = Foreach ($item in $bindings) {
            If ( $protocol -eq $item.protocol -and $current_bindings.bindingInformation -eq $item.bindingInformation ) {
                $bindings.indexof($item)
                break
            }
        }

        Remove-WebconfigurationProperty -filter $current_bindings.ItemXPath -Name Bindings.collection -AtIndex $index -WhatIf:$check_mode
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
since we have already have the parameters available to get-webbinding,
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
            #$new_binding = get-webbinding -Name $name -IPAddress $ip -port $port -Protocol $protocol -hostheader $host_header
            $new_binding = Get-SingleWebBinding $binding_parameters
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

    # incase there are no bindings we do a check before calling Create-BindingInfo
    $web_binding = Get-SingleWebBinding $binding_parameters
    if ($web_binding) {
        $result.binding_info = Create-BindingInfo $web_binding
    } else {
        $result.binding_info = $null
    } 
    Exit-Json $result
}
