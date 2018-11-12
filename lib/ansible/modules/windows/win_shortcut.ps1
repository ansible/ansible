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
        arguments = @{ type='str'; aliases=@( 'args' ) }
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
$arguments = $module.Params.arguments  # NOTE: Variable $args is a special variable
$directory = $module.Params.directory
$hotkey = $module.Params.hotkey
$icon = $module.Params.icon
$description = $module.Params.description
$windowstyle = $module.Params.windowstyle

# Expand environment variables on non-path types
if ($null -ne $src) {
    $src = [System.Environment]::ExpandEnvironmentVariables($src)
}
if ($null -ne $arguments) {
    $arguments = [System.Environment]::ExpandEnvironmentVariables($arguments)
}
if ($null -ne $description) {
    $description = [System.Environment]::ExpandEnvironmentVariables($description)
}

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
            Remove-Item -Path $dest -WhatIf:$module.CheckMode
        } Catch {
            # Report removal failure
            $module.FailJson("Failed to remove shortcut '$dest'. ($($_.Exception.Message))", $_)
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

    If ($null -ne $src) {
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

    If (($null -ne $src) -and ($ShortCut.TargetPath -ne $src)) {
        $module.Result.changed = $true
        $ShortCut.TargetPath = $src
    }
    $module.Result.src = $ShortCut.TargetPath

    # Determine if we have a WshShortcut or WshUrlShortcut by checking the Arguments property
    # A WshUrlShortcut objects only consists of a TargetPath property

    If (Get-Member -InputObject $ShortCut -Name Arguments) {

        # This is a full-featured application shortcut !
        If (($null -ne $arguments) -and ($ShortCut.Arguments -ne $arguments)) {
            $module.Result.changed = $true
            $ShortCut.Arguments = $arguments
        }
        $module.Result.args = $ShortCut.Arguments

        If (($null -ne $directory) -and ($ShortCut.WorkingDirectory -ne $directory)) {
            $module.Result.changed = $true
            $ShortCut.WorkingDirectory = $directory
        }
        $module.Result.directory = $ShortCut.WorkingDirectory

        # FIXME: Not all values are accepted here ! Improve docs too.
        If (($null -ne $hotkey) -and ($ShortCut.Hotkey -ne $hotkey)) {
            $module.Result.changed = $true
            $ShortCut.Hotkey = $hotkey
        }
        $module.Result.hotkey = $ShortCut.Hotkey

        If (($null -ne $icon) -and ($ShortCut.IconLocation -ne $icon)) {
            $module.Result.changed = $true
            $ShortCut.IconLocation = $icon
        }
        $module.Result.icon = $ShortCut.IconLocation

        If (($null -ne $description) -and ($ShortCut.Description -ne $description)) {
            $module.Result.changed = $true
            $ShortCut.Description = $description
        }
        $module.Result.description = $ShortCut.Description

        If (($null -ne $windowstyle) -and ($ShortCut.WindowStyle -ne $windowstyles.$windowstyle)) {
            $module.Result.changed = $true
            $ShortCut.WindowStyle = $windowstyles.$windowstyle
        }
        $module.Result.windowstyle = $windowstyleids[$ShortCut.WindowStyle]
    }

    If (($module.Result.changed -eq $true) -and ($module.CheckMode -ne $true)) {
        Try {
            $ShortCut.Save()
        } Catch {
            $module.FailJson("Failed to create shortcut '$dest'. ($($_.Exception.Message))", $_)
        }
    }
}

$module.ExitJson()
