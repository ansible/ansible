#!powershell
# (c) 2016, Dag Wieers <dag@wieers.com>
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

# Based on: http://powershellblogger.com/2016/01/create-shortcuts-lnk-or-url-files-with-powershell/

# TODO: Add debug information with what has changed using windows functions
# TODO: Ensure that by default variables default to $null automatically (so that they can be tested)

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true;

$_ansible_check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -default $null
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "string" -default "present"
$orig_args = Get-AnsibleParam -obj $params -name "args" -type "string" -default $null
$directory = Get-AnsibleParam -obj $params -name "directory" -type "path" -default $null
$hotkey = Get-AnsibleParam -obj $params -name "hotkey" -type "string" -default $null
$icon = Get-AnsibleParam -obj $params -name "icon" -type "path" -default $null
$orig_description = Get-AnsibleParam -obj $params -name "description" -type "string" -default $null
$windowstyle = Get-AnsibleParam -obj $params -name "windowstyle" -type "string" -validateset "default","maximized","minimized" -default $null

# Expand environment variables on non-path types (Beware: turns $null into "")
#$src = [System.Environment]::ExpandEnvironmentVariables($orig_src)
#$dest = [System.Environment]::ExpandEnvironmentVariables($orig_dest)
$args = Expand-Environment($orig_args)
#$directory = [System.Environment]::ExpandEnvironmentVariables($orig_directory)
#$icon = [System.Environment]::ExpandEnvironmentVariables($orig_icon)
$description = Expand-Environment($orig_description)

$result = @{
    changed = $false
    dest = $dest
    state = $state
}

If ($state -eq "absent") {
    If (Test-Path "$dest") {
        # If the shortcut exists, try to remove it
        Try {
            Remove-Item -Path "$dest";
        } Catch {
            # Report removal failure
            Fail-Json $result "Failed to remove shortcut $dest. ($($_.Exception.Message))"
        }
        # Report removal success
        $result.changed = $true
    } Else {
        # Nothing to report, everything is fine already
    }
} ElseIf ($state -eq "present") {
    # Create an in-memory object based on the existing shortcut (if any)
    $Shell = New-Object -ComObject ("WScript.Shell")
    $ShortCut = $Shell.CreateShortcut($dest)

    # Compare existing values with new values, report as changed if required

    If ($src -ne $null -and $ShortCut.TargetPath -ne $src) {
        $result.changed = $true
        $ShortCut.TargetPath = $src
    }
    $result.src = $ShortCut.TargetPath

    # Determine if we have a WshShortcut or WshUrlShortcut by checking the Arguments property
    # A WshUrlShortcut objects only consists of a TargetPath property

    # TODO: Find a better way to do has_attr() or isinstance() ?
    If (Get-Member -InputObject $ShortCut -Name Arguments) {

        # This is a full-featured application shortcut !
        If ($orig_args -ne $null -and $ShortCut.Arguments -ne $args) {
            $result.changed = $true
            $ShortCut.Arguments = $args
        }
        $result.args = $ShortCut.Arguments

        If ($directory -ne $null -and $ShortCut.WorkingDirectory -ne $directory) {
            $result.changed = $true
            $ShortCut.WorkingDirectory = $directory
        }
        $result.directory = $ShortCut.WorkingDirectory

        # FIXME: Not all values are accepted here !
        If ($hotkey -ne $null -and $ShortCut.Hotkey -ne $hotkey) {
            $result.changed = $true
            $ShortCut.Hotkey = $hotkey
        }
        $result.hotkey = $ShortCut.Hotkey

        If ($icon -ne $null -and $ShortCut.IconLocation -ne $icon) {
            $result.changed = $true
            $ShortCut.IconLocation = $icon
        }
        $result.icon = $ShortCut.IconLocation

        If ($orig_description -ne $null -and $ShortCut.Description -ne $description) {
            $result.changed = $true
            $ShortCut.Description = $description
        }
        $result.description = $ShortCut.Description

        If ($windowstyle -ne $null -and $ShortCut.WindowStyle -ne $windowstyle) {
            $result.changed = $true
            switch ($windowstyle) {
                "default" { $windowstyle_id = 1 }
                "maximized" { $windowstyle_id = 3 }
                "minimized" { $windowstyle_id = 7 }
                default { $windowstyle_id = 1 }
            }
            $ShortCut.WindowStyle = $windowstyle_id
        }
        $result.windowstyle = $ShortCut.WindowStyle
    }

    If ($result.changed -eq $true -and $_ansible_check_mode -ne $true) {
        Try {
            $ShortCut.Save()
        } Catch {
            Fail-Json $result "Failed to create shortcut $dest. ($($_.Exception.Message))"
        }
    }
}

Exit-Json $result
