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
#
# Based on: http://powershellblogger.com/2016/01/create-shortcuts-lnk-or-url-files-with-powershell/

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true;

$_ansible_check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$orig_src = Get-AnsibleParam -obj $params -name "src"
$orig_dest = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -default "present"
$orig_args = Get-AnsibleParam -obj $params -name "args"
$orig_directory = Get-AnsibleParam -obj $params -name "directory"
$hotkey = Get-AnsibleParam -obj $params -name "hotkey"
$orig_icon = Get-AnsibleParam -obj $params -name "icon"
$orig_description = Get-AnsibleParam -obj $params -name "description"
$windowstyle = Get-AnsibleParam -obj $params -name "windowstyle" -validateset "default","maximized","minimized"

# Expand environment variables (Beware: turns $null into "")
$src = [System.Environment]::ExpandEnvironmentVariables($orig_src)
$dest = [System.Environment]::ExpandEnvironmentVariables($orig_dest)
$args = [System.Environment]::ExpandEnvironmentVariables($orig_args)
$directory = [System.Environment]::ExpandEnvironmentVariables($orig_directory)
$icon = [System.Environment]::ExpandEnvironmentVariables($orig_icon)
$description = [System.Environment]::ExpandEnvironmentVariables($orig_description)

$result = New-Object PSObject @{
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
        Set-Attr $result "changed" $true
    } Else {
        # Nothing to report, everything is fine already
    }
} ElseIf ($state -eq "present") {
    # Create an in-memory object based on the existing shortcut (if any)
    $Shell = New-Object -ComObject ("WScript.Shell")
    $ShortCut = $Shell.CreateShortcut($dest)

    # Compare existing values with new values, report as changed if required

    If ($orig_src -ne $null -and $ShortCut.TargetPath -ne $src) {
        Set-Attr $result "changed" $true
        $ShortCut.TargetPath = $src
    }
    Set-Attr $result "src" $ShortCut.TargetPath

    # Determine if we have a WshShortcut or WshUrlShortcut by checking the Arguments property
    # A WshUrlShortcut objects only consists of a TargetPath property

    # TODO: Find a better way to do has_attr() or isinstance() ?
    If (Get-Member -InputObject $ShortCut -Name Arguments) {

        # This is a full-featured application shortcut !
        If ($orig_args -ne $null -and $ShortCut.Arguments -ne $args) {
            Set-Attr $result "changed" $true
            $ShortCut.Arguments = $args
        }
        Set-Attr $result "args" $ShortCut.Arguments

        If ($orig_directory -ne $null -and $ShortCut.WorkingDirectory -ne $directory) {
            Set-Attr $result "changed" $true
            $ShortCut.WorkingDirectory = $directory
        }
        Set-Attr $result "directory" $ShortCut.WorkingDirectory

        If ($hotkey -ne $null -and $ShortCut.Hotkey -ne $hotkey) {
            Set-Attr $result "changed" $true
            $ShortCut.Hotkey = $hotkey
        }
        Set-Attr $result "hotkey" $ShortCut.Hotkey

        If ($orig_icon -ne $null -and $ShortCut.IconLocation -ne $icon) {
            Set-Attr $result "changed" $true
            $ShortCut.IconLocation = $icon
        }
        Set-Attr $result "icon" $ShortCut.IconLocation

        If ($orig_description -ne $null -and $ShortCut.Description -ne $description) {
            Set-Attr $result "changed" $true
            $ShortCut.Description = $description
        }
        Set-Attr $result "description" $ShortCut.Description

        If ($windowstyle -ne $null -and $ShortCut.WindowStyle -ne $windowstyle) {
            Set-Attr $result "changed" $true
            switch ($windowstyle) {
                "default" { $windowstyle_id = 1 }
                "maximized" { $windowstyle_id = 3 }
                "minimized" { $windowstyle_id = 7 }
                default { $windowstyle_id = 1 }
            }
            $ShortCut.WindowStyle = $windowstyle_id
        }
        Set-Attr $result "windowstyle" $ShortCut.WindowStyle
    }

    If ($result["changed"] -eq $true -and $_ansible_check_mode -ne $true) {
        Try {
            $ShortCut.Save()
        } Catch {
            Fail-Json $result "Failed to create shortcut $dest. ($($_.Exception.Message))"
        }
    }
}

Exit-Json $result
