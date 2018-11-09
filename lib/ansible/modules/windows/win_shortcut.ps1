#!powershell

# Copyright: (c) 2016, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Based on: http://powershellblogger.com/2016/01/create-shortcuts-lnk-or-url-files-with-powershell/

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        src = @{ type='str' }
        dest = @{ type='path'; required=$true }
        state = @{ type='str'; default='present'; choices=@( 'absent', 'present' ) }
        args = @{ type='str' }
        directory = @{ type='path' }
        hotkey = @{ type='str' }
        icon = @{ type='path' }
        description = @{ type='str' }
        windowstyle = @{ type='str'; choices=@( 'maximized', 'minimized', 'normal' ) }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$src = $module.Params.src
$dest = $module.Params.dest
$state = $module.Params.state
$args = $module.Params.args
$directory = $module.Params.directory
$hotkey = $module.Params.hotkey
$icon = $module.Params.icon
$description = $module.Params.description
$windowstyle = $module.Params.windowstyle

$orig_src = $module.Params.src
$orig_args = $module.Params.args
$orig_description = $module.Params.description

# Expand environment variables on non-path types
if ($null -ne $src) {
    $src = [System.Environment]::ExpandEnvironmentVariables($src)
}
if ($null -ne $args) {
    $src = [System.Environment]::ExpandEnvironmentVariables($args)
}
if ($null -ne $description) {
    $description = [System.Environment]::ExpandEnvironmentVariables($description)
}

$module.Result.changed = $false
$module.Result.dest = $dest
$module.Result.state = $state

# Convert from window style name to window style id
$windowstyles = @{
    normal = 1
    maximized = 3
    minimized = 7
}

# Convert from window style id to window style name
$windowstyleids = @( "", "normal", "", "maximized", "", "", "", "minimized" )

If ($state -eq "absent") {
    If (Test-Path -Path $dest) {
        # If the shortcut exists, try to remove it
        Try {
            Remove-Item -Path $dest -WhatIf:$check_mode
        } Catch {
            # Report removal failure
            $module.FailJson("Failed to remove shortcut '$dest'. ($($_.Exception.Message))")
        }
        # Report removal success
        $module.Result.changed = $true
    } Else {
        # Nothing to report, everything is fine already
    }
} ElseIf ($state -eq "present") {
    # Create an in-memory object based on the existing shortcut (if any)
    $Shell = New-Object -ComObject ("WScript.Shell")
    $ShortCut = $Shell.CreateShortcut($dest)

    # Compare existing values with new values, report as changed if required

    If ($src -ne $null) {
        # Windows translates executables to absolute path, so do we
        If (Get-Command -Name $src -Type Application -ErrorAction SilentlyContinue) {
            $src = (Get-Command -Name $src -Type Application).Definition
        }
        If (-not (Test-Path -Path $src -IsValid)) {
            If (-not (Split-Path -Path $src -IsAbsolute)) {
                $module.FailJson("Source '$src' is not found in PATH and not a valid or absolute path.")
            }
        }
    }

    If ($src -ne $null -and $ShortCut.TargetPath -ne $src) {
        $module.Result.changed = $true
        $ShortCut.TargetPath = $src
    }
    $module.Result.src = $ShortCut.TargetPath

    # Determine if we have a WshShortcut or WshUrlShortcut by checking the Arguments property
    # A WshUrlShortcut objects only consists of a TargetPath property

    If (Get-Member -InputObject $ShortCut -Name Arguments) {

        # This is a full-featured application shortcut !
        If ($orig_args -ne $null -and $ShortCut.Arguments -ne $args) {
            $module.Result.changed = $true
            $ShortCut.Arguments = $args
        }
        $module.Result.args = $ShortCut.Arguments

        If ($directory -ne $null -and $ShortCut.WorkingDirectory -ne $directory) {
            $module.Result.changed = $true
            $ShortCut.WorkingDirectory = $directory
        }
        $module.Result.directory = $ShortCut.WorkingDirectory

        # FIXME: Not all values are accepted here ! Improve docs too.
        If ($hotkey -ne $null -and $ShortCut.Hotkey -ne $hotkey) {
            $module.Result.changed = $true
            $ShortCut.Hotkey = $hotkey
        }
        $module.Result.hotkey = $ShortCut.Hotkey

        If ($icon -ne $null -and $ShortCut.IconLocation -ne $icon) {
            $module.Result.changed = $true
            $ShortCut.IconLocation = $icon
        }
        $module.Result.icon = $ShortCut.IconLocation

        If ($orig_description -ne $null -and $ShortCut.Description -ne $description) {
            $module.Result.changed = $true
            $ShortCut.Description = $description
        }
        $module.Result.description = $ShortCut.Description

        If ($windowstyle -ne $null -and $ShortCut.WindowStyle -ne $windowstyles.$windowstyle) {
            $module.Result.changed = $true
            $ShortCut.WindowStyle = $windowstyles.$windowstyle
        }
        $module.Result.windowstyle = $windowstyleids[$ShortCut.WindowStyle]
    }

    If ($module.Result.changed -eq $true -and $check_mode -ne $true) {
        Try {
            $ShortCut.Save()
        } Catch {
            $module.FailJson("Failed to create shortcut '$dest'. ($($_.Exception.Message))")
        }
    }
}

$module.ExitJson()
