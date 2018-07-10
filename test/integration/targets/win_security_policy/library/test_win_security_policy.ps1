#!powershell

# WANT_JSON
# POWERSHELL_COMMON

# basic script to get the lsit of users in a particular right
# this is quite complex to put as a simple script so this is
# just a simple module

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $false
$section = Get-AnsibleParam -obj $params -name "section" -type "str" -failifempty $true
$key = Get-AnsibleParam -obj $params -name "key" -type "str" -failifempty $true

$result = @{
    changed = $false
}

Function ConvertFrom-Ini($file_path) {
    $ini = @{}
    switch -Regex -File $file_path {
        "^\[(.+)\]" {
            $section = $matches[1]
            $ini.$section = @{}
        }
        "(.+?)\s*=(.*)" {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($value -match "^\d+$") {
                $value = [int]$value
            } elseif ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            }

            $ini.$section.$name = $value
        }
    }

    $ini
}

$secedit_ini_path = [IO.Path]::GetTempFileName()
&SecEdit.exe /export /cfg $secedit_ini_path /quiet
$secedit_ini = ConvertFrom-Ini -file_path $secedit_ini_path

if ($secedit_ini.ContainsKey($section)) {
    $result.value = $secedit_ini.$section.$key
} else {
    $result.value = $null
}

Exit-Json $result
