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

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_unzip = New-Object psobject
    changed = $false
}

If ($params.src) {
    $src = $params.src.toString()

    If (-Not (Test-Path -path $src)){
        Fail-Json $result "src file: $src does not exist."
    }

    $ext = [System.IO.Path]::GetExtension($src)
}
Else {
    Fail-Json $result "missing required argument: src"
}

If (-Not($params.dest -eq $null)) {
    $dest = $params.dest.toString()

    If (-Not (Test-Path $dest -PathType Container)){
        Try{
            New-Item -itemtype directory -path $dest
        }
        Catch {
            Fail-Json $result "Error creating $dest directory"
        }
    }
}
Else {
    Fail-Json $result "missing required argument: dest"
}

If ($params.recurse -eq "true" -Or $params.recurse -eq "yes") {
    $recurse = $true
}
Else {
    $recurse = $false
}

If ($params.rm -eq "true" -Or $params.rm -eq "yes"){
    $rm = $true
    Set-Attr $result.win_unzip "rm" "true"
}
Else {
    $rm = $false
}

If ($ext -eq ".zip" -And $recurse -eq $false) {
    Try {
        $shell = New-Object -ComObject Shell.Application
        $shell.NameSpace($dest).copyhere(($shell.NameSpace($src)).items(), 20)
        $result.changed = $true
    }
    Catch {
        Fail-Json $result "Error unzipping $src to $dest"
    }
}
# Requires PSCX
Else {
    # Check if PSCX is installed
    $list = Get-Module -ListAvailable

    If (-Not ($list -match "PSCX")) {
        Fail-Json "PowerShellCommunityExtensions PowerShell Module (PSCX) is required for non-'.zip' compressed archive types."
    }
    Else {
        Set-Attr $result.win_unzip "pscx_status" "present"
    }

    # Import
    Try {
        Import-Module PSCX
    }
    Catch {
        Fail-Json $result "Error importing module PSCX"
    }

    Try {
        If ($recurse) {
            Expand-Archive -Path $src -OutputPath $dest -Force

            If ($rm) {
                Get-ChildItem $dest -recurse | Where {$_.extension -eq ".gz" -Or $_.extension -eq ".zip" -Or $_.extension -eq ".bz2" -Or $_.extension -eq ".tar" -Or $_.extension -eq ".msu"} | % {
                    Expand-Archive $_.FullName -OutputPath $dest  -Force
                    Remove-Item $_.FullName -Force
                }
            }
            Else {
                Get-ChildItem $dest -recurse | Where {$_.extension -eq ".gz" -Or $_.extension -eq ".zip" -Or $_.extension -eq ".bz2" -Or $_.extension -eq ".tar" -Or $_.extension -eq ".msu"} | % {
                    Expand-Archive $_.FullName -OutputPath $dest  -Force
                }
            }
        }
        Else {
            Expand-Archive -Path $src -OutputPath $dest -Force
        }
    }
    Catch {
        If ($recurse) {
            Fail-Json "Error recursively expanding $src to $dest"
        }
        Else {
            Fail-Json "Error expanding $src to $dest"
        }
    }
}

If ($rm -eq $true){
    Remove-Item $src -Recurse -Force
    Set-Attr $result.win_unzip "rm" "true"
}

If ($params.restart -eq "true" -Or $params.restart -eq "yes") {
    Restart-Computer -Force
    Set-Attr $result.win_unzip "restart" "true"
}

# Fixes a fail error message (when the task actually succeeds) for a "Convert-ToJson: The converted JSON string is in bad format"
# This happens when JSON is parsing a string that ends with a "\", which is possible when specifying a directory to download to.
# This catches that possible error, before assigning the JSON $result
If ($src[$src.length-1] -eq "\") {
    $src = $src.Substring(0, $src.length-1)
}
If ($dest[$dest.length-1] -eq "\") {
    $dest = $dest.Substring(0, $dest.length-1)
}
Set-Attr $result.win_unzip "src" $src.toString()
Set-Attr $result.win_unzip "dest" $dest.toString()
Set-Attr $result.win_unzip "recurse" $recurse.toString()

Exit-Json $result;