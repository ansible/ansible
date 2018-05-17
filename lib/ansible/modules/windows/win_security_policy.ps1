#!powershell
# This file is part of Ansible
#
# Copyright 2017, Jordan Borean <jborean93@gmail.com>
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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $Params -name "_ansible_diff" -type "bool" -default $false

$section = Get-AnsibleParam -obj $params -name "section" -type "str" -failifempty $true
$key = Get-AnsibleParam -obj $params -name "key" -type "str" -failifempty $true
$value = Get-AnsibleParam -obj $params -name "value" -failifempty $true

$result = @{
    changed = $false
    section = $section
    key = $key
    value = $value
}

if ($diff_mode) {
    $result.diff = @{}
}

Function Run-SecEdit($arguments) {
    $rc = $null
    $stdout = $null
    $stderr = $null
    $log_path = [IO.Path]::GetTempFileName()
    $arguments = $arguments + @("/log", $log_path)

    try {
        $stdout = &SecEdit.exe $arguments | Out-String
    } catch {
        $stderr = $_.Exception.Message
    }
    $log = Get-Content -Path $log_path
    Remove-Item -Path $log_path -Force

    $return = @{
        log = ($log -join "`n").Trim()
        stdout = $stdout
        stderr = $stderr
        rc = $LASTEXITCODE
    }

    return $return
}

Function Export-SecEdit() {
    $secedit_ini_path = [IO.Path]::GetTempFileName()
    # while this will technically make a change to the system in check mode by
    # creating a new file, we need these values to be able to do anything
    # substantial in check mode
    $export_result = Run-SecEdit -arguments @("/export", "/cfg", $secedit_ini_path, "/quiet")

    # check the return code and if the file has been populated, otherwise error out
    if (($export_result.rc -ne 0) -or ((Get-Item -Path $secedit_ini_path).Length -eq 0)) {
        Remove-Item -Path $secedit_ini_path -Force
        $result.rc = $export_result.rc
        $result.stdout = $export_result.stdout
        $result.stderr = $export_result.stderr
        Fail-Json $result "Failed to export secedit.ini file to $($secedit_ini_path)"
    }
    $secedit_ini = ConvertFrom-Ini -file_path $secedit_ini_path

    return $secedit_ini
}

Function Import-SecEdit($ini) {
    $secedit_ini_path = [IO.Path]::GetTempFileName()
    $secedit_db_path = [IO.Path]::GetTempFileName()
    Remove-Item -Path $secedit_db_path -Force # needs to be deleted for SecEdit.exe /import to work

    $ini_contents = ConvertTo-Ini -ini $ini
    Set-Content -Path $secedit_ini_path -Value $ini_contents
    $result.changed = $true

    $import_result = Run-SecEdit -arguments @("/configure", "/db", $secedit_db_path, "/cfg", $secedit_ini_path, "/quiet")
    $result.import_log = $import_result.log
    Remove-Item -Path $secedit_ini_path -Force
    if ($import_result.rc -ne 0) {
        $result.rc = $import_result.rc
        $result.stdout = $import_result.stdout
        $result.stderr = $import_result.stderr
        Fail-Json $result "Failed to import secedit.ini file from $($secedit_ini_path)"
    }
}

Function ConvertTo-Ini($ini) {
    $content = @()
    foreach ($key in $ini.GetEnumerator()) {
        $section = $key.Name
        $values = $key.Value

        $content += "[$section]"
        foreach ($value in $values.GetEnumerator()) {
            $value_key = $value.Name
            $value_value = $value.Value

            if ($value_value -ne $null) {
                $content += "$value_key = $value_value"
            }
        }
    }

    return $content -join "`r`n"
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

    return $ini
}

$will_change = $false
$secedit_ini = Export-SecEdit
if (-not ($secedit_ini.ContainsKey($section))) {
    Fail-Json $result "The section '$section' does not exist in SecEdit.exe output ini"
}

if ($secedit_ini.$section.ContainsKey($key)) {
    $current_value = $secedit_ini.$section.$key

    if ($current_value -cne $value) {
        if ($diff_mode) {
            $result.diff.prepared = @"
[$section]
-$key = $current_value
+$key = $value
"@
        }

        $secedit_ini.$section.$key = $value
        $will_change = $true
    }
} else {
    if ($diff_mode) {
        $result.diff.prepared = @"
[$section]
+$key = $value        
"@
    }
    $secedit_ini.$section.$key = $value
    $will_change = $true
}

if ($will_change -eq $true) {
    $result.changed = $true
    if (-not $check_mode) {
        Import-SecEdit -ini $secedit_ini

        # secedit doesn't error out on improper entries, re-export and verify
        # the changes occurred
        $verification_ini = Export-SecEdit
        $new_section_values = $verification_ini.$section
        if ($new_section_values.ContainsKey($key)) {
            $new_value = $new_section_values.$key
            if ($new_value -cne $value) {
                Fail-Json $result "Failed to change the value for key '$key' in section '$section', the value is still $new_value"
            }
        } else {
            Fail-Json $result "The key '$key' in section '$section' is not a valid key, cannot set this value"
        }
    }
}

Exit-Json $result
