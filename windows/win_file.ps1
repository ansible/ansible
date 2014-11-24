#!powershell
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

$params = Parse-Args $args;

# path
$path = Get-Attr $params "path" $FALSE;
If ($path -eq $FALSE)
{
    $path = Get-Attr $params "dest" $FALSE;
    If ($path -eq $FALSE)
    {
        $path = Get-Attr $params "name" $FALSE;
        If ($path -eq $FALSE)
        {
            Fail-Json (New-Object psobject) "missing required argument: path";
        }
    }
}

# JH Following advice from Chris Church, only allow the following states
# in the windows version for now:
# state - file, directory, touch, absent
# (originally was: state - file, link, directory, hard, touch, absent)

$state = Get-Attr $params "state" "file";

#$recurse = Get-Attr $params "recurse" "no";

# force - yes, no
# $force = Get-Attr $params "force" "no";

# result
$result = New-Object psobject @{
    changed = $FALSE
};

If ( $state -eq "touch" )
{
    If(Test-Path $path)
    {
        (Get-ChildItem $path).LastWriteTime = Get-Date
    }
    Else
    {
        echo $null > $file
    }
    $result.changed = $TRUE;
}

If (Test-Path $path)
{
    $fileinfo = Get-Item $path;
    If ( $state -eq "absent" )
    {   
        Remove-Item -Recurse -Force $fileinfo;
        $result.changed = $TRUE;
    }
    Else
    {
        # Only files have the .Directory attribute.
        If ( $state -eq "directory" -and $fileinfo.Directory )
        {
            Fail-Json (New-Object psobject) "path is not a directory";
        }

        # Only files have the .Directory attribute.
        If ( $state -eq "file" -and -not $fileinfo.Directory )
        {
            Fail-Json (New-Object psobject) "path is not a file";
        }

    }
}
Else
{
    If ( $state -eq "directory" )
    {
        New-Item -ItemType directory -Path $path
        $result.changed = $TRUE;
    }

    If ( $state -eq "file" )
    {
        Fail-Json (New-Object psobject) "path will not be created";
    }
}

Exit-Json $result;
