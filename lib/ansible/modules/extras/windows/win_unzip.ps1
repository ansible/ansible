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

$creates = Get-AnsibleParam -obj $params -name "creates"
If ($creates -ne $null) {
    If (Test-Path $params.creates) {
        Exit-Json $result "The 'creates' file or directory already exists."
    }
}

$src = Get-AnsibleParam -obj $params -name "src" -failifempty $true
If (-Not (Test-Path -path $src)){
    Fail-Json $result "src file: $src does not exist."
}

$ext = [System.IO.Path]::GetExtension($src)


$dest = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
If (-Not (Test-Path $dest -PathType Container)){
    Try{
        New-Item -itemtype directory -path $dest
    }
    Catch {
        $err_msg = $_.Exception.Message
        Fail-Json $result "Error creating $dest directory! Msg: $err_msg"
    }
}

$recurse = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "recurse" -default "false")
$rm = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "rm" -default "false")

If ($ext -eq ".zip" -And $recurse -eq $false) {
    Try {
        $shell = New-Object -ComObject Shell.Application
        $zipPkg = $shell.NameSpace($src)
        $destPath = $shell.NameSpace($dest)
        $destPath.CopyHere($zipPkg.Items())
        $result.changed = $true
    }
    Catch {
        $err_msg = $_.Exception.Message
        Fail-Json $result "Error unzipping $src to $dest! Msg: $err_msg"
    }
}
# Requires PSCX
Else {
    # Check if PSCX is installed
    $list = Get-Module -ListAvailable

    If (-Not ($list -match "PSCX")) {
        Fail-Json $result "PowerShellCommunityExtensions PowerShell Module (PSCX) is required for non-'.zip' compressed archive types."
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

            If ($rm -eq $true) {
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
        $err_msg = $_.Exception.Message
        If ($recurse) {
            Fail-Json $result "Error recursively expanding $src to $dest! Msg: $err_msg"
        }
        Else {
            Fail-Json $result "Error expanding $src to $dest! Msg: $err_msg"
        }
    }
}

If ($rm -eq $true){
    Remove-Item $src -Recurse -Force
    Set-Attr $result.win_unzip "rm" "true"
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
