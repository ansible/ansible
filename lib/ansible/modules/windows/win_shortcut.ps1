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
$result = New-Object PSObject;
Set-Attr $result "changed" $false;
$State = Get-AnsibleParam -obj $params -name "state" -default "present" -ValidateSet "present","absent" -resultobj $result -failifempty $true
$TargetFile = Get-AnsibleParam -obj $params -name "src" -failifempty $true
$ShortcutFile = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
$Arguments = Get-AnsibleParam -obj $params -name "arguments" -default $null
$Directory =  Get-AnsibleParam -obj $params -name "directory" -default $null
$hotkey = Get-AnsibleParam -obj $params -name "hotkey" -default $null
$Description = Get-AnsibleParam -obj $params -name "desc" -default $null
$IconLocation = Get-AnsibleParam -obj $params -name "icon" -default $null
$windowstyle = Get-AnsibleParam -obj $params -name "windowstyle" -default $null
#Expands variable
$src = [System.Environment]::ExpandEnvironmentVariables($TargetFile)
$dest = [System.Environment]::ExpandEnvironmentVariables($ShortcutFile)
$arguments = [System.Environment]::ExpandEnvironmentVariables($Arguments)
$directory = [System.Environment]::ExpandEnvironmentVariables($Directory)
$icon = [System.Environment]::ExpandEnvironmentVariables($IconLocation)
$description = [System.Environment]::ExpandEnvironmentVariables($Description)
try
{
 if ($State -eq "absent")
 {
   if(Test-Path $dest)
   {
     Remove-Item -Path "$dest";
     $result.changed = $TRUE
   }
   else
    {
     Fail-Json (New-Object psobject) "missing required argument: Provide valid shortcut path to remove"
    }
  }
 else
 {
 if(!(Test-Path $src))
 {
  Fail-Json (New-Object psobject) "missing required argument: Provide valid exe path to create Shortcut"
 }
 $WScriptShell = New-Object -ComObject WScript.Shell
 $targetPath = $WScriptShell.CreateShortcut($dest).TargetPath
 $ShortcutKey = $WScriptShell.CreateShortcut($dest).HotKey
 $ShortcutIconloc = $WScriptShell.CreateShortcut($dest).IconLocation
 $ShortcutDescription =  $WScriptShell.CreateShortcut($dest).Description
 $ShortcutDirectory =  $WScriptShell.CreateShortcut($dest).WorkingDirectory
 $ShortcutArguments = $WscriptShell.CreateShortcut($dest).Arguments
 $ShortcutWindowstyle = $WscriptShell.CreateShortcut($dest).WindowStyle
 if(($targetPath -eq $src) -and ($ShortcutKey -eq $hotkey) -and ($ShortcutIconloc -eq $icon) -and ($ShortcutDescription -eq $description) -and ($ShortcutDirectory -eq $directory) -and ($ShortcutArguments -eq $arguments) -and ($ShortcutWindowstyle -eq $windowstyle))
 {
  $result.changed = $FALSE
 }
 else
 {
  $Shortcut = $WScriptShell.CreateShortcut($dest)
  $Shortcut.TargetPath = $src
  $ShortCut.Arguments = $arguments
  $Shortcut.WorkingDirectory = $directory
  $Shortcut.HotKey = $hotkey
  $Shortcut.IconLocation = $icon
  $Shortcut.Description = $description
  $ShortCut.WindowStyle = $windowstyle
  $Shortcut.Save()
  $result.changed = $TRUE
 }
 }
}
catch
{
 Fail-Json $result $_.Exception.Message
}
Exit-Json $result
