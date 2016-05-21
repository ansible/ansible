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

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_robocopy = New-Object psobject @{
        recurse         = $false
        purge           = $false
    }
    changed = $false
}

$src = Get-AnsibleParam -obj $params -name "src" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
$purge = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "purge" -default $false)
$recurse = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "recurse" -default $false)
$flags = Get-AnsibleParam -obj $params -name "flags" -default $null
$_ansible_check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

# Search for an Error Message
# Robocopy seems to display an error after 3 '-----' separator lines
Function SearchForError($cmd_output, $default_msg) {
    $separator_count = 0
    $error_msg = $default_msg
    ForEach ($line in $cmd_output) {
        if (-Not $line) {
            continue
        }

        if ($separator_count -ne 3) {
            if (Select-String -InputObject $line -pattern "^(\s+)?(\-+)(\s+)?$") {
                $separator_count += 1
            }
        }
        Else {
            If (Select-String -InputObject $line -pattern "error") {
                $error_msg = $line
                break
            }
        }
    }

    return $error_msg
}

# Build Arguments
$robocopy_opts = @()

if (-Not (Test-Path $src)) {
    Fail-Json $result "$src does not exist!"
}

$robocopy_opts += $src
Set-Attr $result.win_robocopy "src" $src

$robocopy_opts += $dest
Set-Attr $result.win_robocopy "dest" $dest

if ($flags -eq $null) {
    if ($purge) {
        $robocopy_opts += "/purge"
    }

    if ($recurse) {
        $robocopy_opts += "/e"
    }
}
Else {
    $robocopy_opts += $flags
}

Set-Attr $result.win_robocopy "purge" $purge
Set-Attr $result.win_robocopy "recurse" $recurse
Set-Attr $result.win_robocopy "flags" $flags

$robocopy_output = ""
$rc = 0
If ($_ansible_check_mode -eq $true) {
    $robocopy_output = "Would have copied the contents of $src to $dest"
    $rc = 0
}
Else {
    Try {
        &robocopy $robocopy_opts | Tee-Object -Variable robocopy_output | Out-Null
        $rc = $LASTEXITCODE
    }
    Catch {
        $ErrorMessage = $_.Exception.Message
        Fail-Json $result "Error synchronizing $src to $dest! Msg: $ErrorMessage"
    }
}

Set-Attr $result.win_robocopy "return_code" $rc
Set-Attr $result.win_robocopy "output" $robocopy_output

$cmd_msg = "Success"
If ($rc -eq 0) {
    $cmd_msg = "No files copied."
}
ElseIf ($rc -eq 1) {
    $cmd_msg = "Files copied successfully!"
    $changed = $true
}
ElseIf ($rc -eq 2) {
    $cmd_msg = "Extra files or directories were detected!"
    $changed = $true
}
ElseIf ($rc -eq 4) {
    $cmd_msg = "Some mismatched files or directories were detected!"
    $changed = $true
}
ElseIf ($rc -eq 8) {
    $error_msg = SearchForError $robocopy_output "Some files or directories could not be copied!"
    Fail-Json $result $error_msg
}
ElseIf ($rc -eq 10) {
    $error_msg = SearchForError $robocopy_output "Serious Error! No files were copied! Do you have permissions to access $src and $dest?"
    Fail-Json $result $error_msg
}
ElseIf ($rc -eq 16) {
    $error_msg = SearchForError $robocopy_output "Fatal Error!"
    Fail-Json $result $error_msg
}

Set-Attr $result.win_robocopy "msg" $cmd_msg
Set-Attr $result.win_robocopy "changed" $changed

Exit-Json $result
