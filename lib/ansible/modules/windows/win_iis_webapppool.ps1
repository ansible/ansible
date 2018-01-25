#!powershell

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
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

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateSet "started","restarted","stopped","absent","present"
$result = @{
    changed = $false
    attributes = @{}
    info = @{
        name = $name
        state = $state
        attributes = @{}
        cpu = @{}
        failure = @{}
        processModel = @{}
        recycling = @{
            periodicRestart = @{}
        }
    }
}

# Stores the free form attributes for the module
$attributes = @{}
$input_attributes = Get-AnsibleParam -obj $params -name "attributes"
if ($input_attributes) {
    if ($input_attributes -is [System.Collections.Hashtable]) {
        # Uses dict style parameters, newer and recommended style
        $attributes = $input_attributes
    } else {
        # Uses older style of separating with | per key pair and : for key:value (paramA:valueA|paramB:valueB)
        Add-DeprecationWarning -obj $result -message "Using a string for the attributes parameter is deprecated, please use a dict instead" -version 2.6
        $input_attributes -split '\|' | ForEach-Object {
            $key, $value = $_ -split "\:"
            $attributes.$key = $value
        }
    }
}
$result.attributes = $attributes

Function Get-DotNetClassForAttribute($attribute_parent) {
    switch ($attribute_parent) {
        "attributes" { [Microsoft.Web.Administration.ApplicationPool] }
        "cpu" { [Microsoft.Web.Administration.ApplicationPoolCpu] }
        "failure" { [Microsoft.Web.Administration.ApplicationPoolFailure] }
        "processModel" { [Microsoft.Web.Administration.ApplicationPoolProcessModel] }
        "recycling" { [Microsoft.Web.Administration.ApplicationPoolRecycling] }
        default { [Microsoft.Web.Administration.ApplicationPool] }
    }
}

Function Convert-CollectionToList($collection) {
    $list = @()

    if ($collection -is [String]) {
        $raw_list = $collection -split ","
        foreach ($entry in $raw_list) {
            $list += $entry.Trim()
        }
    } elseif ($collection -is [Microsoft.IIs.PowerShell.Framework.ConfigurationElement]) {
        # the collection is the value from IIS itself, we need to conver accordingly
        foreach ($entry in $collection.Collection) {
            $list += $entry.Value.ToString()
        }
    } elseif ($collection -isnot [Array]) {
        $list += $collection
    } else {
        $list = $collection
    }

    return ,$list
}

Function Compare-Values($current, $new) {
    if ($current -eq $null) {
        return $true
    }

    if ($current -is [Array]) {
        if ($new -isnot [Array]) {
            return $true
        }

        if ($current.Count -ne $new.Count) {
            return $true
        }
        for ($i = 0; $i -lt $current.Count; $i++) {
            if ($current[$i] -ne $new[$i]) {
                return $true
            }
        }
    } else {
        if ($current -ne $new) {
            return $true
        }
    }
    return $false
}

Function Convert-ToPropertyValue($pool, $attribute_key, $attribute_value) {
    # Will convert the new value to the enum value expected and cast accordingly to the type
    if ([bool]($attribute_value.PSobject.Properties -match "Value")) {
        $attribute_value = $attribute_value.Value
    }
    $attribute_key_split = $attribute_key -split "\."
    if ($attribute_key_split.Length -eq 1) {
        $attribute_parent = "attributes"
        $attribute_child = $attribute_key
        $attribute_meta = $pool.Attributes | Where-Object { $_.Name -eq $attribute_child }
    } elseif ($attribute_key_split.Length -gt 1) {
        $attribute_parent = $attribute_key_split[0]
        $attribute_key_split = $attribute_key_split[1..$($attribute_key_split.Length - 1)]
        $parent = $pool.$attribute_parent

        foreach ($key in $attribute_key_split) {
            $attribute_meta = $parent.Attributes | Where-Object { $_.Name -eq $key }
            $parent = $parent.$key
            if ($attribute_meta -eq $null) {
                $attribute_meta = $parent
            }
        }
        $attribute_child = $attribute_key_split[-1]
    }

    if ($attribute_meta) {
        if (($attribute_meta.PSObject.Properties.Name -eq "Collection").Count -gt 0) {
            return ,(Convert-CollectionToList -collection $attribute_value)
        }
        $type = $attribute_meta.Schema.Type
        $value = $attribute_value
        if ($type -eq "enum") {
            # Attempt to convert the value from human friendly to enum value - use existing value if we fail
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

# Ensure WebAdministration module is loaded
if ((Get-Module -Name "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
    Import-Module WebAdministration
    $web_admin_dll_path = Join-Path $env:SystemRoot system32\inetsrv\Microsoft.Web.Administration.dll 
    Add-Type -Path $web_admin_dll_path
}

$pool = Get-Item -Path IIS:\AppPools\$name -ErrorAction SilentlyContinue
if ($state -eq "absent") {
    # Remove pool if present
    if ($pool) {
        try {
            Remove-WebAppPool -Name $name -WhatIf:$check_mode
        } catch {
            Fail-Json $result "Failed to remove Web App pool $($name): $($_.Exception.Message)"
        }
        $result.changed = $true
    }
} else {
    # Add pool if absent
    if (-not $pool) {
        if (-not $check_mode) {
            try {
                New-WebAppPool -Name $name
            } catch {
                Fail-Json $result "Failed to create new Web App Pool $($name): $($_.Exception.Message)"
            }
        }
        $result.changed = $true
        # If in check mode this pool won't actually exists so skip it
        if (-not $check_mode) {
            $pool = Get-Item -Path IIS:\AppPools\$name
        }
    }

    # Modify pool based on parameters
    foreach ($attribute in $attributes.GetEnumerator()) {
        $attribute_key = $attribute.Name
        $new_raw_value = $attribute.Value
        $new_value = Convert-ToPropertyValue -pool $pool -attribute_key $attribute_key -attribute_value $new_raw_value

        $current_raw_value = Get-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -ErrorAction SilentlyContinue
        $current_value = Convert-ToPropertyValue -pool $pool -attribute_key $attribute_key -attribute_value $current_raw_value

        $changed = Compare-Values -current $current_value -new $new_value
        if ($changed -eq $true) {
            if ($new_value -is [Array]) {
                try {
                    Clear-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -WhatIf:$check_mode
                } catch {
                    Fail-Json -obj $result -message "Failed to clear attribute to Web App Pool $name. Attribute: $attribute_key, Exception: $($_.Exception.Message)"
                }
                foreach ($value in $new_value) {
                    try {
                        New-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -Value @{value=$value} -WhatIf:$check_mode
                    } catch {
                        Fail-Json -obj $result -message "Failed to add new attribute to Web App Pool $name. Attribute: $attribute_key, Value: $value, Exception: $($_.Exception.Message)"
                    }
                }
            } else {
                try {
                    Set-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -Value $new_value -WhatIf:$check_mode
                } catch {
                    Fail-Json $result "Failed to set attribute to Web App Pool $name. Attribute: $attribute_key, Value: $new_value, Exception: $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    }

    # Set the state of the pool
    if ($pool.State -eq "Stopped") {
        if ($state -eq "started" -or $state -eq "restarted") {
            if (-not $check_mode) {
                try {
                    Start-WebAppPool -Name $name
                } catch {
                    Fail-Json $result "Failed to start Web App Pool $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    } else {
        if ($state -eq "stopped") {
            if (-not $check_mode) {
                try {
                    Stop-WebAppPool -Name $name
                } catch {
                    Fail-Json $result "Failed to stop Web App Pool $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        } elseif ($state -eq "restarted") {
            if (-not $check_mode) {
                try {
                    Restart-WebAppPool -Name $name
                } catch {
                    Fail-Json $result "Failed to restart Web App Pool $($name): $($_.Exception.Message)"
                }
            }
            $result.changed = $true
        }
    }
}

# Get all the current attributes for the pool
$pool = Get-Item -Path IIS:\AppPools\$name -ErrorAction SilentlyContinue
$elements = @("attributes", "cpu", "failure", "processModel", "recycling")

foreach ($element in $elements)  {
    if ($element -eq "attributes") {
        $attribute_collection = $pool.Attributes
        $attribute_parent = $pool
    } else {
        $attribute_collection = $pool.$element.Attributes
        $attribute_parent = $pool.$element
    }

    foreach ($attribute in $attribute_collection) {
        $attribute_name = $attribute.Name
        if ($attribute_name -notlike "*password*") {
            $attribute_value = $attribute_parent.$attribute_name

            $result.info.$element.Add($attribute_name, $attribute_value)
        }
    }
}

# Manually get the periodicRestart attributes in recycling
foreach ($attribute in $pool.recycling.periodicRestart.Attributes) {
    $attribute_name = $attribute.Name
    $attribute_value = $pool.recycling.periodicRestart.$attribute_name
    $result.info.recycling.periodicRestart.Add($attribute_name, $attribute_value)
}

Exit-Json $result
