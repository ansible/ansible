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

$src = '';
If ($params.src.GetType)
{
    $src = $params.src;
}
Else
{
    If ($params.path.GetType)
    {
        $src = $params.path;
    }
}
If (-not $src)
{
    $result = New-Object psobject @{};
    Fail-Json $result "missing required argument: src";
}

If (Test-Path $src)
{
    If ((Get-Item $src).Directory) # Only files have the .Directory attribute.
    {
        $bytes = [System.IO.File]::ReadAllBytes($src);
        $content = [System.Convert]::ToBase64String($bytes);

        $result = New-Object psobject @{
            changed = $false
            encoding = "base64"
        };
        Set-Attr $result "content" $content;
        Exit-Json $result;
    }
    Else
    {
        $result = New-Object psobject @{};
        Fail-Json $result ("is a directory: " + $src);
    }
}
Else
{
    $result = New-Object psobject @{};
    Fail-Json $result ("file not found: " + $src);
}
