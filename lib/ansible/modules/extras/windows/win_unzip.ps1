#!powershell
# This file is part of Ansible
#
# Copyright 2014, Phil Schwartz <schwartzmx@gmail.com>
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

If ($params.zip) {
    $zip = $params.zip.toString()

    If (-Not (Test-Path -path $zip)){
        Fail-Json $result "zip file: $zip does not exist."
    }
}
Else {
    Fail-Json $result "missing required argument: zip"
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

Try {
    $shell = New-Object -ComObject Shell.Application
    $shell.NameSpace($dest).copyhere(($shell.NameSpace($zip)).items(), 20)
    $result.changed = $true
}
Catch {
    # Used to allow reboot after exe hotfix extraction (Windows 2008 R2 SP1)
    # This will have no effect in most cases.
    If (-Not ([System.IO.Path]::GetExtension($zip) -match ".exe")){
        $result.changed = $false
        Fail-Json $result "Error unzipping $zip to $dest"
    }
}

If ($params.rm -eq "true"){
    Remove-Item $zip -Recurse -Force
    Set-Attr $result.win_unzip "rm" "true"
}

If ($params.restart -eq "true") {
    Restart-Computer -Force
    Set-Attr $result.win_unzip "restart" "true"
}


Set-Attr $result.win_unzip "zip" $zip.toString()
Set-Attr $result.win_unzip "dest" $dest.toString()

Exit-Json $result;
