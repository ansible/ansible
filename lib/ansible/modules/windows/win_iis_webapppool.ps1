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
        recycling = @{}
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

# Ensure WebAdministration module is loaded
if ((Get-Module -Name "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
    Import-Module WebAdministration
    $web_admin_dll_path = Join-Path $env:SystemRoot system32\inetsrv\Microsoft.Web.Administration.dll 
    Add-Type -Path $web_admin_dll_path
    $t = [Type]"Microsoft.Web.Administration.ApplicationPool"
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
        $pool = Get-Item -Name IIS:\AppPools\$name
    }

    # Modify pool based on parameters
    foreach ($attribute in $attributes.GetEnumerator()) {
        $attribute_key = $attribute.Name
        $new_value = $attribute.Value
        $current_value = Get-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -ErrorAction SilentlyContinue
        $current_enum_value = $current_value

        # Used to overwrite with the actual enum values if necessary
        $attribute_key_split = $attribute_key -split "\."
        if ($attribute_key_split.Length -eq 1) {
            $attribute_meta = $pool.Attributes | Where-Object { $_.Name -eq $attribute_key }
        } elseif ($attribute_key_split.Length -eq 2) {
            $attribute_meta = $pool.($attribute_key_split[0]).Attributes | Where-Object { $_.Name -eq $attribute_key_split[1] }
        }
        if ($attribute_meta) {
            if ($attribute_meta.Schema.Type -eq "enum") {
                $current_enum_value = $attribute_meta.Value
            }
        }

        if (-not $current_value -or (($current_value -ne $new_value) -and ($current_enum_value -ne $new_value))) {
            # Convert to int if it is a number
            if ($new_value -match '^\d+$') {
                $new_value = [int]$new_value
            }
            try {
                Set-ItemProperty -Path IIS:\AppPools\$name -Name $attribute_key -Value $new_value -WhatIf:$check_mode
            } catch {
                Fail-Json $result "Failed to set attribute to Web App Pool $name. Attribute: $attribute_key, Value: $new_value, Exception: $($_.Exception.Message)"
            }
            $result.changed = $true
        }
    }

    # Set the state of the pool
    if (($state -eq "stopped") -and ($pool.State -eq "Started")) {
        if (-not $check_mode) {
            try {
                Stop-WebAppPool -Name $name
            } catch {
                Fail-Json $result "Failed to stop Web App Pool $($name): $($_.Exception.Message)"
            }
        }
        $result.changed = $true
    }

    
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
$elements = @{
    attributes = [Microsoft.Web.Administration.ApplicationPool]
    cpu = [Microsoft.Web.Administration.ApplicationPoolCpu]
    failure = [Microsoft.Web.Administration.ApplicationPoolFailure]
    processModel = [Microsoft.Web.Administration.ApplicationPoolProcessModel]
    recycling = [Microsoft.Web.Administration.ApplicationPoolRecycling]
}

foreach ($element in $elements.GetEnumerator())  {
    $parent_attribute = $element.Key
    if ($parent_attribute -eq "attributes") {
        $attribute_collection = $pool.Attributes
    } else {
        $attribute_collection = $pool.$parent_attribute.Attributes
    }

    foreach ($attribute in $attribute_collection) {
        $attribute_name = $attribute.Name
        $attribute_value = $attribute.Value
        $type = $attribute.Schema.Type

        if ($type -eq "enum") {
            $enum_attribute_name = $attribute_name.Substring(0,1).ToUpper() + $attribute_name.Substring(1)
            $enum = $element.Value.GetProperty($enum_attribute_name).PropertyType.FullName
            if ($enum) {
                $enum_names = [Enum]::GetNames($enum)
                $attribute_value = $enum_names[$attribute_value]
            } else {
                $attribute_value = $pool.$parent_attribute.$attribute_name
            }
        }

        $result.info.$parent_attribute.Add($attribute_name, $attribute_value)
    }
}

Exit-Json $result
