#!powershell

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# (c) 2017, Jordan Borean <jborean93@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$ErrorActionPreference = 'Stop'

# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
    Import-Module WebAdministration
    $web_admin_dll_path = Join-Path $env:SystemRoot system32\inetsrv\Microsoft.Web.Administration.dll 
    Add-Type -Path $web_admin_dll_path
}

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "started" -validateset "started","restarted","stopped","absent"
$physical_path = Get-AnsibleParam -obj $params -name "physical_path" -type "path"
$site_id = Get-AnsibleParam -obj $params -name "site_id" -type "int"
$application_pool = Get-AnsibleParam -obj $params -name "application_pool" -type "str"
$port = Get-AnsibleParam -obj $params -name "port" -type "int"
$ip = Get-AnsibleParam -obj $params -name "ip" -type "str"
$hostname = Get-AnsibleParam -obj $params -name "hostname" -type "str"
$ssl = Get-AnsibleParam -obj $params -name "ssl" -type "bool"

$result = @{
    changed = $false
    attributes = @{}
    info = @{
        attributes = @{}
        bindings = @()
        limits = @{}
        logFile = @{}
        traceFailedRequestsLogging = @{}
        applicationDefaults = @{}
        virtualDirectoryDefaults = @{}
    }
    # Deprecated use info instead
    site = @{}
}

# These variables are only used when creating a new site and cannot modify existing bindings
# use win_iis_webbinding to modify these parameter instead. Will be removed in future
# versions.
if ($port) {
    Add-DeprecationWarning -obj $result -message "port is deprecated, use win_iis_webbinding to modify a site bindings" -version 2.6
}
if ($ip) {
    Add-DeprecationWarning -obj $result -message "ip is deprecated, use win_iis_webbinding to modify a site bindings" -version 2.6
}
if ($hostname) {
    Add-DeprecationWarning -obj $result -message "hostname is deprecated, use win_iis_webbinding to modify a site bindings" -version 2.6
}
if ($ssl) {
    Add-DeprecationWarning -obj $result -message "ssl is deprecated, use win_iis_webbinding to modify a site bindings" -version 2.6
}

# Verify we can set the Site ID (it isn't already taken)
if ($site_id) {
    $existing_id = Get-ChildItem -Path IIS:\sites | Where-Object { ($_.id -eq $site_id) -and ($_.name -ne $name) }
    if ($existing_id) {
        Fail-Json $result "Cannot set ID of site $name to $site_id, this ID is already taken by $($existing_id.Name)"
    }
}

# Validate physical_path if set
if ($physical_path) {
    if (-not (Test-Path -Path $physical_path)) {
        Fail-Json $result "physical_path is not a valid path: $physical_path"
    }
}

# Get attributes (originally parameters in a string form)
$attributes = Get-AnsibleParam -obj $params -name "attributes" -default @{}
if ($attributes) {
    if (-not ($attributes -is [System.Collections.Hashtable])) {
        Fail-Json $result "Expecting a dict for 'attributes' but got $($attributes.GetType())"
    }
}

# Parse the deprecated parameters param, convert to newer style attributes if necessary
$parameters = Get-AnsibleParam -obj $params -name "parameters" -type "str"
if ($parameters) {
    if ($attributes.count -gt 0) {
        Add-Warning -obj $result -message "Both the parameters (deprecated) and attributes parameter is set, ignoring parameters"
    } else {
        Add-DeprecationWarning -obj $result -message "The parameter parameters is deprecated, use attributes with a dict value" -version 2.6
        $parameters -split '\|' | ForEach-Object {
            $key, $value = $_ -split "\:"
            $attributes.$key = $value
        }
    }
}
$result.attributes = $attributes

Function Get-DotNetClassForAttribute($attribute_parent) {
    switch ($attribute_parent) {
        "attributes" { [Microsoft.Web.Administration.Site] }
        "bindings" { [Microsoft.Web.Administration.Binding] }
        "limits" { [Microsoft.Web.Administration.SiteLimits] }
        "logFile" { [Microsoft.Web.Administration.SiteLogFile] }
        "traceFailedRequestsLogging" { [Microsoft.Web.Administration.SiteTraceFailedRequestsLogging] }
        "applicationDefaults" { [Microsoft.Web.Administration.ApplicationDefaults] }
        "virtualDirectoryDefaults" { [Microsoft.Web.Administration.VirtualDirectory] }
        default { [Microsoft.Web.Administration.Site] }
    }
}

Function Convert-ToPropertyValue($site, $attribute_key, $attribute_value) {
    # Will convert the new value to the enum value expected and cast accordingly to the type
    if ([bool]($attribute_value.PSobject.Properties -match "Value")) {
        $attribute_value = $attribute_value.Value
    }
    $attribute_key_split = $attribute_key -split "\."
    if ($attribute_key_split.Length -eq 1) {
        $attribute_parent = "attributes"
        $attribute_child = $attribute_key
        $attribute_meta = $site.Attributes | Where-Object { $_.Name -eq $attribute_child }
    } elseif ($attribute_key_split.Length -eq 2) {
        $attribute_parent = $attribute_key_split[0]
        $attribute_child = $attribute_key_split[1]
        $attribute_meta = $site.$attribute_parent.Attributes | Where-Object { $_.Name -eq $attribute_child }
    }

    if ($attribute_meta) {
        $type = $attribute_meta.Schema.Type
        $value = $attribute_value
        if ($type -eq "enum") {
            # Convert the value from human friendly to enum value
            $dot_net_class = Get-DotNetClassForAttribute -attribute_parent $attribute_parent
            $enum_attribute_name = $attribute_child.Substring(0,1).ToUpper() + $attribute_child.Substring(1)
            $enum = $dot_net_class.GetProperty($enum_attribute_name).PropertyType.FullName
            if ($enum) {
                $enum_values = [Enum]::GetValues($enum)
                foreach ($enum_value in $enum_values) {
                    if ($attribute_value.GetType() -is $enum_value.GetType()) {
                        if ($enum_value -eq $attribute_value) {
                            $value = $enum_value
                            break
                        }
                    } else {
                        if ([System.String]$enum_value -eq [System.String]$attribute_value) {
                            $value = $enum_value
                            break
                        }
                    }
                }
            }            
        }
        # Try and cast the variable using the chosen type, revert to the default if it fails
        Set-Variable -Name casted_value -Value ($value -as ([type] $attribute_meta.TypeName))
        if ($casted_value -eq $null) {
            $value
        } else {
            $casted_value
        }
    } else {
        $attribute_value
    }
}

Function Remove-IISSite($name) {
    try {
        Remove-Website -Name $name -WhatIf:$check_mode
    } catch {
        Fail-Json $result "Failed to remove web site $($name): $($_.Exception.Message)"
    }
    $result.changed = $true
}

Function New-IISSite($name, $physical_path, $application_pool, $site_id, $port, $ip, $hostname, $ssl) {
    if (-not $physical_path) {
        Fail-Json $result "physical_path is required to be set when creating a new website"
    }

    $site_attributes = @{
        Name = $name
        PhysicalPath = $physical_path
    }

    if (-not $site_id) {
        # Fix for error "New-Item : Index was outside the bounds of the array."
        # This is a bug in the New-WebSite commandlet. Apparently there must be at least one site configured in IIS otherwise New-WebSite crashes.
        # For more details, see http://stackoverflow.com/questions/3573889/ps-c-new-website-blah-throws-index-was-outside-the-bounds-of-the-array
        if ((Get-ChildItem -Path IIS:\sites) -eq $null) {
            $site_id = 1
        }
    }

    $optional_attributes = @{
        ApplicationPool = $application_pool
        ID = $site_id
        Port = $port
        IPAddress = $ip
        HostHeader = $hostname
        Ssl = $ssl
    }
    foreach ($optional_attribute in $optional_attributes.GetEnumerator()) {
        $key = $optional_attribute.Name
        $value = $optional_attribute.Value
        if ($value) {
            $site_attributes.$key = $value
        }
    }

    if (-not $check_mode) {
        try {
            $site = New-Website @site_attributes -Force
        } catch {
            Fail-Json $result "Failed to created new website $($name): $($_.Exception.Message)"
        }
    } else {
        # need to set a null value when running in check mode
        $site = $null
    }
    $result.changed = $true

    $site
}

$site = Get-Website | Where-Object { $_.Name -eq $name }
if ($state -eq "absent") {
    if ($site) {
        Remove-IISSite -name $name
    }
} else {
    # create the site if it doesn't exist
    if (-not $site) {
        $site = New-IISSite -name $name -physical_path $physical_path -application_pool $application_pool -site_id $site_id -port $port -ip $ip -hostname $hostname -ssl $ssl
    }

    # recreate the site if the ID's don't match
    if ($site_id) {
        if ($site.ID -ne $site_id) {
            Remove-IISSite -name $name
            $site = New-IISSite -name $name -physical_path $physical_path -application_pool $application_pool -site_id $site_id -port $port -ip $ip -hostname $hostname -ssl $ssl
        }
    }

    # need to put the following here for when running in check mode and
    # the site doesn't exist
    if ($site) {
        # set the physical path of site
        if ($physical_path) {
            $folder = Get-Item -Path $physical_path
            if ($folder.FullName -ne $site.PhysicalPath) {
                try {
                    Set-ItemProperty -Path IIS:\Sites\$name -Name PhysicalPath -Value $folder.FullName -WhatIf:$check_mode
                } catch {
                    Fail-Json $result "Failed to set PhysicalPath for site. Site: $name, Path: $($folder.FullName), Exception: $($_.Exception.Message)"
                }
                $result.changed = $true
            }
        }

        # set the application_pool of the site
        if ($application_pool) {
            if ($application_pool -ne $site.ApplicationPool) {
                try {
                    Set-ItemProperty -Path IIS:\Sites\$name -Name ApplicationPool -Value $application_pool -WhatIf:$check_mode
                } catch {
                    Fail-Json $result "Failed to set ApplicationPool for site. Site: $name, Pool: $($application_pool), Exception: $($_.Exception.Message)"
                }
            }
        }

        # modify site based on attributes
        foreach ($attribute in $attributes.GetEnumerator()) {
            $attribute_key = $attribute.Name
            $new_raw_value = $attribute.Value
            $new_value = Convert-ToPropertyValue -site $site -attribute_key $attribute_key -attribute_value $new_raw_value

            $current_raw_value = $site
            foreach ($split_entry in ($attribute_key -split "\.")) {
                $current_raw_value = $current_raw_value.$split_entry
            }
            $current_value = Convert-ToPropertyValue -site $site -attribute_key $attribute_key -attribute_value $current_raw_value

            if (($current_value -eq $null) -or ($current_value -ne $new_value)) {
                try {
                    Set-ItemProperty -Path IIS:\Sites\$name -Name $attribute_key -Value $new_value -WhatIf:$check_mode
                } catch {
                    Fail-Json $result "Failed to set attribute to site $name. Attribute: $attribute_key, Value: $new_value, Exception: $($_.Exception.Message)"
                }
                $result.changed = $true
            }
        }
    }

    if ($site.State -eq "Stopped") {
        if ($state -eq "started" -or $state -eq "restarted") {
            if (-not $check_mode) {
                try {
                    Start-WebSite -Name $name
                } catch {
                    Fail-Json $result "Failed to start web site $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    } else {
        if ($state -eq "stopped") {
            if (-not $check_mode) {
                try {
                    Stop-WebSite -Name $name
                } catch {
                    Fail-Json $result "Failed to stop web site $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        } elseif ($state -eq "restarted") {
            if (-not $check_mode) {
                try {
                    Stop-WebSite -Name $name
                    Start-WebSite -Name $name
                } catch {
                    Fail-Json $result "Failed to restart web site $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    }
}

# set the return values
$site = Get-Website | Where-Object { $_.Name -eq $name }

# return values under site is deprecated, still return them for backward compatibility
if ($site) {
    $result.site.Name
    $result.site.ID = $site.ID
    $result.site.State = $site.State
    $result.site.PhysicalPath = $site.PhysicalPath
    $result.site.ApplicationPool = $site.ApplicationPool
    $result.site.Bindings = $($site.Bindings.Collection | ForEach-Object { $_.BindingInformation })
}

# populate the new return values under info
$elements = @("attributes", "limits", "logFile", "traceFailedRequestsLogging", "applicationDefaults", "virtualDirectoryDefaults")
foreach ($element in $elements) {
    if ($element -eq "attributes") {
        $attribute_collection = $site.Attributes
        $attribute_parent = $site
    } else {
        $attribute_collection = $site.$element.Attributes
        $attribute_parent = $site.$element
    }
    
    foreach ($attribute in $attribute_collection) {
        $attribute_name = $attribute.Name
        $attribute_value = $attribute_parent.$attribute_name

        $result.info.$element.Add($attribute_name, $attribute_value)
    }
}
# manually get some leftover variables not set above
$site_bindings = $site.Bindings.Collection
if ($site_bindings) {
    foreach ($binding in $site_bindings) {
        $binding_info = @{}
        foreach ($binding_attribute in $binding.Attributes) {
            $binding_key = $binding_attribute.Name
            $binding_value = $binding.$binding_key
            $binding_info.Add($binding_key, $binding_value)
        }
        $result.info.bindings += $binding_info
    }
}

$result.info.attributes.physicalPath = $site.physicalPath
$result.info.attributes.applicationPool = $site.applicationPool

Exit-Json $result
