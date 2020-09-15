#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true

$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true -aliases "key"
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -aliases "entry","value"

$result = @{
    changed = $false
}

Function Get-PropertyValue {
    param(
        [Parameter(Mandatory=$true)][Microsoft.Win32.RegistryKey]$Key,
        [String]$Name
    )

    $value = $Key.GetValue($Name, $null, [Microsoft.Win32.RegistryValueOptions]::None)
    if ($null -eq $value) {
        # Property does not exist or the key's (Default) is not set
        return $null
    }

    $raw_value = $Key.GetValue($Name, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)

    if ($Name -eq "") {
        # The key's (Default) will fail on GetValueKind
        $type = [Microsoft.Win32.RegistryValueKind]::String
    } else {
        $type = $Key.GetValueKind($Name)
    }

    if ($type -in @([Microsoft.Win32.RegistryValueKind]::Binary, [Microsoft.Win32.RegistryValueKind]::None)) {
        $formatted_raw_value = [System.Collections.Generic.List`1[String]]@()
        foreach ($byte in $value) {
            $formatted_raw_value.Add("0x{0:x2}" -f $byte)
        }
        $raw_value = $formatted_raw_value
    } elseif ($type -eq [Microsoft.Win32.RegistryValueKind]::DWord) {
        # .NET returns the value as a signed integer, we need to make it unsigned
        $value = [UInt32]("0x{0:x}" -f $value)
        $raw_value = $value
    } elseif ($type -eq [Microsoft.Win32.RegistryValueKind]::QWord) {
        $value = [UInt64]("0x{0:x}" -f $value)
        $raw_value = $value
    }

    $return_type = switch($type.ToString()) {
        "Binary" { "REG_BINARY" }
        "String" { "REG_SZ" }
        "DWord" { "REG_DWORD" }
        "QWord" { "REG_QWORD" }
        "MultiString" { "REG_MULTI_SZ" }
        "ExpandString" { "REG_EXPAND_SZ" }
        "None" { "REG_NONE" }
        default { "Unknown - $($type.ToString())" }
    }

    return @{
        type = $return_type
        value = $value
        raw_value = $raw_value
    }
}

# Will validate the key parameter to make sure it matches known format
if ($path -notmatch "^HK(CC|CR|CU|LM|U):\\") {
    Fail-Json -obj $result -message "path: $path is not a valid registry path, see module documentation for examples."
}

$registry_path = (Split-Path -Path $path -NoQualifier).Substring(1)  # removes the hive: and leading \
$registry_hive = switch(Split-Path -Path $path -Qualifier) {
    "HKCR:" { [Microsoft.Win32.Registry]::ClassesRoot }
    "HKCC:" { [Microsoft.Win32.Registry]::CurrentConfig }
    "HKCU:" { [Microsoft.Win32.Registry]::CurrentUser }
    "HKLM:" { [Microsoft.Win32.Registry]::LocalMachine }
    "HKU:" { [Microsoft.Win32.Registry]::Users }
}

$key = $null
try {
    $key = $registry_hive.OpenSubKey($registry_path, $false)

    if ($null -ne $key) {
        if ($null -eq $name) {
            $property_info = @{}
            foreach ($property in $key.GetValueNames()) {
                $property_info.$property = Get-PropertyValue -Key $key -Name $property
            }

            # Return the key's (Default) property if it has been defined
            $default_value = Get-PropertyValue -Key $key -Name ""
            if ($null -ne $default_value) {
                $property_info."" = $default_value
            }

            $result.exists = $true
            $result.properties = $property_info
            $result.sub_keys = $key.GetSubKeyNames()
        } else {
            $property_value = Get-PropertyValue -Key $key -Name $name
            if ($null -ne $property_value) {
                $result.exists = $true
                $result += $property_value
            } else {
                $result.exists = $false
            }
        }
    } else {
        $result.exists = $false
    }
} finally {
    if ($key) {
        $key.Dispose()
    }
    $registry_hive.Dispose()
}

Exit-Json -obj $result

