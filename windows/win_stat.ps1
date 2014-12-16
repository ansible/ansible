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

$path = Get-Attr $params "path" $FALSE;
If ($path -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: path";
}

$get_md5 = Get-Attr $params "get_md5" $TRUE | ConvertTo-Bool;

$result = New-Object psobject @{
    stat = New-Object psobject
    changed = $false
};

If (Test-Path $path)
{
    Set-Attr $result.stat "exists" $TRUE;
    $info = Get-Item $path;
    If ($info.Directory) # Only files have the .Directory attribute.
    {
        Set-Attr $result.stat "isdir" $FALSE;
        Set-Attr $result.stat "size" $info.Length;
    }
    Else
    {
        Set-Attr $result.stat "isdir" $TRUE;
    }
}
Else
{
    Set-Attr $result.stat "exists" $FALSE;
}

If ($get_md5 -and $result.stat.exists -and -not $result.stat.isdir)
{
    $hash = Get-FileChecksum($path);
    Set-Attr $result.stat "md5" $hash;
    Set-Attr $result.stat "checksum" $hash;
}

Exit-Json $result;
