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

Function Get-NetHiveName($hive) {
    # Will also check that the hive passed in the path is a known hive
    switch ($hive.ToUpper()) {
        "HKCR" {"ClassesRoot"}
        "HKCC" {"CurrentConfig"}
        "HKCU" {"CurrentUser"}
        "HKLM" {"LocalMachine"}
        "HKU" {"Users"}
        default {"unsupported"}
    }
}

Function Get-PropertyType($hive, $path, $property) {
    $type = (Get-Item REGISTRY::$hive\$path).GetValueKind($property)
    switch ($type) {
        "Binary" {"REG_BINARY"}
        "String" {"REG_SZ"}
        "DWord" {"REG_DWORD"}
        "QWord" {"REG_QWORD"}
        "MultiString" {"REG_MULTI_SZ"}
        "ExpandString" {"REG_EXPAND_SZ"}
        "None" {"REG_NONE"}
        default {"Unknown"}
    }
}

Function Get-PropertyObject($hive, $net_hive, $path, $property) {
    $value = (Get-ItemProperty REGISTRY::$hive\$path).$property
    $type = Get-PropertyType -hive $hive -path $path -property $property
    If ($type -eq 'REG_EXPAND_SZ') {
        $raw_value = [Microsoft.Win32.Registry]::$net_hive.OpenSubKey($path).GetValue($property, $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
    } ElseIf ($type -eq 'REG_BINARY' -or $type -eq 'REG_NONE') {
        $raw_value = @()
        foreach ($byte in $value) {
            $hex_value = ('{0:x}' -f $byte).PadLeft(2, '0')
            $raw_value += "0x$hex_value"
        }
    } Else {
        $raw_value = $value
    }

    $object = @{
        raw_value = $raw_value
        value = $value
        type = $type
    }

    $object
}

Function Test-RegistryProperty($hive, $path, $property) {
    Try {
        $type = (Get-Item REGISTRY::$hive\$path).GetValueKind($property)
    } Catch {
        $type = $null
    }

    If ($type -eq $null) {
        $false
    } Else {
        $true
    }
}

# Will validate the key parameter to make sure it matches known format
if ($path -match "^([a-zA-Z_]*):\\(.*)$") {
    $hive = $matches[1]
    $reg_path = $matches[2]
} else {
    Fail-Json $result "path does not match format 'HIVE:\KEY_PATH'"
}

# Used when getting the actual REG_EXPAND_SZ value as well as checking the hive is a known value
$net_hive = Get-NetHiveName -hive $hive
if ($net_hive -eq 'unsupported') {
    Fail-Json $result "the hive in path is '$hive'; must be 'HKCR', 'HKCC', 'HKCU', 'HKLM' or 'HKU'"
}

if (Test-Path REGISTRY::$hive\$reg_path) {
    if ($name -eq $null) {
        $property_info = @{}
        $properties = Get-ItemProperty REGISTRY::$hive\$reg_path

        foreach ($property in $properties.PSObject.Properties) {
            # Powershell adds in some metadata we need to filter out
            $real_property = Test-RegistryProperty -hive $hive -path $reg_path -property $property.Name
            if ($real_property -eq $true) {
                $property_object = Get-PropertyObject -hive $hive -net_hive $net_hive -path $reg_path -property $property.Name 
                $property_info.Add($property.Name, $property_object)
            }
        }

        $sub_keys = @()
        $sub_keys_raw = Get-ChildItem REGISTRY::$hive\$reg_path -ErrorAction SilentlyContinue

        foreach ($sub_key in $sub_keys_raw) {
            $sub_keys += $sub_key.PSChildName
        }

        $result.exists = $true
        $result.sub_keys = $sub_keys
        $result.properties = $property_info
    } else {
        $exists = Test-RegistryProperty -hive $hive -path $reg_path -property $name
        if ($exists -eq $true) {
            $propertyObject = Get-PropertyObject -hive $hive -net_hive $net_hive -path $reg_path -property $name
            $result.exists = $true
            $result.raw_value = $propertyObject.raw_value
            $result.value = $propertyObject.value
            $result.type = $propertyObject.type
        } else {
            $result.exists = $false
        }
    }
} else {
    $result.exists = $false
}

Exit-Json $result
