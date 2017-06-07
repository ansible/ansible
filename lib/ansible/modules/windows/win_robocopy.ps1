#!powershell
# This file is part of Ansible
#
# Copyright 2015, Corwin Brown <corwin.brown@maxpoint.com>
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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$purge = Get-AnsibleParam -obj $params -name "purge" -type "bool" -default $false
$recurse = Get-AnsibleParam -obj $params -name "recurse" -type "bool" -default $false
$flags = Get-AnsibleParam -obj $params -name "flags" -type "string"

$result = @{
    changed = $false
    dest = $dest
    purge = $purge
    recurse = $recurse
    src = $src
}

# Search for an Error Message
# Robocopy seems to display an error after 3 '-----' separator lines
Function SearchForError($cmd_output, $default_msg) {
    $separator_count = 0
    $error_msg = $default_msg
    ForEach ($line in $cmd_output) {
        if (-not $line) {
            continue
        }

        if ($separator_count -ne 3) {
            if (Select-String -InputObject $line -pattern "^(\s+)?(\-+)(\s+)?$") {
                $separator_count += 1
            }
        } else {
            if (Select-String -InputObject $line -pattern "error") {
                $error_msg = $line
                break
            }
        }
    }

    return $error_msg
}

if (-not (Test-Path -Path $src)) {
    Fail-Json $result "$src does not exist!"
}

# Build Arguments
$robocopy_opts = @()

$robocopy_opts += $src
$robocopy_opts += $dest

if ($check_mode) {
    $robocopy_opts += "/L"
}

if ($flags -eq $null) {
    if ($purge) {
        $robocopy_opts += "/purge"
    }

    if ($recurse) {
        $robocopy_opts += "/e"
    }
} else {
    ForEach ($f in $flags.split(" ")) {
        $robocopy_opts += $f
    }
}

$result.flags = $flags

$robocopy_output = ""
$rc = 0
Try {

    &robocopy $robocopy_opts | Tee-Object -Variable robocopy_output | Out-Null
    $rc = $LASTEXITCODE

} Catch {

    Fail-Json $result "Error synchronizing $src to $dest! Msg: $($_.Exception.Message)"

}

$result.msg = "Success"
$result.output = $robocopy_output
$result.return_code = $rc

switch ($rc) {

    0 {
        $result.msg = "No files copied."
    }
    1 {
        $result.msg = "Files copied successfully!"
        $result.changed = $true
    }
    2 {
        $result.msg = "Some Extra files or directories were detected. No files were copied."
    }
    3 {
        $result.msg = "(2+1) Some files were copied. Additional files were present."
        $result.changed = $true
    }
    4 {
        $result.msg = "Some mismatched files or directories were detected. Housekeeping might be required!"
        $result.changed = $true
    }
    5 {
        $result.msg = "(4+1) Some files were copied. Some files were mismatched."
        $result.changed = $true
    }
    6 {
        $result.msg = "(4+2) Additional files and mismatched files exist. No files were copied."
    }
    7 {
        $result.msg = "(4+1+2) Files were copied, a file mismatch was present, and additional files were present."
        $result.changed = $true
    }
    8 {
        Fail-Json $result (SearchForError $robocopy_output "Some files or directories could not be copied!")
    }
    { @(9, 10, 11, 12, 13, 14, 15) -contains $_ } {
        Fail-Json $result (SearchForError $robocopy_output "Fatal error. Check log message!")
    }
    16 {
        Fail-Json $result (SearchForError $robocopy_output "Serious Error! No files were copied! Do you have permissions to access $src and $dest?")
    }
}

Exit-Json $result
