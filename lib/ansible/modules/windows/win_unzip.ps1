#!powershell
# This file is part of Ansible
#
# Copyright 2015, Phil Schwartz <schwartzmx@gmail.com>
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

# TODO: This module is not idempotent (it will always unzip and report change)

$ErrorActionPreference = "Stop"

$pcx_extensions = @('.bz2', '.gz', '.msu', '.tar', '.zip')

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$recurse = Get-AnsibleParam -obj $params -name "recurse" -type "bool" -default $false
$delete_archive = Get-AnsibleParam -obj $params -name "delete_archive" -type "bool" -default $false -aliases 'rm'

# Fixes a fail error message (when the task actually succeeds) for a
# "Convert-ToJson: The converted JSON string is in bad format"
# This happens when JSON is parsing a string that ends with a "\",
# which is possible when specifying a directory to download to.
# This catches that possible error, before assigning the JSON $result
$result = @{
    changed = $false
    dest = $dest -replace '\$',''
    removed = $false
    src = $src -replace '\$',''
}

If ($creates -and (Test-Path -LiteralPath $creates)) {
    $result.skipped = $true
    $result.msg = "The file or directory '$creates' already exists."
    Exit-Json -obj $result
}

If (-Not (Test-Path -LiteralPath $src)) {
    Fail-Json -obj $result -message "File '$src' does not exist."
}

$ext = [System.IO.Path]::GetExtension($src)

If (-Not (Test-Path -LiteralPath $dest -PathType Container)){
    Try{
        New-Item -ItemType "directory" -path $dest -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $result -message "Error creating '$dest' directory! Msg: $($_.Exception.Message)"
    }
}

If ($ext -eq ".zip" -And $recurse -eq $false) {
    Try {
        $shell = New-Object -ComObject Shell.Application
        $zipPkg = $shell.NameSpace([IO.Path]::GetFullPath($src))
        $destPath = $shell.NameSpace([IO.Path]::GetFullPath($dest))

        if (-not $check_mode) {
            # https://msdn.microsoft.com/en-us/library/windows/desktop/bb787866.aspx
            # From Folder.CopyHere documentation, 1044 means:
            #  - 1024: do not display a user interface if an error occurs
            #  -   16: respond with "yes to all" for any dialog box that is displayed
            #  -    4: do not display a progress dialog box
            $destPath.CopyHere($zipPkg.Items(), 1044)
        }
        $result.changed = $true
    } Catch {
        Fail-Json -obj $result -message "Error unzipping '$src' to $dest! Msg: $($_.Exception.Message)"
    }
} Else {
    # Check if PSCX is installed
    $list = Get-Module -ListAvailable

    If (-Not ($list -match "PSCX")) {
        Fail-Json -obj $result -message "PowerShellCommunityExtensions PowerShell Module (PSCX) is required for non-'.zip' compressed archive types."
    } Else {
        $result.pscx_status = "present"
    }

    Try {
        Import-Module PSCX
    }
    Catch {
        Fail-Json $result "Error importing module PSCX"
    }

    Try {
        Expand-Archive -Path $src -OutputPath $dest -Force -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $result -message "Error expanding '$src' to '$dest'! Msg: $($_.Exception.Message)"
    }

    If ($recurse) {
        Get-ChildItem $dest -recurse | Where {$pcx_extensions -contains $_.extension} | % {
            Try {
                Expand-Archive $_.FullName -OutputPath $dest -Force -WhatIf:$check_mode
            } Catch {
                Fail-Json -obj $result -message "Error recursively expanding '$src' to '$dest'! Msg: $($_.Exception.Message)"
            }
            If ($delete_archive) {
                Remove-Item $_.FullName -Force -WhatIf:$check_mode
                $result.removed = $true
            }
        }
    }

    $result.changed = $true
}

If ($delete_archive){
    Remove-Item $src -Recurse -Force -WhatIf:$check_mode
    $result.removed = $true
}

Exit-Json $result
