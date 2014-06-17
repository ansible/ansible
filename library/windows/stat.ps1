#!powershell
# WANT_JSON
# POWERSHELL_COMMON

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

$params = Parse-Args $args;

$path = '';
If ($params.path.GetType)
{
   $path = $params.path;
}

$get_md5 = $TRUE;
If ($params.get_md5.GetType)
{
   $get_md5 = $params.get_md5;
}

$stat = New-Object psobject;
If (Test-Path $path)
{
   Set-Attr $stat "exists" $TRUE;
   $info = Get-Item $path;
   If ($info.Directory) # Only files have the .Directory attribute.
   {
      Set-Attr $stat "isdir" $FALSE;
      Set-Attr $stat "size" $info.Length;
   }
   Else
   {
      Set-Attr $stat "isdir" $TRUE;
   }
}
Else
{
   Set-Attr $stat "exists" $FALSE;
}

If ($get_md5 -and $stat.exists -and -not $stat.isdir)
{
   $path_md5 = (Get-FileHash -Path $path -Algorithm MD5).Hash.ToLower();
   Set-Attr $stat "md5" $path_md5;
}

$result = New-Object psobject;
Set-Attr $result "stat" $stat;
Set-Attr $result "changed" $FALSE;
echo $result | ConvertTo-Json;
