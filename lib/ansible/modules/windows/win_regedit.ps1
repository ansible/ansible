#!powershell
# This file is part of Ansible
#
# (c) 2015, Adam Keech <akeech@chathamfinancial.com>, Josh Ludwig <jludwig@chathamfinancial.com>
# (c) 2017, Jordan Borean <jborean93@gmail.com>
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

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true -aliases "key"
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -aliases "entry","value"
$data = Get-AnsibleParam -obj $params -name "data"
$type = Get-AnsibleParam -obj $params -name "type" -type "str" -default "string" -validateset "none","binary","dword","expandstring","multistring","string","qword" -aliases "datatype"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$delete_key = Get-AnsibleParam -obj $params -name "delete_key" -type "bool" -default $true

$result = @{
    changed = $false
    data_changed = $false
    data_type_changed = $false
}

if ($diff_mode) {
    $result.diff = @{
        prepared = ""
    }
}

# Fix HCCC:\ PSDrive for pre-2.3 compatibility
if ($path -match "^HCCC:\\") {
    Add-DeprecationWarning -obj $result -message "Please use path: HKCC:\... instead of path: $path" -version 2.6
    $path = $path -replace "HCCC:\\","HKCC:\\"
}

# fire a warning if the property name isn't specified, the (Default) key ($null) can only be a string
if ($name -eq $null -and $type -ne "string") {
    Add-Warning -obj $result -message "the data type when name is not specified can only be 'string', the type has automatically been converted"
    $type = "string"
}

# Check that the registry path is in PSDrive format: HKCC, HKCR, HKCU, HKLM, HKU
if ($path -notmatch "^HK(CC|CR|CU|LM|U):\\") {
    Fail-Json $result "path: $path is not a valid powershell path, see module documentation for examples."
}

# Create the required PSDrives if missing
$registry_hive = Split-Path -Path $path -Qualifier
if ($registry_hive -eq "HKCR:" -and (-not (Test-Path HKCR:\))) {
    New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT
}
if ($registry_hive -eq "HKU:" -and (-not (Test-Path HKU:\))) {
    New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS
}
if ($registry_hive -eq "HKCC:" -and (-not (Test-Path HKCC:\))) {
    New-PSDrive -Name HKCC -PSProvider Registry -Root HKEY_CURRENT_CONFIG
}

# Simplified version of Convert-HexStringToByteArray from
# https://cyber-defense.sans.org/blog/2010/02/11/powershell-byte-array-hex-convert
# Expects a hex in the format you get when you run reg.exe export,
# and converts to a byte array so powershell can modify binary registry entries
# import format is like 'hex:be,ef,be,ef,be,ef,be,ef,be,ef'
Function Convert-RegExportHexStringToByteArray($string) {
    # Remove 'hex:' from the front of the string if present
    $string = $string.ToLower() -replace '^hex\:',''

    # Remove whitespace and any other non-hex crud.
    $string = $string -replace '[^a-f0-9\\,x\-\:]',''

    # Turn commas into colons
    $string = $string -replace ',',':'

    # Maybe there's nothing left over to convert...
    if ($string.Length -eq 0) {
        return ,@()
    }

    # Split string with or without colon delimiters.
    if ($string.Length -eq 1) {
        return ,@([System.Convert]::ToByte($string,16))
    } elseif (($string.Length % 2 -eq 0) -and ($string.IndexOf(":") -eq -1)) {
        return ,@($string -split '([a-f0-9]{2})' | foreach-object { if ($_) {[System.Convert]::ToByte($_,16)}})
    } elseif ($string.IndexOf(":") -ne -1) {
        return ,@($string -split ':+' | foreach-object {[System.Convert]::ToByte($_,16)})
    } else {
        return ,@()
    }
}

Function Test-RegistryProperty($path, $name) {
    # will validate if the registry key contains the property, returns true
    # if the property exists and false if the property does not
    try {
        $value = (Get-Item -Path $path).GetValue($name)
        # need to do it this way return ($value -eq $null) does not work
        if ($value -eq $null) {
            return $false
        } else {
            return $true
        }
    } catch [System.Management.Automation.ItemNotFoundException] {
        # key didn't exist so the property mustn't
        return $false
    }
}

Function Compare-RegistryProperties($existing, $new) {
    $mismatch = $false
    if ($existing -is [Array]) {
        if ((Compare-Object -ReferenceObject $existing -DifferenceObject $new -SyncWindow 0).Length -ne 0) {
            $mismatch = $true
        }
    } else {
        if ($existing -cne $new) {
            $mismatch = $true
        }
    }

    return $mismatch
}

# convert property names "" to $null as "" refers to (Default)
if ($name -eq "") {
    $name = $null
}

# convert the data to the required format
if ($type -in @("binary", "none")) {
    if ($data -eq $null) {
        $data = ""
    }

    # convert the data from string to byte array if in hex: format
    if ($data -is [String]) {
        $data = [byte[]](Convert-RegExportHexStringToByteArray -string $data)
    } elseif ($data -is [Int]) {
        if ($data -gt 255) {
            Fail-Json $result "cannot convert binary data '$data' to byte array, please specify this value as a yaml byte array or a comma separated hex value string"
        }
        $data = [byte[]]@([byte]$data)
    } elseif ($data -is [Array]) {
        $data = [byte[]]$data
    }
} elseif ($type -in @("dword", "qword")) {
    # dword's and dword's don't allow null values, set to 0
    if ($data -eq $null) {
        $data = 0
    }

    if ($data -is [String]) {
        # if the data is a string we need to convert it to an unsigned int64
        # it needs to be unsigned as Ansible passes in an unsigned value while
        # powershell uses a signed data type. The value will then be converted
        # below
        $data = [UInt64]$data
    }

    if ($type -eq "dword") {
        if ($data -gt [UInt32]::MaxValue) {
            Fail-Json $result "data cannot be larger than 0xffffffff when type is dword"
        } elseif ($data -gt [Int32]::MaxValue) {
            # when dealing with larger int32 (> 2147483647 or 0x7FFFFFFF) powershell
            # automatically converts it to a signed int64. We need to convert this to
            # signed int32 by parsing the hex string value.
            $data = "0x$("{0:x}" -f $data)"
        }
        $data = [Int32]$data
    } else {
        if ($data -gt [UInt64]::MaxValue) {
            Fail-Json $result "data cannot be larger than 0xffffffffffffffff when type is qword"
        } elseif ($data -gt [Int64]::MaxValue) {
            $data = "0x$("{0:x}" -f $data)"
        }
        $data = [Int64]$data
    }
} elseif ($type -in @("string", "expandstring")) {
    # a null string or expandstring must be empty quotes
    if ($data -eq $null) {
        $data = ""
    }
} elseif ($type -eq "multistring") {
    # convert the data for a multistring to a String[] array
    if ($data -eq $null) {
        $data = [String[]]@()
    } elseif ($data -isnot [Array]) {
        $new_data = New-Object -TypeName String[] -ArgumentList 1
        $new_data[0] = $data.ToString([CultureInfo]::InvariantCulture)
        $data = $new_data
    } else {
        $new_data = New-Object -TypeName String[] -ArgumentList $data.Count
        foreach ($entry in $data) {
            $new_data[$data.IndexOf($entry)] = $entry.ToString([CultureInfo]::InvariantCulture)
        }
        $data = $new_data
    }
}


# convert the type string to the .NET class
$type = [System.Enum]::Parse([Microsoft.Win32.RegistryValueKind], $type, $true)

if ($state -eq "present") {
    if (-not (Test-Path -path $path)) {
        # the key doesn't exist, create it so the next steps work
        try {
            New-Item -Path $path -Type directory -Force -WhatIf:$check_mode
        } catch {
            Fail-Json $result "failed to create registry key at $($path): $($_.Exception.Message)"
        }
        $result.changed = $true

        if ($diff_mode) {
            $result.diff.prepared += @"
+[$path]            
"@
        }
    }

    if (Test-RegistryProperty -path $path -name $name) {
        # property exists, need to compare the values and type
        $existing_key = Get-Item -Path $path
        $existing_type = $existing_key.GetValueKind($name)
        $existing_data = $existing_key.GetValue($name, $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $change_value = $false
        
        if ($type -ne $existing_type) {
            $change_value = $true
            $result.data_type_changed = $true
            $data_mismatch = Compare-RegistryProperties -existing $existing_data -new $data
            if ($data_mismatch) {
                $result.data_changed = $true
            }
        } else {
            $data_mismatch = Compare-RegistryProperties -existing $existing_data -new $data
            if ($data_mismatch) {
                $change_value = $true
                $result.data_changed = $true
            }
        }

        if ($change_value) {
            if (-not $check_mode) {
                try {
                    (Get-Item -Path $path).OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree).SetValue($name, $data, $type)
                } catch {
                    Fail-Json $result "failed to change registry property '$name' at $($path): $($_.Exception.Message)"
                }
            }
            $result.changed = $true

            if ($diff_mode) {
                $result.diff.prepared += @"
[$path]
-"$name" = "$existing_type`:$existing_data"
+"$name" = "$type`:$data"               
"@
            }
        }
    } else {
        # property doesn't exist just create a new one
        if (-not $check_mode) {
            try {
                (Get-Item -Path $path).OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree).SetValue($name, $data, $type)
            } catch {
                Fail-Json $result "failed to change registry property '$name' at $($path): $($_.Exception.Message)"
            }
        }
        $result.changed = $true
        if ($diff_mode) {
            $result.diff.prepared += @"
[$path]
+"$name" = "$type`:$data"
"@
        }
    }
} else {
    if (Test-Path -path $path) {
        if ($delete_key -and $name -eq $null) {
            # the clear_key flag is set and name is null so delete the entire key
            try {
                Remove-Item -Path $path -Force -Recurse -WhatIf:$check_mode
            } catch {
                Fail-Json $result "failed to delete registry key at $($path): $($_.Exception.Message)"
            }
            $result.changed = $true

            if ($diff_mode) {
                $result.diff.prepared += @"
-[$path]
"@
            }
        } else {
            # the clear_key flag is set or name is not null, check whether we need to delete a property
            if (Test-RegistryProperty -path $path -name $name) {
                $existing_key = Get-Item -Path $path
                $existing_type = $existing_key.GetValueKind($name)
                $existing_data = $existing_key.GetValue($name, $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)

                # cannot use Remove-ItemProperty as it fails when deleting the (Default) key ($name = $null)
                if (-not $check_mode) {
                    try {
                        (Get-Item -Path $path).OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree).DeleteValue($name)
                    } catch {
                        Fail-Json $result "failed to delete registry property '$name' at $($path): $($_.Exception.Message)"
                    }
                }
                $result.changed = $true

                if ($diff_mode) {
                    $result.diff.prepared += @"
[$path]
-"$name" = "$existing_type`:$existing_data"
"@
                }
            }
        }
    }
}

Exit-Json $result
