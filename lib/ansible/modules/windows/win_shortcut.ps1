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

$ErrorActionPreference = "Stop"
$params = Parse-Args $args
$TargetFile = Get-AnsibleParam -obj $params -name "src" -failifempty $true
$ShortcutFile = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
$result = New-Object psobject @{
    changed = $FALSE
}
try
{
 $Scriptsh = New-Object -COM WScript.Shell
 $targetPath = $Scriptsh.CreateShortcut($ShortcutFile).TargetPath
 if(!(Test-Path $TargetFile))
 {
  Fail-Json (New-Object psobject) "missing required argument: Provide valid Folder where exe present"
 }
 elseif($targetPath -eq $TargetFile)
 {
 $result.changed = $FALSE
 }
 else
 {
  $WScriptShell = New-Object -ComObject WScript.Shell
  $Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
  $Shortcut.TargetPath = $TargetFile
  $Shortcut.Save()
  $result.changed = $TRUE
 }
}
catch
{
 Fail-Json $result $_.Exception.Message
}
Exit-Json $result
