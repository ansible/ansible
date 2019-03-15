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

$params = Parse-Args $args -supports_check_mode $true;
$src = Get-AnsibleParam -obj $params -name "src" -type "path" -aliases "path" -failifempty $true;

$result = @{
    changed = $false;
}

If (Test-Path -LiteralPath $src -PathType Leaf)
{
    $bytes = [System.IO.File]::ReadAllBytes($src);
    $result.content = [System.Convert]::ToBase64String($bytes);
    $result.encoding = "base64";
    Exit-Json $result;
}
ElseIf (Test-Path -LiteralPath $src -PathType Container)
{
    Fail-Json $result "Path $src is a directory";
}
Else
{
    Fail-Json $result "Path $src is not found";
}
